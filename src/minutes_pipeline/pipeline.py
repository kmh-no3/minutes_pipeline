from __future__ import annotations

import datetime as dt
import http.client
import json
import re
import time
import urllib.error
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, TypeVar

T = TypeVar("T")


def _retry_on_network_error(
    fn: Callable[[], T],
    max_attempts: int = 3,
    delay_seconds: float = 10.0,
) -> T:
    """Retry fn on connection/download errors (e.g. RemoteDisconnected, URLError)."""
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except (http.client.RemoteDisconnected, urllib.error.URLError, OSError) as e:
            last_error = e
            if attempt < max_attempts - 1:
                print(f"Model download failed ({e}). Retrying in {delay_seconds:.0f}s... ({attempt + 1}/{max_attempts})")
                time.sleep(delay_seconds)
            else:
                raise
    if last_error is not None:
        raise last_error
    raise RuntimeError("retry exhausted")

from .config import load_config
from .io import ensure_dir, materialize_run_paths, read_json, write_json, write_text
from .summarize.llm_adapter import get_summarizer, run_llm_and_parse_json
from .summarize.prompt import load_prompt_text, load_schema, try_validate_schema, extract_json
from .summarize.render import (
    render_minutes_md,
    check_minutes_quality,
    _render_minutes_md_sections_format,
)


def run_pipeline(input_media: Path, config_path: Path) -> None:
    cfg = load_config(config_path)
    project_root: Path = cfg["__project_root__"]

    today = dt.datetime.now().date().isoformat()
    stem = input_media.stem
    run_folder = cfg["naming"]["output_folder"].format(date=today, stem=stem)

    rp = materialize_run_paths(
        project_root=project_root,
        output_dir=Path(cfg["paths"]["output_dir"]),
        run_folder_name=run_folder,
        minutes_md_name=cfg["summarize"].get("output_md", "minutes_draft.md"),
    )
    _ensure_run_dirs(rp)

    meta = {
        "run_at": dt.datetime.now().isoformat(timespec="seconds"),
        "input_media": str(input_media.resolve()),
        "config_path": str(config_path.resolve()),
        "output_dir": str(rp.run_dir),
        "steps": cfg["pipeline"]["steps"],
        "versions": {"minutes_pipeline": "0.3.0"},
    }
    write_json(rp.metadata_json, meta)

    # ASR
    if "asr" in cfg["pipeline"]["steps"]:
        transcript_raw = _step_asr(input_media, cfg)
        write_json(rp.transcript_raw, transcript_raw)
    else:
        transcript_raw = read_json(rp.transcript_raw)

    # preprocess
    if "preprocess" in cfg["pipeline"]["steps"]:
        transcript_clean = _step_preprocess(transcript_raw, cfg)
        write_json(rp.transcript_clean, transcript_clean)
    else:
        transcript_clean = transcript_raw

    # summarize
    if "summarize" in cfg["pipeline"]["steps"]:
        engine = (cfg["summarize"].get("engine") or "mock").lower()
        if engine == "manual":
            # generate request pack in the run folder and stop
            _write_request_pack(transcript_clean, cfg, out_dir=rp.run_dir)
            # also write a placeholder minutes draft
            placeholder = (
                "# 議事録（ドラフト）\n\n"
                "この実行は `summarize.engine: manual` のため、LLM UI向けのリクエストパックを出力しました。\n\n"
                f"- 次に: `mpipe request {rp.transcript_clean}`（再生成可）\n"
                f"- ChatGPT/Copilotに `llm_transcript.txt` をアップロードし、`llm_instructions.md` の指示を貼り付け\n"
                f"- 返ってきたJSONを `llm_output.json` として保存\n"
                f"- 適用: `mpipe apply {rp.run_dir/'llm_output.json'} --transcript {rp.transcript_clean}`\n"
            )
            write_text(rp.minutes_md, placeholder)
        else:
            minutes_md = _step_summarize(transcript_clean, cfg)
            write_text(rp.minutes_md, minutes_md)

    print(f"[OK] Output: {rp.run_dir}")


def summarize_only(input_transcript_clean: Path, config_path: Path) -> None:
    cfg = load_config(config_path)
    transcript_clean = read_json(input_transcript_clean)

    engine = (cfg["summarize"].get("engine") or "mock").lower()
    if engine == "manual":
        _write_request_pack(transcript_clean, cfg, out_dir=input_transcript_clean.parent)
        print(f"[OK] Request pack written to: {input_transcript_clean.parent}")
        return

    minutes_md = _step_summarize(transcript_clean, cfg)
    out_path = input_transcript_clean.parent / cfg["summarize"].get("output_md", "minutes_draft.md")
    write_text(out_path, minutes_md)
    print(f"[OK] Output: {out_path}")


def request_pack(input_transcript_clean: Path, config_path: Path, mode: str = "full") -> None:
    cfg = load_config(config_path)
    out_dir = input_transcript_clean.parent
    if (mode or "full").lower() == "chunked":
        chunks_dir = out_dir / "chunks"
        manifest_path = chunks_dir / "manifest.json"
        if not manifest_path.exists():
            print("[WARN] Chunked mode requires mpipe chunk first. Run: mpipe chunk <transcript_clean.json>")
            _write_request_pack(read_json(input_transcript_clean), cfg, out_dir=out_dir)
            print(f"[OK] Request pack (full) written to: {out_dir}")
            return
        manifest = read_json(manifest_path)
        _write_request_pack_chunked(cfg, out_dir, manifest)
        print(f"[OK] Request pack (chunked) written to: {out_dir}")
    else:
        transcript_clean = read_json(input_transcript_clean)
        _write_request_pack(transcript_clean, cfg, out_dir=out_dir)
        print(f"[OK] Request pack written to: {out_dir}")


def apply_llm_output(llm_json_path: Path, transcript_clean_path: Path, config_path: Path) -> None:
    cfg = load_config(config_path)
    transcript_clean = read_json(transcript_clean_path)

    # Accept raw JSON text too (in case saved as .txt)
    raw = llm_json_path.read_text(encoding="utf-8").strip()
    minutes_obj = extract_json(raw) if not raw.startswith("{") else json.loads(raw)

    schema = load_schema(cfg["__project_root__"], cfg["summarize"]["schema_path"])
    err = try_validate_schema(minutes_obj, schema)
    sections = minutes_obj.get("sections") or []
    use_sections_format = sections and isinstance(sections, list) and len(sections) > 0
    if err and not use_sections_format:
        notes_val = minutes_obj.get("notes", "")
        if isinstance(notes_val, dict):
            notes_val = json.dumps(notes_val, ensure_ascii=False)
        else:
            notes_val = str(notes_val or "")
        minutes_obj["notes"] = (notes_val + "\n\n[SchemaValidationError]\n" + err).strip()

    if use_sections_format:
        md = _render_minutes_md_sections_format(minutes_obj)
    else:
        md = render_minutes_md(minutes_obj)

    quality_warnings = check_minutes_quality(minutes_obj)
    if quality_warnings:
        print("[品質チェック]")
        for w in quality_warnings:
            print(f"  - {w}")

    out_md = llm_json_path.parent / cfg["summarize"].get("output_md", "minutes_draft.md")
    write_text(out_md, md)
    print(f"[OK] Output: {out_md}")


def eval_pipeline(config_path: Path) -> None:
    cfg = load_config(config_path)
    print("[EVAL] config ok")
    print("[EVAL] steps:", cfg["pipeline"]["steps"])
    print("[EVAL] summarize.engine:", cfg["summarize"].get("engine"))


def _ensure_run_dirs(rp) -> None:
    ensure_dir(rp.run_dir)
    ensure_dir(rp.logs_dir)


# -----------------------------
# ASR (Whisper)
# -----------------------------
def _step_asr(input_media: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    engine = cfg["asr"].get("engine", "whisper")
    if engine != "whisper":
        raise ValueError(f"Unsupported ASR engine: {engine}")

    # Prefer faster-whisper
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model_name = cfg["asr"].get("model", "large-v3")
        device = cfg["asr"].get("device", "cpu")
        compute_type = cfg["asr"].get("compute_type", "int8")

        def _load_faster_whisper():
            return WhisperModel(model_name, device=device, compute_type=compute_type)

        model = _retry_on_network_error(_load_faster_whisper)
        segments_iter, info = model.transcribe(str(input_media), vad_filter=True)
        segments = []
        for s in segments_iter:
            segments.append({"start": float(s.start), "end": float(s.end), "speaker": None, "text": (s.text or "").strip()})
        return {"language": getattr(info, "language", None), "segments": segments}
    except ImportError:
        pass

    # Fallback: openai-whisper
    try:
        import whisper  # type: ignore
        model_name = cfg["asr"].get("model", "large")

        def _load_openai_whisper():
            return whisper.load_model(model_name)

        model = _retry_on_network_error(_load_openai_whisper)
        result = model.transcribe(str(input_media), fp16=False)
        segments = []
        for s in result.get("segments", []):
            segments.append({"start": float(s.get("start", 0.0)), "end": float(s.get("end", 0.0)), "speaker": None, "text": (s.get("text", "") or "").strip()})
        return {"language": result.get("language"), "segments": segments}
    except ImportError as e:
        raise RuntimeError(
            "Whisper backend not found. Install one of:\n"
            "  pip install openai-whisper\n"
            "  pip install faster-whisper\n"
            "Or install with optional deps: pip install -e \".[asr]\""
        ) from e


# -----------------------------
# Preprocess (rule-driven)
# -----------------------------
def _step_preprocess(transcript: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    segs: List[Dict[str, Any]] = transcript.get("segments", [])
    terms_map = _load_terms_map(cfg)
    stop_phrases = _load_stop_phrases(cfg)

    cleaned_segments = []
    for seg in segs:
        text = seg.get("text", "") or ""
        text = _normalize_whitespace(text)
        text = _apply_term_map(text, terms_map)
        text = _remove_stop_phrases(text, stop_phrases)
        text = _light_cleanup(text)
        if text.strip():
            cleaned_segments.append({**seg, "text": text})

    out = dict(transcript)
    out["segments"] = cleaned_segments
    return out


def _load_terms_map(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    path = cfg["preprocess"]["dictionaries"].get("terms_csv")
    if not path:
        return []
    csv_path = (cfg["__project_root__"] / path).resolve()
    if not csv_path.exists():
        return []
    pairs: List[Tuple[str, str]] = []
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",", 1)]
        if len(parts) != 2:
            continue
        pairs.append((parts[0], parts[1]))
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    return pairs


def _load_stop_phrases(cfg: Dict[str, Any]) -> List[str]:
    path = cfg["preprocess"]["dictionaries"].get("stop_phrases")
    if not path:
        return []
    p = (cfg["__project_root__"] / path).resolve()
    if not p.exists():
        return []
    items = []
    for line in p.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if not t or t.startswith("#"):
            continue
        items.append(t)
    items.sort(key=len, reverse=True)
    return items


def _apply_term_map(text: str, pairs: List[Tuple[str, str]]) -> str:
    for frm, to in pairs:
        text = text.replace(frm, to)
    return text


def _remove_stop_phrases(text: str, stop_phrases: List[str]) -> str:
    for s in stop_phrases:
        text = text.replace(s, "")
    return text


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip()


def _light_cleanup(text: str) -> str:
    return text.replace("、、", "、").replace("。。", "。").strip()


# -----------------------------
# Summarize (LLM adapters)
# -----------------------------
def _step_summarize(transcript_clean: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    project_root: Path = cfg["__project_root__"]
    prompt_text = load_prompt_text(project_root, cfg["summarize"]["prompt_path"])
    schema = load_schema(project_root, cfg["summarize"]["schema_path"])

    system_prompt = (
        "あなたは高精度な議事録作成アシスタントです。"
        "必ず指定されたJSON Schemaに適合する**JSONのみ**を返してください。"
        "余計な文章やMarkdownは禁止です。"
        "決定事項とToDo（担当・期限）を特に重視してください。"
        "ToDoには会議後にやるタスクのみを含めてください。"
    )

    transcript_block = _format_transcript_for_prompt(
        transcript_clean, max_chars=int(cfg['summarize'].get('max_transcript_chars', 40000))
    )

    user_prompt = (
        prompt_text.strip()
        + "\n\n"
        + "## 文字起こし（整形後）\n"
        + transcript_block
        + "\n\n"
        + "## 出力はJSONのみ\n"
        + _schema_hint(schema)
    )

    engine = cfg["summarize"].get("engine", "mock")
    model = cfg["summarize"].get("model")
    ollama_base = cfg["summarize"].get("ollama_base_url", "http://localhost:11434")

    summarizer = get_summarizer(engine, ollama_base_url=ollama_base)
    minutes_obj = run_llm_and_parse_json(summarizer, system_prompt, user_prompt, model=model)

    err = try_validate_schema(minutes_obj, schema)
    if err:
        minutes_obj.setdefault("notes", "")
        minutes_obj["notes"] = (minutes_obj["notes"] + "\n\n[SchemaValidationError]\n" + err).strip()

    return render_minutes_md(minutes_obj)


def _write_request_pack(transcript_clean: Dict[str, Any], cfg: Dict[str, Any], out_dir: Path) -> None:
    """Create files for ChatGPT/Copilot UI summarization (no API)."""
    schema = load_schema(cfg["__project_root__"], cfg["summarize"]["schema_path"])
    prompt_text = load_prompt_text(cfg["__project_root__"], cfg["summarize"]["prompt_path"])

    transcript_block = _format_transcript_for_prompt(transcript_clean, max_chars=int(cfg['summarize'].get('max_transcript_chars', 40000)))

    instr_name = cfg["summarize"].get("manual_instructions_md", "llm_instructions.md")
    txt_name = cfg["summarize"].get("manual_transcript_txt", "llm_transcript.txt")

    instructions = f"""# LLM UI Instructions (ChatGPT / Copilot)

## Inputs
- Attach the file: **{txt_name}**
- Then paste the instruction below (this document) into the chat.

## Instruction to the LLM
あなたは高精度な議事録作成アシスタントです。
次の条件を必ず守ってください。

- **出力はJSONのみ**
- **コードフェンス（```）や前置き、解説は禁止**
- JSONは **指定されたSchemaの必須キーを欠かさない**
- 決定事項とToDo（担当・期限）を特に重視
- ToDoは**会議後にやるタスクのみ**を含める。会議中のルール・手順（例：マイク/カメラオフ、質問はチャットへ）はToDoに含めない
- next_stepsは空でよい（ToDoに一本化）
- 任意で、決定事項・ToDoに発言時刻（例: 00:12:34）や根拠の短い引用（証跡）を付与するとよい
- 不確かな場合は推測しない（未確定として書く、期限/担当が不明なら空文字でも可）
- 日本語で書く

### JSON Schema 必須トップレベルキー
{", ".join(schema.get("required", []) or [])}

### 参考の作業指示（テンプレ）
{prompt_text.strip()}

---
上記に加えて、添付ファイル **{txt_name}** の文字起こし内容を読んで議事録JSONを作成してください。
"""

    # write transcript file (for attachment)
    transcript_txt = transcript_block

    write_text(out_dir / instr_name, instructions)
    write_text(out_dir / txt_name, transcript_txt)


def _write_request_pack_chunked(cfg: Dict[str, Any], out_dir: Path, manifest: Dict[str, Any]) -> None:
    """Create instructions for chunked flow: per-chunk extract + merge."""
    schema = load_schema(cfg["__project_root__"], cfg["summarize"]["schema_path"])
    prompt_text = load_prompt_text(cfg["__project_root__"], cfg["summarize"]["prompt_path"])
    chunks_dir = out_dir / "chunks"
    chunk_list = manifest.get("chunks", [])
    req_keys = ", ".join(schema.get("required", []) or [])

    chunk_instr = f"""# チャンク別抽出（ChatGPT / Copilot）

## 手順
1. 以下の「チャンクファイル」を **1本ずつ** 添付して、同じ指示で実行する
2. 各回の出力は **JSONのみ**（コードフェンス禁止）。中間形式でOK
   - decisions[]（決定事項候補）
   - todos[]（owner / task / due、分からなければ空欄可）
   - topics[]（論点ラベル）
3. 各回のJSONを partial_01.json, partial_02.json, ... として保存する
4. 全チャンク終了後、**統合**用の指示（llm_instructions_merge.md）で最終JSONを作成する

## チャンク一覧（chunks/ フォルダ内）
"""
    for i, c in enumerate(chunk_list, 1):
        fname = c.get("file", f"chunk_{i:02d}.txt")
        chunk_instr += f"- {fname} （開始 {c.get('start_sec')}秒、{c.get('char_count')} 文字）\n"

    chunk_instr += f"""
## 各チャンクへの指示（貼り付けて使用）
{prompt_text.strip()}

- **出力はJSONのみ**（コードフェンス禁止）
- 必須トップレベル: {req_keys}
- 決定事項とToDoを最優先で抽出。可能なら根拠のタイムスタンプも付与
- ToDoは会議後にやるタスクのみを含める（会議中のルール・手順はToDoに含めない）
"""
    write_text(out_dir / "llm_instructions_chunk.md", chunk_instr)

    merge_instr = """# 統合（最終JSON）

## 手順
1. これまでに得た partial_01.json, partial_02.json, ... の内容を貼り付ける（または列挙）
2. 以下を守って **1つの最終JSON** に統合する
   - 重複ToDoは1件にまとめる（同一タスク）
   - 期限が矛盾している場合は「未確定」にする
   - 決定事項と未決事項を混同しない
3. 出力はJSONのみ（コードフェンス禁止）。Schemaの必須キーを欠かさない

## 必須キー
""" + req_keys + """

## 統合ルール
- decisions: 重複除去
- todos: 同一タスクは統合、期限矛盾時は due = 未確定
- topics / open_questions / next_steps: 重複除去
"""
    write_text(out_dir / "llm_instructions_merge.md", merge_instr)


def _schema_hint(schema: Dict[str, Any]) -> str:
    req = schema.get("required", []) or []
    return "必須トップレベルキー: " + ", ".join(req)


def _format_transcript_for_prompt(transcript: Dict[str, Any], max_chars: int = 40000) -> str:
    segs = transcript.get("segments", []) or []
    lines = []
    total = 0
    for s in segs:
        start = float(s.get("start", 0.0))
        speaker = s.get("speaker") or "Speaker"
        text = (s.get("text") or "").strip()
        if not text:
            continue
        line = f"[{_sec_to_mmss(start)}] {speaker}: {text}"
        lines.append(line)
        total += len(line) + 1
        if total > max_chars:
            lines.append("...（以下省略）")
            break
    return "\n".join(lines)


def _format_transcript_plain(transcript: Dict[str, Any], max_chars: int = 20000) -> str:
    segs = transcript.get("segments", []) or []
    txt = "\n".join([(s.get("text") or "").strip() for s in segs if (s.get("text") or "").strip()])
    return txt[:max_chars]


def _sec_to_mmss(sec: float) -> str:
    m = int(sec) // 60
    s = int(sec) % 60
    return f"{m:02d}:{s:02d}"


# -----------------------------
# Chunk (2時間対応：文字数分割)
# -----------------------------
def run_chunk(transcript_clean_path: Path, config_path: Path) -> None:
    """Split transcript_clean.json into chunks (20k–40k chars) and write manifest."""
    cfg = load_config(config_path)
    transcript_clean = read_json(transcript_clean_path)
    run_dir = transcript_clean_path.parent
    chunks_dir = run_dir / "chunks"
    ensure_dir(chunks_dir)

    target_chars = int(cfg.get("chunk", {}).get("target_chars", 30000))
    min_chars = int(cfg.get("chunk", {}).get("min_chars", 10000))

    slices = _build_chunk_slices(
        transcript_clean, target_chars=target_chars, min_chars=min_chars
    )
    segs = transcript_clean.get("segments", []) or []
    chunk_list: List[Dict[str, Any]] = []

    for idx, (start_i, end_i, start_sec, end_sec, char_count) in enumerate(slices, 1):
        chunk_segs = segs[start_i:end_i]
        lines = []
        for s in chunk_segs:
            start = float(s.get("start", 0.0))
            speaker = s.get("speaker") or "Speaker"
            text = (s.get("text") or "").strip()
            if text:
                lines.append(f"[{_sec_to_mmss(start)}] {speaker}: {text}")
        chunk_path = chunks_dir / f"chunk_{idx:02d}.txt"
        write_text(chunk_path, "\n".join(lines))
        chunk_list.append({
            "file": chunk_path.name,
            "start_sec": round(start_sec, 1),
            "end_sec": round(end_sec, 1),
            "char_count": char_count,
        })

    manifest = {
        "source": str(transcript_clean_path),
        "target_chars": target_chars,
        "chunks": chunk_list,
    }
    write_json(chunks_dir / "manifest.json", manifest)
    print(f"[OK] Chunks: {chunks_dir} ({len(chunk_list)} files)")


def _build_chunk_slices(
    transcript: Dict[str, Any], target_chars: int = 30000, min_chars: int = 10000
) -> List[Tuple[int, int, float, float, int]]:
    """Build (start_idx, end_idx, start_sec, end_sec, char_count) per chunk."""
    segs = transcript.get("segments", []) or []
    if not segs:
        return []

    slices: List[Tuple[int, int, float, float, int]] = []
    start_i = 0
    acc = 0
    chunk_start_sec = float(segs[0].get("start", 0.0))

    for i, s in enumerate(segs):
        start = float(s.get("start", 0.0))
        speaker = s.get("speaker") or "Speaker"
        text = (s.get("text") or "").strip()
        line = f"[{_sec_to_mmss(start)}] {speaker}: {text}" if text else ""
        line_len = len(line) + (1 if line else 0)
        acc += line_len
        end_sec = float(s.get("end", start))

        if acc >= target_chars or (acc >= min_chars and i == len(segs) - 1):
            slices.append((start_i, i + 1, chunk_start_sec, end_sec, acc))
            start_i = i + 1
            acc = 0
            if start_i < len(segs):
                chunk_start_sec = float(segs[start_i].get("start", 0.0))

    if start_i < len(segs):
        acc = 0
        for j in range(start_i, len(segs)):
            s = segs[j]
            st = float(s.get("start", 0.0))
            sp = s.get("speaker") or "Speaker"
            tx = (s.get("text") or "").strip()
            ln = f"[{_sec_to_mmss(st)}] {sp}: {tx}" if tx else ""
            acc += len(ln) + (1 if ln else 0)
        slices.append((start_i, len(segs), chunk_start_sec, float(segs[-1].get("end", 0.0)), acc))

    return slices


# -----------------------------
# Merge (部分要約 → 最終JSON)
# -----------------------------
def run_merge(partial_paths: List[Path], config_path: Path, out_path: Path | None = None) -> Path:
    """Merge partial JSONs into one schema-compliant final JSON. Dedupe ToDo; conflicting due → 未確定."""
    if not partial_paths:
        raise ValueError("At least one partial JSON path is required.")
    cfg = load_config(config_path)
    project_root: Path = cfg["__project_root__"]
    schema = load_schema(project_root, cfg["summarize"]["schema_path"])

    merged: Dict[str, Any] = {
        "meeting": {"title": "", "date": "", "participants": []},
        "summary": [],
        "decisions": [],
        "todos": [],
        "topics": [],
        "open_questions": [],
        "next_steps": [],
        "notes": "",
    }

    all_decisions: List[Dict[str, Any]] = []
    all_todos: List[Dict[str, Any]] = []
    all_topics: List[str] = []
    all_open: List[str] = []
    all_next: List[str] = []
    meeting_seen = False

    for p in partial_paths:
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8").strip()
        obj = extract_json(raw) if not raw.startswith("{") else json.loads(raw)
        for d in obj.get("decisions", []) or []:
            all_decisions.append(_normalize_decision_item(d))
        all_todos.extend(obj.get("todos", []) or [])
        all_topics.extend(obj.get("topics", []) or [])
        all_open.extend(obj.get("open_questions", []) or [])
        all_next.extend(obj.get("next_steps", []) or [])
        if not meeting_seen and obj.get("meeting"):
            merged["meeting"] = {**merged["meeting"], **obj["meeting"]}
            meeting_seen = True
        if obj.get("summary"):
            merged["summary"] = merged["summary"] or obj["summary"]

    merged["decisions"] = _merge_decisions(all_decisions)
    merged["todos"] = _merge_todos(all_todos)
    merged["topics"] = _dedupe_strings(all_topics)
    merged["open_questions"] = _dedupe_strings(all_open)
    merged["next_steps"] = _dedupe_strings(all_next)

    err = try_validate_schema(merged, schema)
    if err:
        merged.setdefault("notes", "")
        merged["notes"] = (merged["notes"] + "\n\n[SchemaValidationError]\n" + err).strip()

    if out_path is None:
        run_dir = partial_paths[0].parent if partial_paths else Path.cwd()
        out_path = run_dir / "llm_output.json"
    write_json(out_path, merged)
    print(f"[OK] Merged: {out_path}")
    return out_path


def _normalize_decision_item(d: Any) -> Dict[str, Any]:
    """Normalize decision item (string or object) to { text, timestamp?, evidence? }."""
    if isinstance(d, str):
        return {"text": d.strip(), "timestamp": "", "evidence": ""}
    if isinstance(d, dict):
        return {
            "text": (d.get("text") or "").strip(),
            "timestamp": (d.get("timestamp") or "").strip(),
            "evidence": (d.get("evidence") or "").strip(),
        }
    return {"text": str(d), "timestamp": "", "evidence": ""}


def _merge_decisions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedupe by text; merge timestamp/evidence from first occurrence."""
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for x in items:
        text = (x.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        entry: Dict[str, Any] = {"text": text}
        if (x.get("timestamp") or "").strip():
            entry["timestamp"] = (x.get("timestamp") or "").strip()
        if (x.get("evidence") or "").strip():
            entry["evidence"] = (x.get("evidence") or "").strip()
        out.append(entry)
    return out


def _dedupe_strings(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out = []
    for x in items:
        t = (x or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _merge_todos(todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedupe by task; if same task with different due → due = 未確定. Preserve timestamp/evidence."""
    key_to_todo: Dict[str, Dict[str, Any]] = {}
    for t in todos:
        task = (t.get("task") or "").strip()
        if not task:
            continue
        owner = (t.get("owner") or "").strip()
        due = (t.get("due") or "").strip()
        ts = (t.get("timestamp") or "").strip()
        ev = (t.get("evidence") or "").strip()
        key = task
        if key in key_to_todo:
            existing = key_to_todo[key]
            if (existing.get("due") or "").strip() != due and due:
                existing["due"] = "未確定"
            if ts and not (existing.get("timestamp") or "").strip():
                existing["timestamp"] = ts
            if ev and not (existing.get("evidence") or "").strip():
                existing["evidence"] = ev
        else:
            key_to_todo[key] = {"owner": owner, "task": task, "due": due or ""}
            if ts:
                key_to_todo[key]["timestamp"] = ts
            if ev:
                key_to_todo[key]["evidence"] = ev
    return list(key_to_todo.values())


# -----------------------------
# Quality check (standalone)
# -----------------------------
def run_check(json_path: Path, config_path: Path) -> None:
    """Run quality check on minutes JSON and print warnings."""
    cfg = load_config(config_path)
    raw = json_path.read_text(encoding="utf-8").strip()
    minutes_obj = extract_json(raw) if not raw.startswith("{") else json.loads(raw)
    schema = load_schema(cfg["__project_root__"], cfg["summarize"]["schema_path"])
    err = try_validate_schema(minutes_obj, schema)
    if err:
        print(f"[Schema] 検証エラー: {err}")
    else:
        print("[Schema] OK")
    warnings = check_minutes_quality(minutes_obj)
    if warnings:
        print("[品質チェック]")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("[品質チェック] 警告なし")

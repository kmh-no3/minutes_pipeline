from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def _decision_text_timestamp_evidence(d: Any) -> tuple[str, str, str]:
    """Normalize decision item (string or object) to (text, timestamp, evidence)."""
    if isinstance(d, str):
        return (d.strip(), "", "")
    if isinstance(d, dict):
        text = (d.get("text") or d.get("decision") or "").strip()
        ts = (d.get("timestamp") or "").strip()
        ev = (d.get("evidence") or d.get("evidence_quote") or "").strip()
        return (text, ts, ev)
    return (str(d), "", "")


def check_minutes_quality(minutes: Dict[str, Any]) -> List[str]:
    """品質チェック: ToDo空欄率・期限形式・決定事項/ToDo 0件警告。警告メッセージのリストを返す。"""
    warnings: List[str] = []
    decisions_raw = minutes.get("decisions") or []
    todos = minutes.get("todos") or []
    if not decisions_raw:
        warnings.append("決定事項が0件です。")
    if not todos:
        warnings.append("ToDoが0件です。")

    n_todos = len(todos)
    if n_todos > 0:
        empty_owner = sum(1 for t in todos if not (t.get("owner") or "").strip())
        empty_task = sum(1 for t in todos if not (t.get("task") or "").strip())
        empty_due = sum(1 for t in todos if not (t.get("due") or "").strip())
        warnings.append(
            f"ToDo空欄率: owner {empty_owner}/{n_todos}, task {empty_task}/{n_todos}, due {empty_due}/{n_todos}"
        )
        # 期限形式: YYYY-MM-DD または 次回まで / 未確定 など
        due_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        non_standard_due = []
        for t in todos:
            due = (t.get("due") or "").strip()
            if due and not due_re.match(due) and due not in ("未確定", "次回まで", "次回", ""):
                non_standard_due.append(due)
        if non_standard_due:
            warnings.append(f"期限の形式（YYYY-MM-DD推奨）: 非標準例: {non_standard_due[:5]}")

    return warnings


def _participants_to_strings(participants_raw: Any) -> List[str]:
    """Normalize participants (string or list of str/dict) to list of display strings."""
    if not participants_raw:
        return []
    if isinstance(participants_raw, str):
        return [participants_raw.strip()] if participants_raw.strip() else []
    result: List[str] = []
    for p in participants_raw:
        if isinstance(p, str):
            if p.strip():
                result.append(p.strip())
        elif isinstance(p, dict):
            name = (p.get("name") or p.get("role") or "").strip()
            if name:
                result.append(name)
        else:
            result.append(str(p))
    return result


def _summary_to_strings(summary_raw: Any) -> List[str]:
    """Normalize summary (array of strings or dict with overview/highlights) to list of strings."""
    if not summary_raw:
        return []
    if isinstance(summary_raw, list):
        return [str(s).strip() for s in summary_raw if str(s).strip()]
    if isinstance(summary_raw, dict):
        lines: List[str] = []
        overview = (summary_raw.get("overview") or "").strip()
        if overview:
            lines.append(overview)
        for h in summary_raw.get("highlights") or []:
            s = (h if isinstance(h, str) else str(h)).strip()
            if s:
                lines.append(s)
        return lines
    return [str(summary_raw)]


def _item_to_string(item: Any, text_keys: tuple[str, ...]) -> str:
    """Normalize list item to display string (string or dict with one of text_keys)."""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        for k in text_keys:
            v = item.get(k)
            if v and isinstance(v, str) and v.strip():
                return v.strip()
    return str(item)


def _list_to_strings(raw: Any, text_keys: tuple[str, ...] = ("topic", "question", "step")) -> List[str]:
    """Normalize list of str or dict to list of display strings."""
    if not raw:
        return []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    return [_item_to_string(x, text_keys) for x in raw]


def _sanitize_notes(notes_raw: Any) -> str:
    """Remove SchemaValidationError and everything after it from notes. Return cleaned string (may be empty)."""
    notes_str = notes_raw if isinstance(notes_raw, str) else json.dumps(notes_raw, ensure_ascii=False)
    if "[SchemaValidationError]" in notes_str:
        notes_str = notes_str.split("[SchemaValidationError]")[0].strip()
    return notes_str.strip()


def _render_section_content(sec: Dict[str, Any], md: List[str]) -> None:
    """Append one section's content (bullets, items, steps, qa, etc.) to md."""
    if "bullets" in sec:
        for b in sec.get("bullets") or []:
            md.append(f"- {b}" if isinstance(b, str) else f"- {json.dumps(b, ensure_ascii=False)}")
    if "items" in sec:
        for it in sec.get("items") or []:
            if isinstance(it, str):
                md.append(f"- {it}")
            elif isinstance(it, dict):
                if "subsection" in it and "content" in it:
                    md.append(f"- **{it.get('subsection', '')}**: {it.get('content', '')}")
                elif "subsection" in it and "bullets" in it:
                    md.append(f"- **{it.get('subsection', '')}**")
                    for b in it.get("bullets") or []:
                        md.append(f"  - {b}")
                elif "tool" in it and "purpose" in it:
                    md.append(f"- **{it.get('tool', '')}**: {it.get('purpose', '')}")
                elif "owner" in it and "task" in it:
                    md.append(f"- {it.get('owner', '')}: {it.get('task', '')}")
                else:
                    md.append(f"- {json.dumps(it, ensure_ascii=False)}")
    if "steps" in sec:
        for s in sec.get("steps") or []:
            md.append(f"- {s}")
    if "flow" in sec:
        for f in sec.get("flow") or []:
            md.append(f"- {f}")
    if "example_findings" in sec:
        for e in sec.get("example_findings") or []:
            md.append(f"- {e}")
    if "qa" in sec:
        for qa in sec.get("qa") or []:
            if isinstance(qa, dict):
                q = qa.get("question", "")
                a = qa.get("answer", "")
                md.append(f"- **Q:** {q}")
                md.append(f"  **A:** {a}")
    if "timing" in sec or "note" in sec:
        t = (sec.get("timing") or "").strip()
        n = (sec.get("note") or "").strip()
        if t or n:
            md.append(f"- {t}; {n}".strip(" ;"))


def _render_minutes_md_sections_format(minutes: Dict[str, Any]) -> str:
    """Render minutes when JSON uses top-level title + sections (e.g. small run LLM output)."""
    md: List[str] = []
    title = (minutes.get("title") or "（未設定）").strip()
    md.append("# 議事録（ドラフト）")
    md.append("")
    md.append("## 会議情報")
    md.append(f"- タイトル: {title}")
    date = (minutes.get("created_at_local_date") or "").strip()
    if date:
        md.append(f"- 日付: {date}")
    topic = (minutes.get("topic") or "").strip()
    if topic:
        md.append(f"- トピック: {topic}")
    fmt = (minutes.get("format") or "").strip()
    if fmt:
        md.append(f"- 形式: {fmt}")
    dur = minutes.get("duration_estimate_minutes")
    if dur is not None:
        md.append(f"- 所要時間（目安）: 約{dur}分")
    md.append("")

    for sec in minutes.get("sections") or []:
        name = (sec.get("name") or "").strip()
        if not name:
            continue
        md.append(f"## {name}")
        md.append("")
        _render_section_content(sec, md)
        md.append("")

    notes_str = _sanitize_notes(minutes.get("notes", "") or "")
    if notes_str:
        md.append("## 補足")
        md.append(notes_str)
        md.append("")

    return "\n".join(md)


def render_minutes_md(minutes: Dict[str, Any]) -> str:
    sections = minutes.get("sections") or []
    use_sections_format = (
        sections and isinstance(sections, list) and len(sections) > 0
    ) or (
        "document_type" in minutes
        and minutes.get("title")
        and not minutes.get("meeting")
        and sections
        and len(sections) > 0
    )
    if use_sections_format:
        return _render_minutes_md_sections_format(minutes)

    meeting = minutes.get("meeting", {}) or {}
    title = meeting.get("title", "（未設定）")
    date = meeting.get("date", "")
    participants_raw = meeting.get("participants", []) or []
    participants = _participants_to_strings(participants_raw)

    summary_raw = minutes.get("summary", []) or []
    summary = _summary_to_strings(summary_raw)
    decisions_raw = minutes.get("decisions") or []
    todos: List[Dict[str, Any]] = minutes.get("todos", []) or []
    topics_raw = minutes.get("topics", []) or []
    topics = _list_to_strings(topics_raw, ("topic",))
    open_q_raw = minutes.get("open_questions", []) or []
    open_q = _list_to_strings(open_q_raw, ("question",))
    next_steps_raw = minutes.get("next_steps", []) or []
    next_steps = _list_to_strings(next_steps_raw, ("step",))
    notes: str = _sanitize_notes(minutes.get("notes", "") or "")

    md: List[str] = []
    md.append("# 議事録（ドラフト）")
    md.append("")
    md.append("## 会議情報")
    md.append(f"- タイトル: {title}")
    if date:
        md.append(f"- 日付: {date}")
    if participants:
        md.append("- 参加者: " + ", ".join(participants))
    md.append("")

    md.append("## サマリ")
    if summary:
        for s in summary:
            md.append(f"- {s}")
    else:
        md.append("- （要約なし）")
    md.append("")

    md.append("## 決定事項")
    if decisions_raw:
        for d in decisions_raw:
            text, ts, ev = _decision_text_timestamp_evidence(d)
            line = f"- {text}"
            if ts or ev:
                extras = [x for x in (f"時刻:{ts}" if ts else None, f"根拠:{ev}" if ev else None) if x]
                line += " " + " ".join(f"（{e}）" for e in extras)
            md.append(line)
    else:
        md.append("- （決定事項なし）")
    md.append("")

    md.append("## ToDo")
    md.append("|担当|内容|期限|証跡（時刻・引用）|")
    md.append("|---|---|---|---|")
    if todos:
        for t in todos:
            owner = (t.get("owner") or "").strip()
            task = (t.get("task") or "").strip()
            due = (t.get("due") or "").strip()
            ts = (t.get("timestamp") or "").strip()
            ev = (t.get("evidence") or t.get("evidence_quote") or "").strip()
            evidence_cell = " / ".join(x for x in (ts, ev) if x) or ""
            md.append(f"|{owner}|{task}|{due}|{evidence_cell}|")
    else:
        md.append("| | | | |")
    md.append("")

    md.append("## 論点・検討事項")
    if topics:
        for t in topics:
            md.append(f"- {t}")
    else:
        md.append("- （論点なし）")
    md.append("")

    md.append("## 未決事項・オープンクエスチョン")
    if open_q:
        for q in open_q:
            md.append(f"- {q}")
    else:
        md.append("- （未決事項なし）")
    md.append("")

    md.append("## 次のアクション")
    if next_steps:
        for n in next_steps:
            md.append(f"- {n}")
    else:
        md.append("- （次アクションなし）")
    md.append("")

    if notes:
        md.append("## 補足")
        md.append(notes)
        md.append("")

    return "\n".join(md)

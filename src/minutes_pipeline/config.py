from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml  # PyYAML

from .io import read_json

DEFAULT_CONFIG_NAME = "minutes.yml"
METADATA_FILENAME = "run_metadata.json"


def resolve_config(explicit: Path | None, metadata_dir: Path | None = None) -> Path:
    """Resolve config path by:
    1) explicit --config
    2) run_metadata.json in metadata_dir (e.g. input file's dir) if it has config_path
    3) searching current dir -> parents for minutes.yml
    """
    if explicit:
        if explicit.exists():
            return explicit.resolve()
        raise FileNotFoundError(f"Config not found: {explicit}")

    if metadata_dir is not None:
        meta_path = metadata_dir.resolve() / METADATA_FILENAME
        if meta_path.exists():
            try:
                meta = read_json(meta_path)
                cfg_path_str = meta.get("config_path") if isinstance(meta, dict) else None
                if cfg_path_str:
                    cfg_path = Path(cfg_path_str)
                    if cfg_path.exists():
                        return cfg_path.resolve()
            except (OSError, ValueError, KeyError):
                pass

    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        candidate = p / DEFAULT_CONFIG_NAME
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"{DEFAULT_CONFIG_NAME} not found in current/parent directories. "
        f"Place it in your project folder or pass --config."
    )


def load_config(config_path: Path) -> Dict[str, Any]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(cfg, dict):
        raise ValueError("minutes.yml must be a mapping (YAML dict).")

    project_root = config_path.parent.resolve()
    cfg["__project_root__"] = project_root

    # defaults
    cfg.setdefault("paths", {})
    cfg["paths"].setdefault("input_dir", "input")
    cfg["paths"].setdefault("output_dir", "output")
    cfg["paths"].setdefault("logs_dir", "logs")

    cfg.setdefault("naming", {})
    cfg["naming"].setdefault("output_folder", "{date}_{stem}")

    cfg.setdefault("pipeline", {})
    cfg["pipeline"].setdefault("steps", ["asr", "preprocess", "summarize"])
    cfg["pipeline"].setdefault("save_intermediates", True)

    cfg.setdefault("asr", {})
    cfg["asr"].setdefault("engine", "whisper")
    cfg["asr"].setdefault("model", "large-v3")

    cfg.setdefault("preprocess", {})
    cfg["preprocess"].setdefault("dictionaries", {})

    cfg.setdefault("summarize", {})
    # engines:
    # - mock: offline deterministic
    # - manual: generate request pack for ChatGPT/Copilot UI (no API)
    # - openai/anthropic/ollama: optional
    cfg["summarize"].setdefault("engine", "mock")
    cfg["summarize"].setdefault("model", None)
    cfg["summarize"].setdefault("output_md", "minutes_draft.md")
    cfg["summarize"].setdefault("prompt_path", "prompts/minutes_prompt.md")
    cfg["summarize"].setdefault("schema_path", "prompts/minutes_schema.json")
    cfg["summarize"].setdefault("max_transcript_chars", 40000)
    cfg["summarize"].setdefault("ollama_base_url", "http://localhost:11434")

    # manual request pack filenames
    cfg["summarize"].setdefault("manual_instructions_md", "llm_instructions.md")
    cfg["summarize"].setdefault("manual_transcript_txt", "llm_transcript.txt")

    cfg.setdefault("chunk", {})
    cfg["chunk"].setdefault("target_chars", 30000)
    cfg["chunk"].setdefault("min_chars", 10000)

    return cfg

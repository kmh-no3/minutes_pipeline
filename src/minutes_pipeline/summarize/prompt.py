from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from .schema import DEFAULT_SCHEMA


def load_prompt_text(project_root: Path, prompt_path: str) -> str:
    p = (project_root / prompt_path).resolve()
    if p.exists():
        return p.read_text(encoding="utf-8")
    return default_prompt()


def load_schema(project_root: Path, schema_path: str) -> Dict[str, Any]:
    p = (project_root / schema_path).resolve()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return DEFAULT_SCHEMA


def try_validate_schema(obj: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(instance=obj, schema=schema)
        return None
    except ImportError:
        return None
    except Exception as e:  # noqa
        return str(e)


def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model output.")
    return json.loads(m.group(0))


def default_prompt() -> str:
    return (
        "以下の文字起こしから議事録を作成してください。"
        "出力はJSONのみで、指定されたJSON Schemaに適合させてください。"
    )

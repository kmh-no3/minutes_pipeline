from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunPaths:
    project_root: Path
    output_root: Path
    run_dir: Path
    logs_dir: Path
    transcript_raw: Path
    transcript_clean: Path
    minutes_md: Path
    metadata_json: Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def materialize_run_paths(
    project_root: Path,
    output_dir: Path,
    run_folder_name: str,
    minutes_md_name: str = "minutes_draft.md",
) -> RunPaths:
    output_root = (project_root / output_dir).resolve()
    run_dir = output_root / run_folder_name
    logs_dir = run_dir / "logs"

    return RunPaths(
        project_root=project_root,
        output_root=output_root,
        run_dir=run_dir,
        logs_dir=logs_dir,
        transcript_raw=run_dir / "transcript_raw.json",
        transcript_clean=run_dir / "transcript_clean.json",
        minutes_md=run_dir / minutes_md_name,
        metadata_json=run_dir / "run_metadata.json",
    )

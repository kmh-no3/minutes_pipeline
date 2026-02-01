from __future__ import annotations

import argparse
from pathlib import Path

from .config import resolve_config
from .pipeline import (
    run_pipeline,
    summarize_only,
    eval_pipeline,
    request_pack,
    apply_llm_output,
    run_chunk,
    run_merge,
    run_check,
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="mpipe")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run full pipeline from media input (mp4/wav).")
    p_run.add_argument("input", type=str, help="Input media file path (mp4/wav).")
    p_run.add_argument("--config", type=str, default=None, help="Path to minutes.yml (optional).")

    p_sum = sub.add_parser("summarize", help="Summarize from cleaned transcript json (engine in minutes.yml).")
    p_sum.add_argument("input", type=str, help="Input transcript_clean.json path.")
    p_sum.add_argument("--config", type=str, default=None)

    p_req = sub.add_parser(
        "request",
        help="Generate ChatGPT/Copilot request pack from transcript_clean.json (manual flow). "
        "Uses config from run_metadata.json in the same dir as input when --config is omitted.",
    )
    p_req.add_argument("input", type=str, help="Input transcript_clean.json path.")
    p_req.add_argument("--mode", type=str, default="full", choices=["full", "chunked"], help="full: 1 file; chunked: per-chunk instructions (requires mpipe chunk first).")
    p_req.add_argument("--config", type=str, default=None, help="Override config (default: use config_path from input dir's run_metadata.json).")

    p_chunk = sub.add_parser("chunk", help="Split transcript_clean.json into chunks (20k–40k chars) for 2h meetings.")
    p_chunk.add_argument("input", type=str, help="Input transcript_clean.json path.")
    p_chunk.add_argument("--config", type=str, default=None)

    p_merge = sub.add_parser("merge", help="Merge partial JSONs (from chunked summarization) into final schema JSON.")
    p_merge.add_argument("partials", type=str, nargs="+", help="Paths to partial_01.json, partial_02.json, ... (or glob).")
    p_merge.add_argument("--output", "-o", type=str, default=None, help="Output JSON path (default: same dir as first partial).")
    p_merge.add_argument("--config", type=str, default=None)

    p_apply = sub.add_parser("apply", help="Apply LLM JSON output to render minutes markdown.")
    p_apply.add_argument("llm_json", type=str, help="Path to llm_output.json")
    p_apply.add_argument("--transcript", type=str, required=True, help="Path to transcript_clean.json used for context.")
    p_apply.add_argument("--config", type=str, default=None)

    p_check = sub.add_parser("check", help="Run quality check on minutes JSON (ToDo empty rate, due format, section warnings).")
    p_check.add_argument("input", type=str, help="Path to llm_output.json or minutes JSON.")
    p_check.add_argument("--config", type=str, default=None)

    p_eval = sub.add_parser("eval", help="Run evaluation/regression (stub for now).")
    p_eval.add_argument("--config", type=str, default=None)

    args = parser.parse_args()

    # When --config is not given, use run_metadata.json in the input dir (written by pipeline run)
    metadata_dir: Path | None = None
    if args.config is None:
        if args.cmd in ("summarize", "request", "chunk", "check"):
            metadata_dir = Path(args.input).resolve().parent
        elif args.cmd == "merge":
            metadata_dir = Path(args.partials[0]).resolve().parent
        elif args.cmd == "apply":
            metadata_dir = Path(args.transcript).resolve().parent

    cfg_path = resolve_config(
        Path(args.config) if args.config else None,
        metadata_dir=metadata_dir,
    )
    if args.cmd == "run":
        run_pipeline(Path(args.input), cfg_path)
    elif args.cmd == "summarize":
        summarize_only(Path(args.input), cfg_path)
    elif args.cmd == "request":
        request_pack(Path(args.input), cfg_path, mode=args.mode)
    elif args.cmd == "chunk":
        run_chunk(Path(args.input), cfg_path)
    elif args.cmd == "merge":
        partial_paths = [Path(p) for p in args.partials]
        out_path = Path(args.output) if args.output else None
        run_merge(partial_paths, cfg_path, out_path=out_path)
    elif args.cmd == "apply":
        apply_llm_output(Path(args.llm_json), Path(args.transcript), cfg_path)
    elif args.cmd == "check":
        run_check(Path(args.input), cfg_path)
    elif args.cmd == "eval":
        eval_pipeline(cfg_path)

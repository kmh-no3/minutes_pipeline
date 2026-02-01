#!/usr/bin/env python3
"""端末スペックを取得し tests/output/specs_report.txt に書き出す。WSL 上で実行すること。"""
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "output" / "specs_report.txt"


def run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return str(e)


def main():
    lines = ["=== CPU (lscpu) ===", run(["lscpu"]), ""]
    lines += ["=== 論理コア数 (nproc) ===", run(["nproc"]), ""]
    lines += ["=== メモリ (free -h) ===", run(["free", "-h"]), ""]
    lines += ["=== GPU (nvidia-smi) ===", run(["nvidia-smi"]) if sys.platform != "win32" else "skip on Windows", ""]
    lines += ["=== Python / CUDA (faster-whisper) ==="]
    try:
        from faster_whisper import WhisperModel
        try:
            m = WhisperModel("tiny", device="cuda", compute_type="float16")
            lines.append("faster-whisper CUDA: OK (GPU 利用可能)")
            del m
        except Exception as e:
            lines.append(f"faster-whisper CUDA: {type(e).__name__} - {str(e)[:200]}")
        try:
            m = WhisperModel("tiny", device="cpu", compute_type="int8")
            lines.append("faster-whisper CPU: OK")
            del m
        except Exception as e:
            lines.append(f"faster-whisper CPU: {type(e).__name__} - {str(e)[:200]}")
    except ImportError:
        lines.append("faster-whisper 未インストール")

    out_text = "\n".join(str(x) for x in lines)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out_text, encoding="utf-8")
    print(out_text)
    print(f"\nWritten: {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

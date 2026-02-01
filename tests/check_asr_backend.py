#!/usr/bin/env python3
"""ASR で使われているバックエンド（faster-whisper / openai-whisper）を確認する。"""
import sys

def main():
    lines = []
    try:
        from faster_whisper import WhisperModel  # noqa: F401
        lines.append("faster-whisper: OK (速い方)")
    except ImportError:
        lines.append("faster-whisper: 未インストール")

    try:
        import whisper  # noqa: F401
        lines.append("openai-whisper: OK")
    except ImportError:
        lines.append("openai-whisper: 未インストール")

    out = "\n".join(lines)
    print(out)
    # 結果をファイルにも書き、CI/自動実行で読めるようにする
    from pathlib import Path
    out_path = Path(__file__).parent / "output" / "asr_check_result.txt"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out)
    except Exception:
        pass
    return 0 if "faster-whisper: OK" in out else 1

if __name__ == "__main__":
    sys.exit(main())

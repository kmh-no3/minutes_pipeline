#!/usr/bin/env python3
"""
WAVEフォルダ内の全 .wav を ffmpeg で .mp4 に変換する（元の .wav は残す）。
使い方: python wav_to_mp4.py [基準ディレクトリ]
  省略時は tests/data/input を対象にする。
要: ffmpeg が PATH にあること（例: apt install ffmpeg / choco install ffmpeg）
"""

import os
import subprocess
import sys
from pathlib import Path


def find_wav_in_wave_dirs(base: Path):
    """基準ディレクトリ以下で、名前が WAVE のフォルダ直下にある .wav を列挙する。"""
    base = base.resolve()
    if not base.is_dir():
        return []
    wavs = []
    for root, dirs, _ in os.walk(base):
        root_path = Path(root)
        if root_path.name != "WAVE":
            continue
        for f in root_path.iterdir():
            if f.suffix.lower() == ".wav" and f.is_file():
                wavs.append(f)
    return sorted(wavs)


def main():
    script_dir = Path(__file__).resolve().parent
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "tests" / "data" / "input"
    base = base.resolve()

    # ログ用（実行結果をファイルにも残す）
    log_path = script_dir / "wav_to_mp4_log.txt"
    log_path.write_text("", encoding="utf-8")

    def log(msg: str):
        print(msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    if not base.is_dir():
        log(f"Error: Directory not found: {base}")
        sys.exit(1)

    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        log("Error: ffmpeg is required. Install with: sudo apt install ffmpeg (Linux) or choco install ffmpeg (Windows)")
        sys.exit(1)

    wavs = find_wav_in_wave_dirs(base)
    if not wavs:
        log(f"No .wav files found under */WAVE/ in {base}")
        return

    for wav in wavs:
        mp4 = wav.with_suffix(".mp4")
        log(f"Converting: {wav} -> {mp4}")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(wav),
                "-c:a", "aac", "-b:a", "192k",
                str(mp4),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )

    log(f"Done. Converted {len(wavs)} file(s). Original .wav files are unchanged.")


if __name__ == "__main__":
    main()

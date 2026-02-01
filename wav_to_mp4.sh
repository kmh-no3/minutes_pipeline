#!/usr/bin/env bash
# WAVEフォルダ内の全.wavファイルを.mp4形式に変換する（元の.wavは残す）
# 要: ffmpeg

set -euo pipefail

# スクリプトのあるディレクトリを基準に tests/data/input 以下の WAVE を探す
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${1:-$SCRIPT_DIR/tests/data/input}"

if [[ ! -d "$BASE_DIR" ]]; then
  echo "Error: Directory not found: $BASE_DIR"
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "Error: ffmpeg is required. Install with: sudo apt install ffmpeg"
  exit 1
fi

count=0
# */WAVE/*.wav かつ WAVE の直下のみ（サブフォルダは除く）
while IFS= read -r -d '' wav; do
  dir="$(dirname "$wav")"
  base="$(basename "$wav" .wav)"
  mp4="${dir}/${base}.mp4"
  echo "Converting: $wav -> $mp4"
  ffmpeg -y -i "$wav" -c:a aac -b:a 192k "$mp4" -nostdin -loglevel warning
  ((count++)) || true
done < <(find "$BASE_DIR" -type f -name "*.wav" -path "*/WAVE/*" ! -path "*/WAVE/*/*" -print0)

echo "Done. Converted $count file(s). Original .wav files are unchanged."

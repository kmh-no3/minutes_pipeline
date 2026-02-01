#!/bin/bash
# 端末スペック調査（WSL 上で実行）
OUT="/home/user/projects/minutes-pipeline/tests/output/specs_report.txt"
cd /home/user/projects/minutes-pipeline || exit 1
{
  echo "=== CPU ==="
  lscpu 2>/dev/null || echo "lscpu not available"
  echo ""
  echo "=== 論理コア数 ==="
  nproc 2>/dev/null
  echo ""
  echo "=== メモリ ==="
  free -h 2>/dev/null
  echo ""
  echo "=== GPU (nvidia-smi) ==="
  nvidia-smi 2>/dev/null || echo "nvidia-smi not found or no NVIDIA GPU"
  echo ""
  echo "=== Python / faster-whisper CUDA ==="
  python3 -c "
import sys
print('Python:', sys.executable)
try:
    from faster_whisper import WhisperModel
    m = WhisperModel('tiny', device='cuda', compute_type='float16')
    print('faster-whisper CUDA: OK (GPU 利用可能)')
    del m
except Exception as e:
    print('faster-whisper CUDA:', type(e).__name__, str(e)[:120])
try:
    from faster_whisper import WhisperModel
    m = WhisperModel('tiny', device='cpu', compute_type='int8')
    print('faster-whisper CPU: OK')
    del m
except Exception as e:
    print('faster-whisper CPU:', type(e).__name__, str(e)[:120])
" 2>/dev/null
} > "$OUT" 2>&1
echo "written $OUT"
cat "$OUT"

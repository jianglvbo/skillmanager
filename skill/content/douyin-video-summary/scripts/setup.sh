#!/bin/bash
# Setup script for douyin-video-summary skill dependencies
# Installs: whisper-cpp, ffmpeg, whisper model (ggml-small.bin)
# Usage: bash setup.sh [--skip-model] [--model-size small|medium|large]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL_DIR="${SCRIPT_DIR}/models"
MODEL_SIZE="${1:-small}"
SKIP_MODEL=false

# Parse arguments
for arg in "$@"; do
  case "$arg" in
    --skip-model) SKIP_MODEL=true ;;
    --model-size=*) MODEL_SIZE="${arg#*=}" ;;
  esac
done

echo "=== douyin-video-summary: dependency setup ==="
echo ""

# 1. Check / install whisper-cpp
if command -v whisper-cli &>/dev/null; then
  echo "[OK] whisper-cli: $(whisper-cli --version 2>&1 | head -1)"
else
  echo "[..] Installing whisper-cpp via Homebrew..."
  if command -v brew &>/dev/null; then
    brew install whisper-cpp
    echo "[OK] whisper-cli installed"
  else
    echo "[!!] Homebrew not found. Install from https://brew.sh first."
    exit 1
  fi
fi

# 2. Check / install ffmpeg
if command -v ffmpeg &>/dev/null; then
  echo "[OK] ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
else
  echo "[..] Installing ffmpeg via Homebrew..."
  if command -v brew &>/dev/null; then
    brew install ffmpeg
    echo "[OK] ffmpeg installed"
  else
    echo "[!!] Homebrew not found. Install from https://brew.sh first."
    exit 1
  fi
fi

# 3. Download whisper model
MODEL_FILE="${MODEL_DIR}/ggml-${MODEL_SIZE}.bin"
if [ -f "$MODEL_FILE" ]; then
  SIZE_MB=$(du -sh "$MODEL_FILE" | cut -f1)
  echo "[OK] Model: $(basename $MODEL_FILE) ($SIZE_MB)"
elif [ "$SKIP_MODEL" = true ]; then
  echo "[--] Skipping model download (--skip-model)"
else
  echo "[..] Downloading whisper model: ggml-${MODEL_SIZE}.bin"
  mkdir -p "$MODEL_DIR"
  
  MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-${MODEL_SIZE}.bin"
  
  # Prefer Chinese mirror, fallback to direct HuggingFace
  MIRROR_URL="https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-${MODEL_SIZE}.bin"
  DIRECT_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-${MODEL_SIZE}.bin"
  
  echo "     Trying hf-mirror.com first..."
  if ! curl -L --progress-bar --connect-timeout 15 --max-time 600 -o "$MODEL_FILE" "$MIRROR_URL" 2>/dev/null; then
    echo "     Mirror failed, trying huggingface.co..."
    curl -L --progress-bar --connect-timeout 30 --max-time 600 -o "$MODEL_FILE" "$DIRECT_URL"
  fi
  
  if [ -f "$MODEL_FILE" ] && [ "$(stat -f%z "$MODEL_FILE" 2>/dev/null || stat -c%s "$MODEL_FILE" 2>/dev/null)" -gt 1000000 ]; then
    SIZE_MB=$(du -sh "$MODEL_FILE" | cut -f1)
    echo "[OK] Model downloaded: $(basename $MODEL_FILE) ($SIZE_MB)"
  else
    echo "[!!] Model download failed or file too small"
    rm -f "$MODEL_FILE"
    exit 1
  fi
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Model sizes reference:"
echo "  tiny   (~75MB)  - fastest, lowest accuracy"
echo "  small  (~460MB) - recommended balance"
echo "  medium (~1.5GB) - better accuracy, may OOM on 8GB"
echo "  large  (~2.9GB) - best accuracy, needs 16GB+ RAM"

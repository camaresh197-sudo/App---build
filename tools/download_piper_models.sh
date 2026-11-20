#!/bin/bash
# Download Piper TTS models for local use
# Run this on your machine (not in cloud)

set -e

MODEL_DIR="${1:-.}"
MODELS=(
    "en_US-male-medium"
    "en_US-female-medium"
    "en_US-male-low"
    "en_US-female-low"
)

echo "Downloading Piper models to: $MODEL_DIR"
mkdir -p "$MODEL_DIR"

for model in "${MODELS[@]}"; do
    echo "Downloading $model..."

    # Download ONNX model
    curl -L -o "$MODEL_DIR/${model}.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/${model##*-}/${model##*-}/en_US-${model##*-}.onnx" \
        --progress-bar

    # Download config JSON
    curl -L -o "$MODEL_DIR/${model}.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/${model##*-}/${model##*-}/en_US-${model##*-}.json" \
        --progress-bar

    echo "✓ Downloaded $model"
done

echo ""
echo "Done! Models are in: $MODEL_DIR"
echo "Next: commit these to your repo or use them locally with Piper"

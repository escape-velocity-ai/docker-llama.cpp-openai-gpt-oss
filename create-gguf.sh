#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Read environment variables, providing default values where appropriate.
HF_MODEL_ID=${HF_MODEL_ID:?ERROR: HF_MODEL_ID environment variable is not set.}
GCP_STORAGE_BUCKET=${GCP_STORAGE_BUCKET:?ERROR: GCP_STORAGE_BUCKET environment variable is not set.}
QUANTIZATION=${QUANTIZATION:-f16}
MODEL_PATH=${MODEL_PATH:-/model-store}
DOWNLOAD_PATH="/model-store/hf-model"
GGUF_MODEL_NAME="$(echo "$HF_MODEL_ID" | cut -d'/' -f2).${QUANTIZATION}.gguf"
GGUF_FILEPATH="${MODEL_PATH}/${GGUF_MODEL_NAME}"

# Ensure the model path exists
mkdir -p ${MODEL_PATH}
mkdir -p ${DOWNLOAD_PATH}

# --- Step 1: Download the model from Hugging Face ---
echo "Downloading model ${HF_MODEL_ID} from Hugging Face..."
huggingface-cli download ${HF_MODEL_ID} --local-dir ${DOWNLOAD_PATH} --local-dir-use-symlinks False

# --- Step 2: Build llama.cpp ---
echo "Building llama.cpp..."
apt-get update
apt-get install -y pciutils build-essential cmake curl libcurl4-openssl-dev
git clone https://github.com/ggml-org/llama.cpp
cmake llama.cpp -B llama.cpp/build \
    -DBUILD_SHARED_LIBS=OFF -DGGML_CUDA=ON -DLLAMA_CURL=ON
cmake --build llama.cpp/build --config Release -j --clean-first --target llama-cli llama-mtmd-cli llama-server llama-gguf-split
cp llama.cpp/build/bin/llama-* llama.cpp

# --- Step 3: Convert the model to GGUF ---
echo "Converting the model to GGUF format..."
python llama.cpp/convert_hf_to_gguf.py ${DOWNLOAD_PATH} \
    --outfile "${GGUF_FILEPATH}" --outtype ${QUANTIZATION} \
    --split-max-size 50G

# --- Step 4: Upload the GGUF model to GCP ---
echo "Uploading the GGUF model to GCP..."
export MODEL_PATH=${MODEL_PATH}
export GGUF_MODEL_PATH=${GGUF_FILEPATH}
python scripts/setup.py

echo "Setup complete. Model ${GGUF_MODEL_NAME} is uploaded to gs://${GCP_STORAGE_BUCKET}."

#!/bin/bash
set -e

# 1. Validate that MODEL_PATH is a mounted directory
if [ -z "$MODEL_PATH" ] || [ ! -d "$MODEL_PATH" ]; then
  echo "Error: The environment variable MODEL_PATH is not set or the directory does not exist." >&2
  echo "Please mount a host directory to your desired model path and set MODEL_PATH." >&2
  echo "Example: docker run -v /path/on/host:/model-store -e MODEL_PATH=/model-store ..." >&2
  exit 1
fi

if [ -z "$GGUF_MODEL_PATH" ]; then
    echo "Error: GGUF_MODEL_PATH environment variable is not set." >&2
    exit 1
fi

if [ -z "$API_KEY" ]; then
    echo "Error: API_KEY environment variable is not set." >&2
    exit 1
fi

FULL_MODEL_PATH="$MODEL_PATH/$GGUF_MODEL_PATH"

if [ ! -f "$FULL_MODEL_PATH" ]; then
    echo "Error: Model file not found at $FULL_MODEL_PATH" >&2
    exit 1
fi

LLAMA_SERVER_PATH="/app/llama.cpp/build/bin/llama-server"
CERT_PATH="/app/certs"
KEY_PATH="$CERT_PATH/key.pem"
CERT_BUNDLE="$CERT_PATH/cert-bundle.pem"


echo "Starting llama.cpp server with model: $FULL_MODEL_PATH"

exec "$LLAMA_SERVER_PATH" \
    -m "$FULL_MODEL_PATH" \
    -ctx-size 32768 \
    -jinja \
    -ub 4096 -b 4096 \
    --chat-template-file "models/templates/openai-gpt-oss-120b.jinja" \
    --no-webui \
    --host "0.0.0.0" \
    --port "443" \
    --ssl-cert-file "$CERT_BUNDLE" \
    --ssl-key-file "$KEY_PATH" \
    --api-key "$API_KEY"

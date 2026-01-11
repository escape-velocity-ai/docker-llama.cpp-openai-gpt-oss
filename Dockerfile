
# Base Image: Debian 12 (Slim)
FROM debian:12-slim

# Set non-interactive frontend for package installations
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install System Dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    git \
    ca-certificates \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    python3-venv \
    bash && \
    rm -rf /var/lib/apt/lists/*

    
# 4. Copy application scripts
WORKDIR /app
COPY scripts/setup_and_run.py /app/scripts/setup_and_run.py
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
COPY llama.cpp/ /app/llama.cpp

# 5. Configure Runtime Environment
# Default model to download. Can be overridden at runtime via `docker run -e HF_MODEL_ID=...`
ENV HF_MODEL_ID="unsloth/mistral-7b-v0.1-bnb-4bit"
# Path to store the converted GGUF model and venv. MUST be a mounted volume.
ENV MODEL_PATH="/model-store"
# Quantization type for GGUF conversion. Default is f16.
ENV QUANTIZATION="f16"

# Expose the port for the llama.cpp server
EXPOSE 8080

# 6. Set the Entrypoint to the new run script
ENTRYPOINT ["/app/run.sh"]

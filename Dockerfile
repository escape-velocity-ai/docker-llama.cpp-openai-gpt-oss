
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

# 2. Install NVIDIA CUDA Toolkit 12.5
# As per https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Debian&target_version=12&target_type=deb_network
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    rm cuda-keyring_1.1-1_all.deb && \
    apt-get update && \
    apt-get -y install cuda-toolkit-12-5

# Set CUDA environment variables
ENV PATH="/usr/local/cuda-12.5/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda-12.5/lib64:${LD_LIBRARY_PATH}"

# 3. Clone and Build llama.cpp with CUDA support (non-native)
WORKDIR /app
RUN git clone https://github.com/ggml-org/llama.cpp.git
WORKDIR /app/llama.cpp
# Create and enter build directory
RUN mkdir build && cd build && \
    # Configure cmake to build with CUDA support and for portability (non-native)
    cmake .. -DLLAMA_CUBLAS=ON -DGGML_NATIVE=OFF && \
    # Build the project
    cmake --build . --config Release

# 4. Copy application scripts
WORKDIR /app
COPY scripts/setup_and_run.py /app/scripts/setup_and_run.py
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh

# 5. Configure Runtime Environment
# Default model to download. Can be overridden at runtime via `docker run -e HF_MODEL_ID=...`
ENV HF_MODEL_ID="unsloth/mistral-7b-v0.1-bnb-4bit"
# Path to store the converted GGUF model and venv. MUST be a mounted volume.
ENV MODEL_PATH="/model-store"
# Quantization type for GGUF conversion. Default is q4_k_m.
ENV QUANTIZATION="q4_k_m"

# Expose the port for the llama.cpp server
EXPOSE 8080

# 6. Set the Entrypoint to the new run script
ENTRYPOINT ["/app/run.sh"]

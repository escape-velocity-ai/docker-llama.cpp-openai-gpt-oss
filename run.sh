
#!/bin/bash
set -e

# 1. Validate that MODEL_PATH is a mounted directory
if [ -z "$MODEL_PATH" ] || [ ! -d "$MODEL_PATH" ]; then
  echo "Error: The environment variable MODEL_PATH is not set or the directory does not exist." >&2
  echo "Please mount a host directory to your desired model path and set MODEL_PATH." >&2
  echo "Example: docker run -v /path/on/host:/model-store -e MODEL_PATH=/model-store ..." >&2
  exit 1
fi

# 2. Define and create the virtual environment inside the mounted volume
VENV_PATH="$MODEL_PATH/venv"

if [ ! -d "$VENV_PATH" ]; then
  echo "Creating Python virtual environment in $VENV_PATH..."
  python3 -m venv "$VENV_PATH"
fi

# 3. Activate venv and install/verify Python dependencies
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

echo "Installing/verifying Python dependencies..."
pip install --no-cache-dir \
    "unsloth[cu121-strict] @ git+https://github.com/unslothai/unsloth.git" \
    huggingface_hub \
    transformers \
    torch

echo "Install NVidia CUDA toolkit"
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb
RUN dpkg -i cuda-keyring_1.1-1_all.deb
RUN apt-get update
RUN apt-get -y install cuda-toolkit-13-1

# 4. Execute the main Python script
echo "Starting model setup and server execution..."
python /app/scripts/setup_and_run.py

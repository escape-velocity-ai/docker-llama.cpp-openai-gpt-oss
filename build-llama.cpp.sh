#!/bin/bash

sudo apt-get install cmake wget

## Build this seperately as it can take some time
# 2. Install NVIDIA CUDA Toolkit 12.5
# As per https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=Debian&target_version=12&target_type=deb_network
if [ ! -f "cuda-keyring_1.1-1_all.deb" ]; then
  wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb
  sudo dpkg -i cuda-keyring_1.1-1_all.deb
  sudo apt-get update
  sudo apt-get -y install cuda-toolkit-13-1
fi
# Apparently we need the libcurl libs
sudo apt-get install libcurl4-openssl-dev

# Set CUDA environment variables
export PATH="/usr/local/cuda-12.5/bin:${PATH}"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/local/cuda/lib64/stubs:${LD_LIBRARY_PATH}"
sudo ln -s /usr/local/cuda/lib64/stubs/libcuda.so /usr/local/cuda/lib64/stubs/libcuda.so.1

# 3. Clone and Build llama.cpp with CUDA support (non-native)
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

# Configure cmake to build with CUDA support and specific architecture (below is for an L4 GPU)
# For arch details see llama.cpp/ggml/src/ggml-cuda/CMakeLists.txt
cmake -B build -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="89" && \
    # Build the project
    cmake --build build --config Release
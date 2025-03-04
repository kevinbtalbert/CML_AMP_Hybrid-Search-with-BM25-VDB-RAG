#!/bin/bash

# Copyright 2025 Cloudera Government Solutions, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Function to get the CUDA version from nvidia-smi
get_cuda_version() {
    if ! command -v nvidia-smi &> /dev/null; then
        echo "Error: nvidia-smi not found. Make sure NVIDIA drivers are installed."
        return 1
    fi

    # Get CUDA version from nvidia-smi output
    cuda_version=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9]+\.[0-9]+')
    if [ -z "$cuda_version" ]; then
        echo "Error: Could not determine CUDA version from nvidia-smi output."
        return 1
    fi

    echo "$cuda_version"
    return 0
}

# Function to install PyTorch based on CUDA version
install_pytorch() {
    local cuda_version=$1

    # Map CUDA versions to PyTorch index URLs
    case "$cuda_version" in
        12.4) pip_url="https://download.pytorch.org/whl/cu124" ;;
        12.3) pip_url="https://download.pytorch.org/whl/cu123" ;;
        11.8) pip_url="https://download.pytorch.org/whl/cu118" ;;
        11.7) pip_url="https://download.pytorch.org/whl/cu117" ;;
        10.2) pip_url="https://download.pytorch.org/whl/cu102" ;;
        *)
            echo "Warning: CUDA version $cuda_version is not explicitly supported. Installing PyTorch for CPU."
            pip install "networkx<3.3" torch torchvision torchaudio
            return 0
            ;;
    esac

    # Install PyTorch with the correct URL
    echo "Detected CUDA version: $cuda_version"
    echo "Installing PyTorch with GPU support from $pip_url..."
    pip install "networkx<3.3" torch torchvision torchaudio --index-url "$pip_url"
}

# Main script logic
main() {
    cuda_version=$(get_cuda_version)
    if [ $? -ne 0 ]; then
        echo "Falling back to CPU-only PyTorch installation."
        pip install torch torchvision torchaudio
        exit 1
    fi

    install_pytorch "$cuda_version"
}

# Run the script
main
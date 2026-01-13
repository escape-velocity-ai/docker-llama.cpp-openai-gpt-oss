#!/bin/bash

# This script builds a Docker image from the current directory, tags it,
# and pushes it to a specified Google Cloud Artifact Registry.
#
# Prerequisites:
# 1. Docker is installed and running.
# 2. Google Cloud SDK (gcloud) is installed.
# 3. You have authenticated with gcloud (`gcloud auth login`).
# 4. You have set your project (`gcloud config set project YOUR_PROJECT_ID`).
# 5. The Artifact Registry API is enabled for your project.
# 6. A Dockerfile exists in the current directory.

# Exit immediately if a command exits with a non-zero status.
set -e

# Build llama.cpp locally - cross compiled - and copy into the docker image
./build-llama.cpp.sh

# --- Configuration ---
# The region of your Artifact Registry.
REGION="europe-west4"

# The name of your Artifact Registry repository.
REGISTRY="llama-cpp"

# The name of the image you are building.
# TODO: Change 'my-app' to your desired image name.
IMAGE_NAME="docker-llama.cpp-openai-gpt-oss"

# The tag for your image. 'latest' is a common default.
TAG="v0.01.02"
# --- End of Configuration ---

# 1. Get the Google Cloud Project ID from the gcloud config.
echo "--> Fetching Google Cloud Project ID..."
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "Error: Google Cloud Project ID not found. Please run 'gcloud config set project YOUR_PROJECT_ID'."
    exit 1
fi
echo "    Project ID: ${PROJECT_ID}"

# 2. Construct the full image path for Artifact Registry.
IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY}/${IMAGE_NAME}:${TAG}"
echo "--> Full image path will be: ${IMAGE_PATH}"

# 3. Authenticate Docker with Google Cloud Artifact Registry.
# This configures the Docker client to use gcloud as a credential helper for the specified registry.
echo "--> Configuring Docker authentication for ${REGION}-docker.pkg.dev..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
echo "    Docker authentication configured."

# 4. Build the Docker image.
# The Dockerfile is assumed to be in the current directory ('.').
# The '-t' flag tags the image with the full path required by Artifact Registry.
echo "--> Building Docker image..."
docker build -t "${IMAGE_PATH}" .
echo "    Image built successfully."

# 5. Push the Docker image to Artifact Registry.
echo "--> Pushing image to Artifact Registry..."
docker push "${IMAGE_PATH}"
echo "    Image pushed successfully to ${IMAGE_PATH}"

echo ""
echo "---"
echo "Build and push complete!"
echo "---"

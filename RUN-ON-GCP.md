# Running on GCP Cloud Run

*** Note, this is still experimental ***

This document provides a step-by-step guide to deploying the service on Google Cloud Run.

## 1. Create a Google Cloud Storage Bucket

First, you need a Google Cloud Storage bucket to store your converted model files.

1.  **Authenticate with GCP:** Make sure you have the `gcloud` CLI installed and authenticated. You can authenticate by running:
    ```bash
    gcloud auth login
    ```

2.  **Create a Bucket:** Follow the official Google Cloud documentation to create a new storage bucket.
    - **Reference:** [Creating a Cloud Storage Bucket](https://docs.cloud.google.com/storage/docs/creating-buckets#console)
    - **Important:** Make a note of the **name** and **region** of your bucket, as you will need them later. Ensure the region you choose has L4 GPUs available.

## 2. Convert and Upload Your Model

The `scripts/setup.py` script is used to download a model from Hugging Face, convert it to the GGUF format, and upload it to your Google Cloud Storage bucket.

1.  **Install Dependencies:**
    ```bash
    cd scripts
    pip install -r scripts/requirements.txt
    ```

2.  **Run the Setup Script:**
    - Set the `HF_MODEL_ID` environment variable to the Hugging Face model you want to use.
    - Set the `GCP_STORAGE_BUCKET` environment variable to the name of the bucket you created in the previous step.
    - Set `MODEL_PATH` to a local directory where you want to store the model temporarily.

    ```bash
    export HF_MODEL_ID="unsloth/mistral-7b-v0.1-bnb-4bit"
    export GCP_STORAGE_BUCKET="your-gcs-bucket-name"
    export MODEL_PATH="/path/to/local/model-store"
    python scripts/setup.py
    ```
    The script will output the name of the converted GGUF file. Make a note of this filename (e.g., `mistral-7b-v0.1-bnb-4bit.f16.gguf`).

## 3. Create a GCP Artifact Registry

You need a GCP Artifact Registry to store your Docker container.

1.  **Create a Docker Repository:** Use the `gcloud` command to create a new Docker repository.
    ```bash
    gcloud artifacts repositories create llama-cpp \
        --repository-format=docker \
        --location=<your-region> \
        --description="Docker repository for llama.cpp"
    ```
    - **Important:** Replace `<your-region>` with the same region you used for your GCS bucket.

## 4. Build and Push the Docker Container

The `build.sh` script builds the Docker container and pushes it to your Artifact Registry.

1.  **Run the Build Script:**
    ```bash
    ./build.sh
    ```
    The script will automatically detect your GCP project ID and region (as configured in `build.sh`) and push the container to the correct repository.

## 5. Deploy on GCP Cloud Run

Now you can deploy your service on GCP Cloud Run.

1.  **Open the Cloud Run Console:** Navigate to the [Google Cloud Run console](https://console.cloud.google.com/run).

2.  **Create a New Service:**
    - Select **"Deploy one revision from an existing container image"**.
    - For the **"Container image URL"**, select the image you pushed to the Artifact Registry.
    - Choose a **"Service name"**.
    - Select the same **region** as your GCS bucket and Artifact Registry.
    - Under **"Authentication"**, choose **"Allow unauthenticated invocations"** for public access.

3.  **Configure Container, Connections, Security:**
    - **Container port:** Set to `443`.
    - **Generate an API Key:**
      ```bash
      python scripts/generate_uuid.py
      ```
      Copy the generated UUID.
    - **Environment Variables:**
      - `API_KEY`: Paste the UUID you generated.
      - `GGUF_MODEL_PATH`: Enter the filename of the converted model (e.g., `mistral-7b-v0.1-bnb-4bit.f16.gguf`).
    - **Volumes:**
      - Click **"Add Volume"**.
      - Select **"Cloud Storage"**.
      - Choose the GCS bucket you created.
      - Set the **"Mount path"** to `/model-store`.
    - **CPU and Memory:**
      - **CPUs:** 8
      - **Memory:** 32GB
    - **GPU:**
      - Select **"NVIDIA L4"**.
    - **Healthcheck:**
      - **Path:** `/v1/health`
      - **Port:** `443`

4.  **Deploy:** Click **"Create"** to deploy your service.

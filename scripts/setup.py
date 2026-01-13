
import os
import sys
import shutil
from pathlib import Path
from google.cloud import storage

# --- Configuration ---
# Read environment variables
HF_MODEL_ID = os.getenv("HF_MODEL_ID")
MODEL_PATH = os.getenv("MODEL_PATH", "/model-store")
QUANTIZATION = os.getenv("QUANTIZATION", "f16")
GCP_STORAGE_BUCKET = os.getenv("GCP_STORAGE_BUCKET")


def main():
    """
    Main function to orchestrate model download, conversion, and upload to GCS.
    """
    if not HF_MODEL_ID:
        print("ERROR: HF_MODEL_ID environment variable is not set.", file=sys.stderr)
        print("Please set it to the Hugging Face model you want to use (e.g., 'unsloth/mistral-7b-v0.1-bnb-4bit').", file=sys.stderr)
        sys.exit(1)

    if not GCP_STORAGE_BUCKET:
        print("ERROR: GCP_STORAGE_BUCKET environment variable is not set.", file=sys.stderr)
        print("Please set it to the name of your Google Cloud Storage bucket.", file=sys.stderr)
        sys.exit(1)

    # Sanitize model name for use in filename
    model_name = HF_MODEL_ID.split("/")[-1]
    gguf_filename = f"{model_name}.{QUANTIZATION}.gguf"
    gguf_filepath = Path(MODEL_PATH) / gguf_filename

    # --- Step 1: Check if GGUF model exists locally ---
    if gguf_filepath.is_file():
        print(f"GGUF model already exists locally at: {gguf_filepath}", file=sys.stderr)
    else:
        print(f"GGUF model not found locally. Starting download and conversion for '{HF_MODEL_ID}'.", file=sys.stderr)
        convert_model_to_gguf(gguf_filepath)

    # --- Step 2: Upload the GGUF model to GCS ---
    print(f"Uploading {gguf_filename} to GCS bucket '{GCP_STORAGE_BUCKET}'...", file=sys.stderr)
    upload_to_gcs(gguf_filepath, gguf_filename)

    # --- Step 3: Print the relative path of the model to stdout ---
    print(gguf_filename)


def convert_model_to_gguf(target_gguf_path: Path):
    """
    Downloads a model from Hugging Face and converts it to GGUF format using Unsloth.
    """
    try:
        from unsloth import FastLanguageModel
        import torch

        print("Loading model from Hugging Face...", file=sys.stderr)
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=HF_MODEL_ID,
            max_seq_length=4096,
            dtype=None,
            load_in_4bit=True,
        )

        print(f"Model '{HF_MODEL_ID}' loaded successfully.", file=sys.stderr)

        temp_save_dir = Path("/tmp/gguf_conversion")
        temp_save_dir.mkdir(exist_ok=True)

        print(f"Saving model to GGUF with quantization: {QUANTIZATION}...", file=sys.stderr)
        model.save_pretrained_gguf(
            save_directory=str(temp_save_dir),
            tokenizer=tokenizer,
            quantization_method=QUANTIZATION
        )

        saved_files = list(temp_save_dir.glob("*.bin"))
        if not saved_files:
            raise FileNotFoundError("GGUF conversion did not produce a .bin file.")

        source_gguf_file = saved_files[0]
        print(f"Moving converted file from {source_gguf_file} to {target_gguf_path}", file=sys.stderr)
        shutil.move(source_gguf_file, target_gguf_path)

        shutil.rmtree(temp_save_dir)

        print("GGUF conversion complete.", file=sys.stderr)

    except Exception as e:
        print(f"An error occurred during model conversion: {e}", file=sys.stderr)
        sys.exit(1)


def upload_to_gcs(source_file_path: Path, destination_blob_name: str):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCP_STORAGE_BUCKET)
        blob = bucket.blob(destination_blob_name)

        print(f"Uploading file {source_file_path} to gs://{GCP_STORAGE_BUCKET}/{destination_blob_name}", file=sys.stderr)
        blob.upload_from_filename(str(source_file_path))
        print("File uploaded successfully.", file=sys.stderr)

    except Exception as e:
        print(f"An error occurred during GCS upload: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

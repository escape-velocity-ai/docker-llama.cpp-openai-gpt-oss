
import os
import sys
import subprocess
import shutil
from pathlib import Path

# --- Configuration ---
# Read environment variables
HF_MODEL_ID = os.getenv("HF_MODEL_ID")
MODEL_PATH = os.getenv("MODEL_PATH", "/model-store")
QUANTIZATION = os.getenv("QUANTIZATION", "q4_k_m")
LLAMA_CPP_PATH = "/app/llama.cpp"
LLAMA_SERVER_PATH = os.path.join(LLAMA_CPP_PATH, "build", "bin", "server")

def main():
    """
    Main function to orchestrate model download, conversion, and server launch.
    """
    if not HF_MODEL_ID:
        print("ERROR: HF_MODEL_ID environment variable is not set.", file=sys.stderr)
        print("Please set it to the Hugging Face model you want to use (e.g., 'unsloth/mistral-7b-v0.1-bnb-4bit').", file=sys.stderr)
        sys.exit(1)

    # Sanitize model name for use in filename
    model_name = HF_MODEL_ID.split("/")[-1]
    gguf_filename = f"{model_name}.{QUANTIZATION}.gguf"
    gguf_filepath = Path(MODEL_PATH) / gguf_filename

    # --- Step 1: Check if GGUF model exists ---
    if gguf_filepath.is_file():
        print(f"GGUF model already exists at: {gguf_filepath}")
    else:
        print(f"GGUF model not found. Starting download and conversion for '{HF_MODEL_ID}'.")
        convert_model_to_gguf(gguf_filepath)

    # --- Step 2: Run the llama.cpp server ---
    run_llama_server(gguf_filepath)


def convert_model_to_gguf(target_gguf_path: Path):
    """
    Downloads a model from Hugging Face and converts it to GGUF format using Unsloth.
    """
    try:
        from unsloth import FastLanguageModel
        import torch

        print("Loading model from Hugging Face...")
        # Load model using Unsloth. `load_in_4bit` is recommended for memory efficiency during conversion.
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=HF_MODEL_ID,
            max_seq_length=4096, # Match context size for server
            dtype=None,
            load_in_4bit=True,
        )
        
        print(f"Model '{HF_MODEL_ID}' loaded successfully.")
        
        temp_save_dir = Path("/tmp/gguf_conversion")
        temp_save_dir.mkdir(exist_ok=True)

        print(f"Saving model to GGUF with quantization: {QUANTIZATION}...")
        # Unsloth saves the file with a standard name inside the specified directory
        model.save_pretrained_gguf(
            save_directory=str(temp_save_dir),
            tokenizer=tokenizer,
            quantization_method=QUANTIZATION
        )
        
        # The saved file is typically named `gguf-model-{quantization}.bin`
        # Let's find it and move it.
        saved_files = list(temp_save_dir.glob("*.bin"))
        if not saved_files:
            raise FileNotFoundError("GGUF conversion did not produce a .bin file.")
            
        source_gguf_file = saved_files[0]
        print(f"Moving converted file from {source_gguf_file} to {target_gguf_path}")
        shutil.move(source_gguf_file, target_gguf_path)
        
        # Clean up temporary directory
        shutil.rmtree(temp_save_dir)
        
        print("GGUF conversion complete.")

    except Exception as e:
        print(f"An error occurred during model conversion: {e}", file=sys.stderr)
        sys.exit(1)


def run_llama_server(model_path: Path):
    """
    Starts the llama.cpp server with the specified GGUF model.
    """
    print(f"\nStarting llama.cpp server with model: {model_path}")
    print("Server will be available at http://0.0.0.0:8080")
    
    # Command arguments based on user request for NVIDIA with 16GB VRAM
    # -ngl 99: Offload all possible layers to GPU
    # -c 4096: Set context size
    command = [
        LLAMA_SERVER_PATH,
        "-m", str(model_path),
        "-c", "4096",
        "--host", "0.0.0.0",
        "--port", "8080",
        "-ngl", "99" # Offload all layers to GPU
    ]

    print(f"Executing command: {' '.join(command)}")
    
    try:
        # Using subprocess.run to execute the server.
        # This will block and keep the container running.
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print(f"ERROR: Server executable not found at '{LLAMA_SERVER_PATH}'", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: The llama.cpp server exited with a non-zero status: {e.returncode}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()

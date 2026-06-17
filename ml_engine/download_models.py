import os
from huggingface_hub import hf_hub_download

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# List of highly optimized 1B-3B parameter quantized models for offline use.
MODELS_TO_DOWNLOAD = [
    # Sage
    {"repo_id": "bartowski/Llama-3.2-1B-Instruct-GGUF", "filename": "Llama-3.2-1B-Instruct-Q4_K_M.gguf"},
    # Analyst
    {"repo_id": "Qwen/Qwen2.5-1.5B-Instruct-GGUF", "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf"},
    # Strategist
    {"repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf", "filename": "Phi-3-mini-4k-instruct-q4.gguf"},
    # Skeptic
    {"repo_id": "bartowski/gemma-2-2b-it-GGUF", "filename": "gemma-2-2b-it-Q4_K_M.gguf"},
    # Judge
    {"repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF", "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"}
]

def download_all():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        
    print(f"Downloading {len(MODELS_TO_DOWNLOAD)} local models to {MODELS_DIR}...")
    print("This will take a significant amount of time and disk space (approx 8-10 GB).")
    
    for model in MODELS_TO_DOWNLOAD:
        print(f"Downloading {model['filename']}...")
        try:
            path = hf_hub_download(
                repo_id=model["repo_id"],
                filename=model["filename"],
                local_dir=MODELS_DIR,
                local_dir_use_symlinks=False
            )
            print(f"Successfully downloaded to: {path}")
        except Exception as e:
            print(f"Failed to download {model['filename']}: {e}")

if __name__ == "__main__":
    download_all()

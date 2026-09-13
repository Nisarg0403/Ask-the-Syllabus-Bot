import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Configurable paths with environment variables support
DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data" / "documents"))
STORAGE_DIR = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))
FAISS_DIR = os.getenv("FAISS_DIR", str(BASE_DIR / "storage" / "faiss"))
METADATA_FILE = os.getenv("METADATA_FILE", str(BASE_DIR / "storage" / "indexed_documents.json"))

# Model settings
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Ensure required runtime directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ==============================================================================
# APPLICATION & SERVER CONFIGURATION
# ==============================================================================
APP_NAME = os.getenv("APP_NAME", "Ask-the-Syllabus Bot API")
APP_VERSION = "2.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# ==============================================================================
# MODEL & EMBEDDING CONFIGURATION
# ==============================================================================
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "ollama").lower()
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "qwen3:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", None)
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.2"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

# ==============================================================================
# RAG RETRIEVAL & CHUNKING CONFIGURATION
# ==============================================================================
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "200"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "4"))
RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "ms-marco-TinyBERT-L-2-v2")
RERANKER_CANDIDATE_K = int(os.getenv("RERANKER_CANDIDATE_K", "16"))
EVIDENCE_THRESHOLD = float(os.getenv("EVIDENCE_THRESHOLD", "0.25"))

# ==============================================================================
# STORAGE & PERSISTENCE PATHS
# ==============================================================================
DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data" / "documents"))
STORAGE_DIR = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))
FAISS_DIR = os.getenv("FAISS_DIR", str(BASE_DIR / "storage" / "faiss"))
BM25_FILE = os.getenv("BM25_FILE", str(BASE_DIR / "storage" / "bm25_index.json"))
METADATA_FILE = os.getenv("METADATA_FILE", str(BASE_DIR / "storage" / "indexed_documents.json"))
MANIFEST_FILE = os.getenv("MANIFEST_FILE", str(BASE_DIR / "storage" / "index_manifest.json"))
REGISTRY_DB_FILE = os.getenv("REGISTRY_DB_FILE", str(BASE_DIR / "storage" / "registry.db"))
JOBS_FILE = os.getenv("JOBS_FILE", str(BASE_DIR / "storage" / "jobs.json"))

# ==============================================================================
# INGESTION & OBSERVABILITY CONFIGURATION
# ==============================================================================
BACKGROUND_INGESTION_ENABLED = os.getenv("BACKGROUND_INGESTION_ENABLED", "true").lower() in ("true", "1", "yes")
STRUCTURED_LOGGING_ENABLED = os.getenv("STRUCTURED_LOGGING_ENABLED", "true").lower() in ("true", "1", "yes")
REQUEST_ID_HEADER = os.getenv("REQUEST_ID_HEADER", "X-Request-ID")

# Ensure required storage directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)

# ==============================================================================
# CONFIGURATION VALIDATION
# ==============================================================================
def validate_config():
    """Validates configuration parameters at application startup."""
    errors = []

    if DEFAULT_CHUNK_SIZE <= 0:
        errors.append(f"DEFAULT_CHUNK_SIZE must be > 0, got {DEFAULT_CHUNK_SIZE}")
    if DEFAULT_CHUNK_OVERLAP < 0:
        errors.append(f"DEFAULT_CHUNK_OVERLAP must be >= 0, got {DEFAULT_CHUNK_OVERLAP}")
    if DEFAULT_CHUNK_OVERLAP >= DEFAULT_CHUNK_SIZE:
        errors.append(f"DEFAULT_CHUNK_OVERLAP ({DEFAULT_CHUNK_OVERLAP}) must be less than DEFAULT_CHUNK_SIZE ({DEFAULT_CHUNK_SIZE})")

    if DEFAULT_TOP_K < 1:
        errors.append(f"DEFAULT_TOP_K must be >= 1, got {DEFAULT_TOP_K}")

    if not (0.0 <= EVIDENCE_THRESHOLD <= 1.0):
        errors.append(f"EVIDENCE_THRESHOLD must be between 0.0 and 1.0, got {EVIDENCE_THRESHOLD}")

    if EMBEDDING_DIMENSION <= 0:
        errors.append(f"EMBEDDING_DIMENSION must be > 0, got {EMBEDDING_DIMENSION}")

    if DEFAULT_LLM_PROVIDER not in ("ollama", "openrouter"):
        errors.append(f"Invalid DEFAULT_LLM_PROVIDER '{DEFAULT_LLM_PROVIDER}'. Must be 'ollama' or 'openrouter'")

    valid_log_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    if LOG_LEVEL not in valid_log_levels:
        errors.append(f"Invalid LOG_LEVEL '{LOG_LEVEL}'. Must be one of {valid_log_levels}")

    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f" - {e}" for e in errors)
        raise ValueError(error_msg)

def get_safe_config() -> Dict[str, Any]:
    """Returns safe, non-secret configuration parameters for telemetry/status APIs."""
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "environment": ENVIRONMENT,
        "llm_provider": DEFAULT_LLM_PROVIDER,
        "llm_model": DEFAULT_LLM_MODEL,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "chunk_overlap": DEFAULT_CHUNK_OVERLAP,
        "top_k": DEFAULT_TOP_K,
        "reranker_model": RERANKER_MODEL_NAME,
        "evidence_threshold": EVIDENCE_THRESHOLD,
        "background_ingestion_enabled": BACKGROUND_INGESTION_ENABLED,
        "structured_logging_enabled": STRUCTURED_LOGGING_ENABLED
    }

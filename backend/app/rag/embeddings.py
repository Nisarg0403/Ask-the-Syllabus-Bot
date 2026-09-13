import torch
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import EMBEDDING_MODEL_NAME

def get_device() -> str:
    """Returns 'cuda' if GPU acceleration is available, otherwise 'cpu'."""
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def get_embeddings() -> HuggingFaceEmbeddings:
    """Initializes local Hugging Face Sentence Transformers embeddings."""
    device = get_device()
    model_kwargs = {"device": device}
    encode_kwargs = {"normalize_embeddings": True}
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

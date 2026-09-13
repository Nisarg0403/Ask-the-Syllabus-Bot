import os
import pickle
import re
from typing import List, Tuple, Optional
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document
from app.core.config import STORAGE_DIR

BM25_DIR = os.path.join(STORAGE_DIR, "bm25")
INDEX_PATH = os.path.join(BM25_DIR, "bm25_index.pkl")
CORPUS_PATH = os.path.join(BM25_DIR, "bm25_corpus.pkl")

def tokenize_text(text: str) -> List[str]:
    """Tokenize text into lowercased words/alphanumeric tokens for BM25."""
    return re.findall(r'\b\w+\b', text.lower())

class BM25Index:
    def __init__(self, corpus: Optional[List[Document]] = None):
        self.corpus: List[Document] = corpus or []
        self.tokenized_corpus = [tokenize_text(doc.page_content) for doc in self.corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus) if self.tokenized_corpus else None

    @property
    def documents(self) -> List[Document]:
        """Alias for corpus to support .documents attribute access."""
        return self.corpus

    def clear(self):
        """Clear all documents and reset the BM25 index."""
        self.corpus = []
        self.tokenized_corpus = []
        self.bm25 = None
        self.save()

    def add_documents(self, documents: List[Document]):
        """Add new document chunks to the BM25 index, rebuild the model, and save to disk."""
        if not documents:
            return
        self.corpus.extend(documents)
        self.tokenized_corpus = [tokenize_text(doc.page_content) for doc in self.corpus]
        self.bm25 = BM25Okapi(self.tokenized_corpus) if self.tokenized_corpus else None
        self.save()

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Document, float]]:
        """Search BM25 index and return top_k documents with scores."""
        if not self.bm25 or not self.corpus:
            return []
        
        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Sort indices by score descending
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self.corpus[idx], float(scores[idx])))
        return results

    def save(self):
        """Save BM25 index and corpus to disk."""
        os.makedirs(BM25_DIR, exist_ok=True)
        with open(INDEX_PATH, "wb") as f:
            pickle.dump(self.bm25, f)
        with open(CORPUS_PATH, "wb") as f:
            pickle.dump(self.corpus, f)

    @classmethod
    def load(cls) -> "BM25Index":
        """Load BM25 index from disk if available."""
        if os.path.exists(INDEX_PATH) and os.path.exists(CORPUS_PATH):
            try:
                with open(INDEX_PATH, "rb") as f:
                    bm25 = pickle.load(f)
                with open(CORPUS_PATH, "rb") as f:
                    corpus = pickle.load(f)
                instance = cls(corpus=corpus)
                instance.bm25 = bm25
                return instance
            except Exception as e:
                print(f"Error loading BM25 index: {e}")
        return cls(corpus=[])

def build_bm25_index(documents: List[Document]) -> BM25Index:
    """Build and save a new BM25 index from document chunks."""
    index = BM25Index(corpus=documents)
    index.save()
    return index

def get_bm25_index() -> BM25Index:
    """Load existing BM25 index."""
    return BM25Index.load()

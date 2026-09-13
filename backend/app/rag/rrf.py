from typing import List, Tuple, Dict
from langchain_core.documents import Document

def reciprocal_rank_fusion(
    dense_results: List[Tuple[Document, float]],
    bm25_results: List[Tuple[Document, float]],
    k: int = 60,
    top_n: int = 10
) -> List[Tuple[Document, float]]:
    """
    Combines dense FAISS results and sparse BM25 results using Reciprocal Rank Fusion (RRF).
    
    RRF Score = 1 / (k + rank_dense) + 1 / (k + rank_bm25)
    """
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    # Helper function to get unique key for a chunk
    def get_chunk_key(doc: Document) -> str:
        source = doc.metadata.get("source", "")
        page = doc.metadata.get("page", "")
        snippet = doc.page_content[:100]
        return f"{source}_p{page}_{hash(snippet)}"

    # Process Dense Ranks
    for rank, (doc, _) in enumerate(dense_results, start=1):
        key = get_chunk_key(doc)
        doc_map[key] = doc
        rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k + rank))

    # Process BM25 Ranks
    for rank, (doc, _) in enumerate(bm25_results, start=1):
        key = get_chunk_key(doc)
        doc_map[key] = doc
        rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k + rank))

    # Sort documents by RRF score descending
    sorted_keys = sorted(rrf_scores.keys(), key=lambda key: rrf_scores[key], reverse=True)

    fused_results = [(doc_map[key], rrf_scores[key]) for key in sorted_keys[:top_n]]
    return fused_results

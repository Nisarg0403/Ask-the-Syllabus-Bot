import os
from typing import List, Tuple, Dict, Any
from langchain_core.documents import Document

DEFAULT_EVIDENCE_THRESHOLD = float(os.getenv("EVIDENCE_THRESHOLD", "0.25"))

class Reranker:
    def __init__(self, model_name: str = "ms-marco-TinyBERT-L-2-v2"):
        self.ranker = None
        try:
            from flashrank import Ranker, RerankRequest
            self.ranker = Ranker(model_name=model_name)
            self.RerankRequest = RerankRequest
            print(f"FlashRank Reranker loaded successfully with model {model_name}")
        except Exception as e:
            print(f"Warning: FlashRank could not be initialized ({e}). Fallback reranking will be used.")

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[Document, float]],
        top_n: int = 5,
        threshold: Optional[float] = None
    ) -> Tuple[List[Tuple[Document, float]], bool]:
        """
        Reranks retrieved candidate chunks using Cross-Encoder / FlashRank.
        Returns:
            - List of (Document, score) tuples
            - boolean indicating whether evidence is sufficient (False = Abstain)
        """
        if not candidates:
            return [], False

        cutoff = threshold if threshold is not None else DEFAULT_EVIDENCE_THRESHOLD

        if self.ranker:
            try:
                passages = [
                    {
                        "id": idx,
                        "text": doc.page_content,
                        "meta": doc.metadata
                    }
                    for idx, (doc, _) in enumerate(candidates)
                ]

                rerank_request = self.RerankRequest(query=query, passages=passages)
                results = self.ranker.rerank(rerank_request)

                reranked_docs = []
                max_score = 0.0

                for item in results[:top_n]:
                    idx = item["id"]
                    score = float(item["score"])
                    max_score = max(max_score, score)
                    original_doc = candidates[idx][0]
                    reranked_docs.append((original_doc, score))

                has_sufficient_evidence = max_score >= cutoff
                return reranked_docs, has_sufficient_evidence

            except Exception as e:
                print(f"FlashRank rerank error ({e}). Returning candidate ranking.")

        # Fallback if reranker is unavailable
        docs_with_scores = candidates[:top_n]
        has_sufficient_evidence = len(docs_with_scores) > 0
        return docs_with_scores, has_sufficient_evidence

_reranker_instance = None

def get_reranker() -> Reranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance

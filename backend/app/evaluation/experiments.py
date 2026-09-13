import os
import json
import time
from typing import Dict, Any, List

from app.evaluation.dataset import load_evaluation_dataset
from app.evaluation.metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr,
    calculate_ndcg_at_k,
    calculate_abstention_metrics,
    is_doc_match
)
from app.rag.pipeline import load_vector_store
from app.rag.query_transform import rewrite_query
from app.rag.bm25 import get_bm25_index
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.reranker import get_reranker
from app.rag.citation_verifier import CitationVerifier

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

class ExperimentRunner:
    def __init__(self):
        self.items = load_evaluation_dataset()
        self.db = load_vector_store()
        self.bm25 = get_bm25_index()
        self.reranker = get_reranker()

    def run_experiments(self) -> Dict[str, Any]:
        experiments_summary = {}

        # 1. Experiment A: Dense Only (FAISS)
        experiments_summary["exp_a_dense_only"] = self._evaluate_config(use_bm25=False, use_rrf=False, use_reranker=False, use_gate=False)

        # 2. Experiment B: Dense + BM25
        experiments_summary["exp_b_dense_bm25"] = self._evaluate_config(use_bm25=True, use_rrf=False, use_reranker=False, use_gate=False)

        # 3. Experiment C: Dense + BM25 + RRF Fusion
        experiments_summary["exp_c_dense_bm25_rrf"] = self._evaluate_config(use_bm25=True, use_rrf=True, use_reranker=False, use_gate=False)

        # 4. Experiment D: Hybrid + FlashRank Reranker
        experiments_summary["exp_d_hybrid_reranker"] = self._evaluate_config(use_bm25=True, use_rrf=True, use_reranker=True, use_gate=False)

        # 5. Experiment E: Hybrid + Reranker + Evidence Gate (Abstention)
        experiments_summary["exp_e_hybrid_reranker_gate"] = self._evaluate_config(use_bm25=True, use_rrf=True, use_reranker=True, use_gate=True)

        # 6. Experiment F: Final Pipeline + Citation Verification
        experiments_summary["exp_f_final_pipeline"] = self._evaluate_config(use_bm25=True, use_rrf=True, use_reranker=True, use_gate=True, use_citations=True)

        os.makedirs(RESULTS_DIR, exist_ok=True)
        out_path = os.path.join(RESULTS_DIR, "experiments.json")
        with open(out_path, "w") as f:
            json.dump(experiments_summary, f, indent=4)

        return experiments_summary

    def _evaluate_config(
        self,
        use_bm25: bool = True,
        use_rrf: bool = True,
        use_reranker: bool = True,
        use_gate: bool = True,
        use_citations: bool = False,
        threshold: float = 0.25
    ) -> Dict[str, Any]:
        recall_1, recall_3, recall_5, recall_10 = [], [], [], []
        precision_1, precision_3, precision_5, precision_10 = [], [], [], []
        mrr_list, ndcg_5_list = [], []
        abstained_preds, should_abstain_truths = [], []
        latencies = []

        for item in self.items:
            t0 = time.time()
            orig_q, search_q = rewrite_query(item.question)

            candidate_k = 15
            dense_docs = []
            if self.db:
                try:
                    res = self.db.similarity_search_with_score(search_q, k=candidate_k)
                    dense_docs = [(doc, 1.0 / (1.0 + score)) for doc, score in res]
                except Exception:
                    dense_docs = []

            bm25_docs = []
            if use_bm25 and self.bm25:
                bm25_docs = self.bm25.search(search_q, top_k=candidate_k)

            if use_rrf and dense_docs and bm25_docs:
                fused = reciprocal_rank_fusion(dense_docs, bm25_docs, k=60, top_n=candidate_k)
            else:
                fused = dense_docs if dense_docs else bm25_docs

            if use_reranker and self.reranker:
                reranked_tuples, has_evidence = self.reranker.rerank(search_q, fused, top_n=5, threshold=threshold)
            else:
                reranked_tuples = [(doc, score) for doc, score in fused[:5]]
                has_evidence = len(reranked_tuples) > 0

            retrieved_docs_objs = [doc for doc, _ in reranked_tuples]
            retrieved_names = [doc.metadata.get("document_name") or doc.metadata.get("source") or "Unknown" for doc in retrieved_docs_objs]

            if use_citations:
                verifier = CitationVerifier(retrieved_docs=retrieved_docs_objs)
                valid_cit = verifier.get_valid_sources()

            latency_ms = (time.time() - t0) * 1000.0
            latencies.append(latency_ms)

            abstained = not has_evidence if use_gate else False
            abstained_preds.append(abstained)
            should_abstain_truths.append(item.should_abstain)

            if not item.should_abstain and item.expected_documents:
                recall_1.append(calculate_recall_at_k(retrieved_names, item.expected_documents, k=1))
                recall_3.append(calculate_recall_at_k(retrieved_names, item.expected_documents, k=3))
                recall_5.append(calculate_recall_at_k(retrieved_names, item.expected_documents, k=5))
                recall_10.append(calculate_recall_at_k(retrieved_names, item.expected_documents, k=10))

                precision_1.append(calculate_precision_at_k(retrieved_names, item.expected_documents, k=1))
                precision_3.append(calculate_precision_at_k(retrieved_names, item.expected_documents, k=3))
                precision_5.append(calculate_precision_at_k(retrieved_names, item.expected_documents, k=5))
                precision_10.append(calculate_precision_at_k(retrieved_names, item.expected_documents, k=10))

                mrr_list.append(calculate_mrr(retrieved_names, item.expected_documents))
                ndcg_5_list.append(calculate_ndcg_at_k(retrieved_names, item.expected_documents, k=5))

        def safe_mean(v):
            return round(sum(v) / len(v), 4) if v else 0.0

        abs_m = calculate_abstention_metrics(abstained_preds, should_abstain_truths)

        return {
            "recall_at_1": safe_mean(recall_1),
            "recall_at_3": safe_mean(recall_3),
            "recall_at_5": safe_mean(recall_5),
            "recall_at_10": safe_mean(recall_10),
            "precision_at_1": safe_mean(precision_1),
            "precision_at_3": safe_mean(precision_3),
            "precision_at_5": safe_mean(precision_5),
            "precision_at_10": safe_mean(precision_10),
            "mrr": safe_mean(mrr_list),
            "ndcg_at_5": safe_mean(ndcg_5_list),
            "abstention_accuracy": abs_m["accuracy"],
            "false_abstention_rate": abs_m["false_abstention_rate"],
            "false_answer_rate": abs_m["false_answer_rate"],
            "mean_latency_ms": safe_mean(latencies)
        }

if __name__ == "__main__":
    runner = ExperimentRunner()
    res = runner.run_experiments()
    print("Controlled RAG Experiments Completed!")

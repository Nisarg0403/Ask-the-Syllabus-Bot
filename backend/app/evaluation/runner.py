import os
import json
import time
from typing import List, Dict, Any, Optional

from app.evaluation.dataset import load_evaluation_dataset, EvaluationItem, DatasetValidator
from app.evaluation.metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr,
    calculate_ndcg_at_k,
    calculate_abstention_metrics,
    is_doc_match,
    StageTimer
)
from app.rag.pipeline import load_vector_store
from app.rag.query_transform import rewrite_query
from app.rag.bm25 import get_bm25_index
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.reranker import get_reranker
from app.rag.citation_verifier import CitationVerifier

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

def classify_failure(
    item: EvaluationItem,
    retrieved_docs: List[str],
    has_sufficient_evidence: bool,
    max_reranker_score: float
) -> str:
    """
    Classifies failure types based on expected ground truth vs pipeline outputs.
    """
    if item.should_abstain:
        if has_sufficient_evidence:
            return "false_answer" # Answer generated on unsupported query (hallucination risk)
        return "none" # Correct abstention
    else:
        if not has_sufficient_evidence:
            return "false_abstention" # Over-abstain on valid query
        
        # Check if expected document was retrieved
        expected_found = any(is_doc_match(ret, exp) for ret in retrieved_docs for exp in item.expected_documents)
        if not expected_found:
            return "retrieval_failure"
            
        if max_reranker_score < 0.25:
            return "ranking_failure"

    return "none"

class EvaluationRunner:
    def __init__(self, dataset_path: Optional[str] = None):
        self.items = load_evaluation_dataset(dataset_path)
        self.db = load_vector_store()
        self.reranker = get_reranker()
        self.bm25 = get_bm25_index()

    def run_evaluation(
        self,
        threshold: float = 0.25,
        output_filename: str = "baseline.json"
    ) -> Dict[str, Any]:
        """
        Executes full benchmark evaluation across all items in the dataset.
        Captures stage-by-stage latencies, per-question trace logs, aggregate metrics, and saves results.
        """
        per_question_traces = []
        abstained_predictions = []
        should_abstain_truths = []

        recall_1_list, recall_3_list, recall_5_list, recall_10_list = [], [], [], []
        precision_1_list, precision_3_list, precision_5_list, precision_10_list = [], [], [], []
        mrr_list = []
        ndcg_5_list = []

        total_latencies = []
        stage_latencies = {
            "query_transformation": [],
            "dense_retrieval": [],
            "bm25_retrieval": [],
            "rrf_fusion": [],
            "reranking": [],
            "evidence_gate": [],
            "citation_verification": []
        }

        failure_counts = {
            "retrieval_failure": 0,
            "ranking_failure": 0,
            "false_abstention": 0,
            "false_answer": 0,
            "none": 0
        }

        for item in self.items:
            timer = StageTimer()
            timer.start("total_end_to_end")

            # 1. Query Transformation
            timer.start("query_transformation")
            orig_q, search_q = rewrite_query(item.question)
            timer.stop("query_transformation")

            retrieved_doc_names = []
            retrieved_pages = []
            reranker_scores = []
            max_score = 0.0
            has_sufficient = False

            if self.db:
                candidate_k = 15

                # 2. Dense FAISS Retrieval
                timer.start("dense_retrieval")
                try:
                    dense_results = self.db.similarity_search_with_score(search_q, k=candidate_k)
                    dense_docs = [(doc, 1.0 / (1.0 + score)) for doc, score in dense_results]
                except Exception:
                    dense_docs = []
                timer.stop("dense_retrieval")

                # 3. Sparse BM25 Retrieval
                timer.start("bm25_retrieval")
                bm25_docs = self.bm25.search(search_q, top_k=candidate_k) if self.bm25 else []
                timer.stop("bm25_retrieval")

                # 4. RRF Fusion
                timer.start("rrf_fusion")
                if dense_docs and bm25_docs:
                    fused_candidates = reciprocal_rank_fusion(dense_docs, bm25_docs, k=60, top_n=candidate_k)
                else:
                    fused_candidates = dense_docs if dense_docs else bm25_docs
                timer.stop("rrf_fusion")

                # 5. Reranking & Evidence Gate
                timer.start("reranking")
                reranked_tuples, has_sufficient = self.reranker.rerank(search_q, fused_candidates, top_n=5, threshold=threshold)
                timer.stop("reranking")

                timer.start("evidence_gate")
                retrieved_docs_objs = [doc for doc, _ in reranked_tuples]
                reranker_scores = [round(score, 4) for _, score in reranked_tuples]
                max_score = max(reranker_scores) if reranker_scores else 0.0
                timer.stop("evidence_gate")

                # Extract metadata
                for doc in retrieved_docs_objs:
                    meta = doc.metadata or {}
                    ret_name = meta.get("document_name") or meta.get("source") or "Unknown"
                    ret_page = meta.get("page_number") or meta.get("page") or 1
                    retrieved_doc_names.append(ret_name)
                    retrieved_pages.append(int(ret_page) if str(ret_page).isdigit() else 1)

            # 6. Citation Verification
            timer.start("citation_verification")
            verifier = CitationVerifier(retrieved_docs=[doc for doc, _ in reranked_tuples] if self.db else [])
            valid_citations = verifier.get_valid_sources()
            timer.stop("citation_verification")

            total_ms = timer.stop("total_end_to_end")

            # Collect stage timings
            for stage, val in timer.timings.items():
                if stage in stage_latencies:
                    stage_latencies[stage].append(val)
            total_latencies.append(total_ms)

            # Collect Abstention Predictions
            abstained_pred = not has_sufficient
            abstained_predictions.append(abstained_pred)
            should_abstain_truths.append(item.should_abstain)

            # Collect Retrieval Metrics if query is supported
            if not item.should_abstain and item.expected_documents:
                r1 = calculate_recall_at_k(retrieved_doc_names, item.expected_documents, k=1)
                r3 = calculate_recall_at_k(retrieved_doc_names, item.expected_documents, k=3)
                r5 = calculate_recall_at_k(retrieved_doc_names, item.expected_documents, k=5)
                r10 = calculate_recall_at_k(retrieved_doc_names, item.expected_documents, k=10)

                p1 = calculate_precision_at_k(retrieved_doc_names, item.expected_documents, k=1)
                p3 = calculate_precision_at_k(retrieved_doc_names, item.expected_documents, k=3)
                p5 = calculate_precision_at_k(retrieved_doc_names, item.expected_documents, k=5)
                p10 = calculate_precision_at_k(retrieved_doc_names, item.expected_documents, k=10)

                mrr_val = calculate_mrr(retrieved_doc_names, item.expected_documents)
                ndcg_5_val = calculate_ndcg_at_k(retrieved_doc_names, item.expected_documents, k=5)

                recall_1_list.append(r1)
                recall_3_list.append(r3)
                recall_5_list.append(r5)
                recall_10_list.append(r10)

                precision_1_list.append(p1)
                precision_3_list.append(p3)
                precision_5_list.append(p5)
                precision_10_list.append(p10)

                mrr_list.append(mrr_val)
                ndcg_5_list.append(ndcg_5_val)

            # Failure classification
            fail_type = classify_failure(item, retrieved_doc_names, has_sufficient, max_score)
            failure_counts[fail_type] = failure_counts.get(fail_type, 0) + 1

            # Per-Question Trace Object
            trace = {
                "id": item.id,
                "category": item.category,
                "original_query": orig_q,
                "rewritten_query": search_q,
                "expected_documents": item.expected_documents,
                "expected_pages": item.expected_pages,
                "should_abstain_ground_truth": item.should_abstain,
                "retrieved_documents": retrieved_doc_names,
                "retrieved_pages": retrieved_pages,
                "reranker_scores": reranker_scores,
                "evidence_score": max_score,
                "evidence_threshold": threshold,
                "abstention_decision": abstained_pred,
                "citations_count": len(valid_citations),
                "failure_classification": fail_type,
                "latency_ms": timer.timings
            }
            per_question_traces.append(trace)

        # Aggregate Metrics Computation
        abstention_metrics = calculate_abstention_metrics(abstained_predictions, should_abstain_truths)

        def safe_mean(vals):
            return round(sum(vals) / len(vals), 4) if vals else 0.0

        avg_stage_latencies = {
            stage: safe_mean(vals) for stage, vals in stage_latencies.items()
        }

        dataset_stats = DatasetValidator.get_statistics(self.items)

        aggregate_results = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "dataset_statistics": dataset_stats,
            "evidence_threshold": threshold,
            "retrieval_metrics": {
                "recall_at_1": safe_mean(recall_1_list),
                "recall_at_3": safe_mean(recall_3_list),
                "recall_at_5": safe_mean(recall_5_list),
                "recall_at_10": safe_mean(recall_10_list),
                "precision_at_1": safe_mean(precision_1_list),
                "precision_at_3": safe_mean(precision_3_list),
                "precision_at_5": safe_mean(precision_5_list),
                "precision_at_10": safe_mean(precision_10_list),
                "mrr": safe_mean(mrr_list),
                "ndcg_at_5": safe_mean(ndcg_5_list)
            },
            "abstention_metrics": abstention_metrics,
            "latency_metrics_ms": {
                "mean_total_end_to_end_ms": safe_mean(total_latencies),
                "stage_breakdown_ms": avg_stage_latencies
            },
            "failure_classification_counts": failure_counts,
            "per_question_traces": per_question_traces
        }

        # Save to machine-readable JSON
        os.makedirs(RESULTS_DIR, exist_ok=True)
        out_path = os.path.join(RESULTS_DIR, output_filename)
        with open(out_path, "w") as f:
            json.dump(aggregate_results, f, indent=4)

        return aggregate_results

    def evaluate_threshold_sensitivity(
        self,
        thresholds: List[float] = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]
    ) -> Dict[float, Dict[str, float]]:
        """
        Runs sensitivity sweep across multiple threshold values against the 100+ dataset.
        """
        sensitivity_report = {}
        for t in thresholds:
            res = self.run_evaluation(threshold=t, output_filename=f"threshold_{t:.2f}.json")
            abs_m = res["abstention_metrics"]
            sensitivity_report[t] = {
                "accuracy": abs_m["accuracy"],
                "precision": abs_m["precision"],
                "recall": abs_m["recall"],
                "false_abstention_rate": abs_m["false_abstention_rate"],
                "false_answer_rate": abs_m["false_answer_rate"]
            }
        return sensitivity_report

if __name__ == "__main__":
    runner = EvaluationRunner()
    results = runner.run_evaluation()
    print("Benchmark Evaluation Completed Successfully!")
    print(f"Total Questions Evaluated: {results['dataset_statistics']['total']}")
    print(f"Recall@5: {results['retrieval_metrics']['recall_at_5']}")
    print(f"MRR: {results['retrieval_metrics']['mrr']}")
    print(f"Abstention Accuracy: {results['abstention_metrics']['accuracy']}")

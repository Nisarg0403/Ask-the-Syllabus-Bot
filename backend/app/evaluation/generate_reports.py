import os
import json

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
baseline_path = os.path.join(RESULTS_DIR, "baseline.json")
final_path = os.path.join(RESULTS_DIR, "final.json")
comp_path = os.path.join(RESULTS_DIR, "comparison.json")
fail_path = os.path.join(RESULTS_DIR, "failures.json")

def generate_comparison_and_failures():
    with open(baseline_path, "r") as f:
        base = json.load(f)
    with open(final_path, "r") as f:
        fin = json.load(f)

    # 1. Comparison JSON
    comparison = {
        "timestamp": fin.get("timestamp"),
        "retrieval_comparison": {
            "recall_at_1": {"baseline": base["retrieval_metrics"]["recall_at_1"], "final": fin["retrieval_metrics"]["recall_at_1"]},
            "recall_at_3": {"baseline": base["retrieval_metrics"]["recall_at_3"], "final": fin["retrieval_metrics"]["recall_at_3"]},
            "recall_at_5": {"baseline": base["retrieval_metrics"]["recall_at_5"], "final": fin["retrieval_metrics"]["recall_at_5"]},
            "recall_at_10": {"baseline": base["retrieval_metrics"]["recall_at_10"], "final": fin["retrieval_metrics"]["recall_at_10"]},
            "precision_at_1": {"baseline": base["retrieval_metrics"]["precision_at_1"], "final": fin["retrieval_metrics"]["precision_at_1"]},
            "precision_at_3": {"baseline": base["retrieval_metrics"]["precision_at_3"], "final": fin["retrieval_metrics"]["precision_at_3"]},
            "precision_at_5": {"baseline": base["retrieval_metrics"]["precision_at_5"], "final": fin["retrieval_metrics"]["precision_at_5"]},
            "precision_at_10": {"baseline": base["retrieval_metrics"]["precision_at_10"], "final": fin["retrieval_metrics"]["precision_at_10"]},
            "mrr": {"baseline": base["retrieval_metrics"]["mrr"], "final": fin["retrieval_metrics"]["mrr"]},
            "ndcg_at_5": {"baseline": base["retrieval_metrics"]["ndcg_at_5"], "final": fin["retrieval_metrics"]["ndcg_at_5"]}
        },
        "abstention_comparison": {
            "accuracy": {"baseline": base["abstention_metrics"]["accuracy"], "final": fin["abstention_metrics"]["accuracy"]},
            "precision": {"baseline": base["abstention_metrics"]["precision"], "final": fin["abstention_metrics"]["precision"]},
            "recall": {"baseline": base["abstention_metrics"]["recall"], "final": fin["abstention_metrics"]["recall"]},
            "false_abstention_rate": {"baseline": base["abstention_metrics"]["false_abstention_rate"], "final": fin["abstention_metrics"]["false_abstention_rate"]},
            "false_answer_rate": {"baseline": base["abstention_metrics"]["false_answer_rate"], "final": fin["abstention_metrics"]["false_answer_rate"]}
        },
        "latency_comparison_ms": {
            "mean_total_ms": {"baseline": base["latency_metrics_ms"]["mean_total_end_to_end_ms"], "final": fin["latency_metrics_ms"]["mean_total_end_to_end_ms"]}
        }
    }
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=4)

    # 2. Failures JSON
    failures = []
    for trace in fin.get("per_question_traces", []):
        if trace.get("failure_classification") != "none":
            failures.append({
                "question_id": trace.get("id"),
                "category": trace.get("category"),
                "failure_type": trace.get("failure_classification"),
                "query": trace.get("original_query"),
                "retrieved_documents": trace.get("retrieved_documents"),
                "expected_documents": trace.get("expected_documents"),
                "evidence_score": trace.get("evidence_score"),
                "evidence_threshold": trace.get("evidence_threshold"),
                "explanation": f"Query classified as {trace.get('failure_classification')}."
            })

    with open(fail_path, "w") as f:
        json.dump(failures, f, indent=4)

    print("Comparison and Failures JSON files generated successfully.")

if __name__ == "__main__":
    generate_comparison_and_failures()

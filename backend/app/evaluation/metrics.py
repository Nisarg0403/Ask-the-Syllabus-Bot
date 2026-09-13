import math
import time
from typing import List, Dict, Any, Set, Tuple, Optional

import re
import os

def normalize_doc_name(doc: str) -> str:
    """Normalizes document names by stripping paths, extension, case, and special punctuation."""
    if not doc:
        return ""
    base = os.path.basename(str(doc))
    # Strip extension
    base_no_ext = os.path.splitext(base)[0]
    # Keep alphanumeric characters and convert to lower
    return re.sub(r'[^a-zA-Z0-9]', '', base_no_ext).lower()

def is_doc_match(retrieved_doc: str, expected_doc: str) -> bool:
    """Robust matching between retrieved and expected document identifiers."""
    r_norm = normalize_doc_name(retrieved_doc)
    e_norm = normalize_doc_name(expected_doc)
    if not r_norm or not e_norm:
        return False
    return (r_norm == e_norm) or (r_norm in e_norm) or (e_norm in r_norm)

def calculate_recall_at_k(retrieved: List[str], expected: List[str], k: int = 5) -> float:
    """
    Calculates Recall@K with normalized document name matching.
    """
    if not expected:
        return 1.0 # Vacuously true for out-of-scope queries
    top_k_retrieved = retrieved[:k]
    matched_expected = 0
    for exp in expected:
        if any(is_doc_match(ret, exp) for ret in top_k_retrieved):
            matched_expected += 1
    return matched_expected / len(expected)

def calculate_precision_at_k(retrieved: List[str], expected: List[str], k: int = 5) -> float:
    """
    Calculates Precision@K with normalized document name matching.
    """
    if not retrieved or k <= 0:
        return 0.0
    if not expected:
        return 1.0 # Out-of-scope query correctly retrieved 0 relevant items
    top_k_retrieved = retrieved[:k]
    relevant_count = sum(1 for ret in top_k_retrieved if any(is_doc_match(ret, exp) for exp in expected))
    return relevant_count / min(k, len(top_k_retrieved))

def calculate_mrr(retrieved: List[str], expected: List[str]) -> float:
    """
    Calculates Mean Reciprocal Rank (MRR) with normalized document matching.
    """
    if not expected:
        return 1.0
    for rank, ret in enumerate(retrieved, start=1):
        if any(is_doc_match(ret, exp) for exp in expected):
            return 1.0 / rank
    return 0.0

def calculate_ndcg_at_k(retrieved: List[str], expected: List[str], k: int = 5) -> float:
    """
    Calculates Normalized Discounted Cumulative Gain (nDCG@K).
    Bounded in [0.0, 1.0]. Each expected document contributes binary relevance at most once.
    """
    if not expected:
        return 1.0
    top_k_retrieved = retrieved[:k]

    dcg = 0.0
    seen_expected = set()
    for rank, ret in enumerate(top_k_retrieved, start=1):
        matched_exp = None
        for exp in expected:
            if exp not in seen_expected and is_doc_match(ret, exp):
                matched_exp = exp
                break
        if matched_exp:
            seen_expected.add(matched_exp)
            dcg += 1.0 / math.log2(rank + 1)

    idcg = 0.0
    for rank in range(1, min(len(expected), k) + 1):
        idcg += 1.0 / math.log2(rank + 1)

    return (dcg / idcg) if idcg > 0 else 0.0

def calculate_abstention_metrics(
    abstained_predictions: List[bool],
    should_abstain_ground_truths: List[bool]
) -> Dict[str, float]:
    """
    Calculates comprehensive Abstention Metrics:
    - True Positives (TP): Correctly abstained on unsupported query
    - False Positives (FP): Incorrectly abstained on supported query (False Abstention)
    - True Negatives (TN): Correctly generated answer on supported query
    - False Negatives (FN): Incorrectly answered unsupported query (False Answer / Hallucination risk)
    """
    if len(abstained_predictions) != len(should_abstain_ground_truths) or not abstained_predictions:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "accuracy": 0.0,
            "false_abstention_rate": 0.0,
            "false_answer_rate": 0.0
        }

    tp = sum(1 for p, g in zip(abstained_predictions, should_abstain_ground_truths) if p and g)
    fp = sum(1 for p, g in zip(abstained_predictions, should_abstain_ground_truths) if p and not g)
    tn = sum(1 for p, g in zip(abstained_predictions, should_abstain_ground_truths) if not p and not g)
    fn = sum(1 for p, g in zip(abstained_predictions, should_abstain_ground_truths) if not p and g)

    total = len(abstained_predictions)
    supported_total = sum(1 for g in should_abstain_ground_truths if not g)
    unsupported_total = sum(1 for g in should_abstain_ground_truths if g)

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    accuracy = (tp + tn) / total
    false_abstention_rate = (fp / supported_total) if supported_total > 0 else 0.0
    false_answer_rate = (fn / unsupported_total) if unsupported_total > 0 else 0.0

    return {
        "tp": float(tp),
        "fp": float(fp),
        "tn": float(tn),
        "fn": float(fn),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "accuracy": round(accuracy, 4),
        "false_abstention_rate": round(false_abstention_rate, 4),
        "false_answer_rate": round(false_answer_rate, 4)
    }

class StageTimer:
    """
    Precision millisecond timer for tracking stage-by-stage pipeline latency.
    """
    def __init__(self):
        self.timings: Dict[str, float] = {}
        self._starts: Dict[str, float] = {}

    def start(self, stage_name: str):
        self._starts[stage_name] = time.perf_counter()

    def stop(self, stage_name: str) -> float:
        if stage_name in self._starts:
            elapsed_ms = round((time.perf_counter() - self._starts[stage_name]) * 1000.0, 2)
            self.timings[stage_name] = elapsed_ms
            return elapsed_ms
        return 0.0

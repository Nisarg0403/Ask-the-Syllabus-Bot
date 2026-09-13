import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.evaluation.dataset import (
    EvaluationItem,
    DatasetValidator,
    generate_100_plus_benchmark_dataset,
    load_evaluation_dataset,
    save_evaluation_dataset
)
from app.evaluation.metrics import (
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_mrr,
    calculate_ndcg_at_k,
    calculate_abstention_metrics,
    StageTimer
)
from app.evaluation.runner import EvaluationRunner

class TestEvaluationFramework(unittest.TestCase):

    def test_dataset_generation_and_validation(self):
        items = generate_100_plus_benchmark_dataset()
        self.assertGreaterEqual(len(items), 100)

        stats = DatasetValidator.get_statistics(items)
        self.assertEqual(stats["total"], 105)
        self.assertEqual(stats["direct"], 20)
        self.assertEqual(stats["multi_chunk"], 15)
        self.assertEqual(stats["cross_doc"], 15)
        self.assertEqual(stats["paraphrased"], 15)
        self.assertEqual(stats["topic_specific"], 15)
        self.assertEqual(stats["out_of_scope"], 10)
        self.assertEqual(stats["adversarial"], 10)
        self.assertEqual(stats["ambiguous"], 5)

        # Check for validation warnings
        all_warnings = []
        for item in items:
            all_warnings.extend(DatasetValidator.validate_item(item))
        self.assertEqual(len(all_warnings), 0)

    def test_retrieval_metrics(self):
        retrieved = ["docA.pdf", "docB.pdf", "docC.pdf", "docD.pdf", "docE.pdf"]
        expected = ["docB.pdf", "docE.pdf"]

        r5 = calculate_recall_at_k(retrieved, expected, k=5)
        self.assertEqual(r5, 1.0) # Both docB and docE retrieved in top 5

        p5 = calculate_precision_at_k(retrieved, expected, k=5)
        self.assertEqual(p5, 2.0 / 5.0)

        mrr = calculate_mrr(retrieved, expected)
        self.assertEqual(mrr, 0.5) # First expected (docB) is at rank 2 -> 1/2 = 0.5

        ndcg = calculate_ndcg_at_k(retrieved, expected, k=5)
        self.assertGreater(ndcg, 0.0)

    def test_abstention_metrics(self):
        predictions = [True, True, False, False]
        truths = [True, False, False, True]

        metrics = calculate_abstention_metrics(predictions, truths)
        self.assertEqual(metrics["tp"], 1.0)
        self.assertEqual(metrics["fp"], 1.0)
        self.assertEqual(metrics["tn"], 1.0)
        self.assertEqual(metrics["fn"], 1.0)
        self.assertEqual(metrics["accuracy"], 0.5)

    def test_stage_timer_latency(self):
        timer = StageTimer()
        timer.start("test_stage")
        import time
        time.sleep(0.01)
        ms = timer.stop("test_stage")
        self.assertGreaterEqual(ms, 5.0)
        self.assertIn("test_stage", timer.timings)

    def test_runner_and_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dataset_path = os.path.join(tmp_dir, "test_dataset.json")
            sample_items = [
                EvaluationItem(
                    id="sample_01",
                    question="What is topic 1?",
                    expected_answer="Topic 1 details",
                    category="direct",
                    expected_documents=["doc1.pdf"],
                    expected_pages=[1],
                    should_abstain=False
                )
            ]
            save_evaluation_dataset(sample_items, tmp_dataset_path)

            runner = EvaluationRunner(dataset_path=tmp_dataset_path)
            res = runner.run_evaluation(threshold=0.25, output_filename="test_out.json")

            self.assertEqual(res["dataset_statistics"]["total"], 1)
            self.assertIn("retrieval_metrics", res)
            self.assertIn("latency_metrics_ms", res)

if __name__ == "__main__":
    unittest.main()

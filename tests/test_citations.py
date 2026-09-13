import os
import sys
import unittest
from langchain_core.documents import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.citation_verifier import CitationVerifier, Citation
from app.rag.reranker import Reranker

class TestCitationVerificationAndAbstention(unittest.TestCase):

    def setUp(self):
        self.sample_docs = [
            Document(
                page_content="Topic 162 covers Production-Grade RAG Upgrade. The final deliverable for Topic 162 is a fully benchmarked, evaluated, and production-ready academic assistant.",
                metadata={
                    "source": "production_rag.pdf",
                    "page": 1,
                    "document_name": "production_rag.pdf",
                    "page_number": 1,
                    "section": "Objective",
                    "chapter": "Unit 1",
                    "chunk_id": "doc1_c1"
                }
            ),
            Document(
                page_content="CS101 Grading Policy: Midterm Exam accounts for 30%, Assignments 30%, and Final Examination 40%.",
                metadata={
                    "source": "cs101_syllabus.pdf",
                    "page": 3,
                    "document_name": "cs101_syllabus.pdf",
                    "page_number": 3,
                    "section": "Grading Policy",
                    "chapter": "General",
                    "chunk_id": "doc2_c1"
                }
            )
        ]
        self.verifier = CitationVerifier(retrieved_docs=self.sample_docs)

    # --- Part I: 10 Citation Regression Tests ---

    def test_1_valid_document_citation(self):
        answer = "Topic 162 details are in [Source: production_rag.pdf, Page: 1]."
        cleaned, citations = self.verifier.extract_and_verify_citations(answer)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].document_name, "production_rag.pdf")

    def test_2_valid_page_citation(self):
        answer = "Grading policy is on [Source: cs101_syllabus.pdf, Page: 3]."
        cleaned, citations = self.verifier.extract_and_verify_citations(answer)
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].page_number, 3)

    def test_3_invalid_document_citation(self):
        # Referencing a fabricated document not in retrieved docs
        answer = "Some information from [Source: fake_syllabus.pdf, Page: 1]."
        cleaned, citations = self.verifier.extract_and_verify_citations(answer)
        # Fabricated inline citation should be stripped
        self.assertNotIn("fake_syllabus.pdf", cleaned)

    def test_4_invalid_page_citation(self):
        # Referencing non-existent page 99 for cs101_syllabus.pdf
        answer = "Info on [Source: cs101_syllabus.pdf, Page: 99]."
        cleaned, citations = self.verifier.extract_and_verify_citations(answer)
        self.assertNotIn("Page: 99", cleaned)

    def test_5_citation_to_non_retrieved_chunk(self):
        # Valid document, but chunk wasn't retrieved
        answer = "Details on [Source: production_rag.pdf, Page: 15]."
        cleaned, citations = self.verifier.extract_and_verify_citations(answer)
        self.assertNotIn("Page: 15", cleaned)

    def test_6_missing_citation_metadata(self):
        empty_doc = [Document(page_content="Text without metadata", metadata={})]
        v = CitationVerifier(retrieved_docs=empty_doc)
        valid = v.get_valid_sources()
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0].document_name, "Unknown Document")

    def test_7_multiple_citations(self):
        answer = "Topic 162 details [Source: production_rag.pdf, Page: 1] and CS101 grading [Source: cs101_syllabus.pdf, Page: 3]."
        cleaned, citations = self.verifier.extract_and_verify_citations(answer)
        self.assertEqual(len(citations), 2)

    def test_8_cross_document_citations(self):
        valid = self.verifier.get_valid_sources()
        doc_names = set(c.document_name for c in valid)
        self.assertIn("production_rag.pdf", doc_names)
        self.assertIn("cs101_syllabus.pdf", doc_names)

    def test_9_unsupported_answer_claims(self):
        answer = "The final deliverable for Topic 162 is a production-ready system. The moon is made of green cheese."
        verified_text, citations = self.verifier.verify_answer_claims(answer)
        # Unsupported claim about the moon should be omitted
        self.assertNotIn("moon is made of green cheese", verified_text)

    def test_10_abstention_without_citations(self):
        empty_verifier = CitationVerifier(retrieved_docs=[])
        answer, citations = empty_verifier.extract_and_verify_citations("I couldn't find sufficient evidence.")
        self.assertEqual(len(citations), 0)

    # --- Part F, G, H: Supported, Unsupported, and Adversarial Tests ---

    def test_supported_question(self):
        reranker = Reranker()
        query = "What is the final deliverable for Topic 162?"
        candidates = [(self.sample_docs[0], 0.85)]
        reranked, sufficient = reranker.rerank(query, candidates, threshold=0.25)
        self.assertTrue(sufficient)
        self.assertGreater(len(reranked), 0)

    def test_unsupported_question(self):
        reranker = Reranker()
        query = "What is the policy for quantum mechanics homework?"
        # Low candidate similarity score
        candidates = [(self.sample_docs[0], 0.05)]
        reranked, sufficient = reranker.rerank(query, candidates, threshold=0.50)
        self.assertFalse(sufficient)

    def test_adversarial_questions(self):
        reranker = Reranker()
        adversarial_queries = [
            "What is the CEO's favorite food?",
            "What is today's Bitcoin price?",
            "What is the current weather in Tokyo?"
        ]
        candidates = [(self.sample_docs[1], 0.02)]
        for q in adversarial_queries:
            reranked, sufficient = reranker.rerank(q, candidates, threshold=0.25)
            self.assertFalse(sufficient, f"Adversarial query '{q}' should trigger abstention gate")

    # --- Part J: Threshold Calibration Experiment ---

    def test_threshold_calibration_experiment(self):
        """
        Runs calibration sweep across thresholds [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]
        and measures abstention accuracy on a controlled calibration dataset.
        """
        reranker = Reranker()

        calibration_data = [
            # Supported
            ("What is the final deliverable for Topic 162?", self.sample_docs[0], True, 0.80),
            ("What is the CS101 exam grading percentage?", self.sample_docs[1], True, 0.75),
            # Unsupported / Adversarial
            ("What is the CEO's favorite food?", self.sample_docs[0], False, 0.05),
            ("What is today's Bitcoin price?", self.sample_docs[1], False, 0.02),
            ("What is the current weather in Tokyo?", self.sample_docs[0], False, 0.03),
        ]

        thresholds = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]
        results = {}

        for t in thresholds:
            correct = 0
            for query, doc, is_supported, mock_score in calibration_data:
                candidates = [(doc, mock_score)]
                _, sufficient = reranker.rerank(query, candidates, threshold=t)
                if sufficient == is_supported:
                    correct += 1
            accuracy = correct / len(calibration_data)
            results[t] = accuracy

        # Verify that threshold 0.25 yields optimal or sub-optimal accuracy >= 80%
        self.assertGreaterEqual(results[0.25], 0.80)

if __name__ == "__main__":
    unittest.main()

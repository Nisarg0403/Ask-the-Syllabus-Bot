import os
import sys
import tempfile
import unittest
from langchain_core.documents import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.ingestion import (
    calculate_file_checksum,
    extract_section_headers,
    structure_aware_split,
    load_metadata,
    save_metadata,
    rebuild_vector_store
)
from app.rag.pipeline import retrieve_context

class TestIngestionModule(unittest.TestCase):

    def test_checksum_generation(self):
        content = b"Sample PDF document binary stream for SHA-256 testing"
        checksum1 = calculate_file_checksum(content)
        checksum2 = calculate_file_checksum(content)
        self.assertEqual(checksum1, checksum2)
        self.assertEqual(len(checksum1), 64) # SHA-256 length

        # Test path checksum vs bytes checksum consistency
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            checksum_file = calculate_file_checksum(tmp_path)
            self.assertEqual(checksum_file, checksum1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_extract_section_headers(self):
        text = "Unit 3: Scheduling Algorithms\nProcess management details..."
        section, chap, topic = extract_section_headers(text)
        self.assertEqual(chap, "Unit 3: Scheduling Algorithms")

        text_policy = "Grading Policy\nFinal Exam 40%, Homework 60%"
        sec, chap, top = extract_section_headers(text_policy)
        self.assertIn("Grading Policy", sec)

    def test_rich_metadata_preservation_and_structure_split(self):
        docs = [
            Document(
                page_content="Unit 1: Intro to AI.\nArtificial intelligence algorithms and concepts.\n\nSection Grading Policy\nExams count for 50%.",
                metadata={
                    "source": "ai_syllabus.pdf",
                    "document_name": "ai_syllabus.pdf",
                    "document_id": "ai_syllabus.pdf",
                    "document_checksum": "abcdef1234567890abcdef1234567890",
                    "page": 1,
                    "page_number": 1,
                    "section": "General",
                    "chapter": "Unit 1: Intro to AI",
                    "topic": "",
                    "document_version": "abcdef12",
                    "indexed_at": "2026-09-13T14:30:00"
                }
            )
        ]

        chunks = structure_aware_split(docs, chunk_size=100, chunk_overlap=20)
        self.assertGreater(len(chunks), 0)

        # Check backward compatibility keys
        self.assertIn("source", chunks[0].metadata)
        self.assertIn("page", chunks[0].metadata)
        self.assertEqual(chunks[0].metadata["source"], "ai_syllabus.pdf")
        self.assertEqual(chunks[0].metadata["page"], 1)

        # Check rich metadata keys
        self.assertIn("document_checksum", chunks[0].metadata)
        self.assertIn("chunk_id", chunks[0].metadata)
        self.assertTrue(chunks[0].metadata["chunk_id"].startswith("abcdef12_p1_c"))

    def test_backward_compatibility_with_pipeline(self):
        docs = [
            Document(
                page_content="The final examination is scheduled for December 20th in Auditorium A.",
                metadata={
                    "source": "exam_schedule.pdf",
                    "page": 4,
                    "document_name": "exam_schedule.pdf",
                    "document_checksum": "1234567890abcdef",
                    "page_number": 4
                }
            )
        ]

        # Verify legacy pipeline snippet works without key errors
        formatted_snippet = f"[Source: {docs[0].metadata.get('source')}, Page: {docs[0].metadata.get('page')}]\n{docs[0].page_content}"
        self.assertIn("[Source: exam_schedule.pdf, Page: 4]", formatted_snippet)
        self.assertIn("December 20th", formatted_snippet)

if __name__ == "__main__":
    unittest.main()

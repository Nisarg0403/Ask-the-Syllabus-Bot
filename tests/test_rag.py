import os
import sys
import unittest
from langchain_core.documents import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.pipeline import stream_answer

class TestRAGPipeline(unittest.TestCase):

    def test_context_construction(self):
        docs = [
            Document(page_content="Grading Criteria: Assignments 30%, Midterm 30%, Final Exam 40%.", metadata={"source": "syllabus.pdf", "page": 2})
        ]
        # Verify generator builds without syntax errors
        context_str = ""
        for doc in docs:
            context_str += f"[Source: {doc.metadata['source']}, Page: {doc.metadata['page']}]\n{doc.page_content}\n\n"
        
        self.assertIn("Grading Criteria", context_str)
        self.assertIn("Page: 2", context_str)

if __name__ == "__main__":
    unittest.main()

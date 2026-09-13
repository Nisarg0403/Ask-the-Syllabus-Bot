import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app

class TestUploadEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_upload_without_filename(self):
        # Sending a file payload with empty/None filename
        response = self.client.post(
            "/api/upload",
            files={"file": ("", b"dummy content", "application/pdf")}
        )
        self.assertIn(response.status_code, (400, 422))

    def test_upload_non_pdf_filename(self):
        response = self.client.post(
            "/api/upload",
            files={"file": ("test.txt", b"dummy content", "text/plain")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only PDF files are supported.", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()

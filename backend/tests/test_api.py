import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

class TestFastAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "online")

    def test_models_endpoint(self):
        response = self.client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        self.assertIn("online", response.json())
        self.assertIn("models", response.json())

    def test_documents_endpoint(self):
        response = self.client.get("/api/documents")
        self.assertEqual(response.status_code, 200)
        self.assertIn("documents", response.json())

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("active", response.json())
        self.assertIn("size", response.json())

if __name__ == "__main__":
    unittest.main()

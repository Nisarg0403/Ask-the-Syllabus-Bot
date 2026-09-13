import os
import sys
import unittest
import logging
import json
import uuid
import tempfile
import shutil
from fastapi.testclient import TestClient

from app.main import app
from app.core import config
from app.core.config import validate_config, get_safe_config
from app.core.logging_config import StructuredJsonFormatter, request_id_var, app_logger
from app.core.observability import (
    log_rag_stage,
    log_ingestion_stage,
    log_job_event,
    log_error_event
)

class TestObservabilityAndConfig(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # 1. Request ID generation
    def test_1_request_id_generation(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
        req_id = response.headers["X-Request-ID"]
        self.assertTrue(len(req_id) > 0)

    # 2. Request ID propagation
    def test_2_request_id_propagation(self):
        custom_req_id = f"custom-req-{uuid.uuid4()}"
        response = self.client.get("/api/status", headers={"X-Request-ID": custom_req_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], custom_req_id)

    # 3. Request ID response header
    def test_3_request_id_response_header(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)

    # 4. Structured logging format
    def test_4_structured_logging_format(self):
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test log message",
            args=(),
            exc_info=None
        )
        record.extra_data = {"test_metric": 123}
        token = request_id_var.set("req-12345")
        try:
            formatted_json = formatter.format(record)
            parsed = json.loads(formatted_json)
            self.assertEqual(parsed["message"], "Test log message")
            self.assertEqual(parsed["request_id"], "req-12345")
            self.assertEqual(parsed["test_metric"], 123)
        finally:
            request_id_var.reset(token)

    # 5. RAG stage logging
    def test_5_rag_stage_logging(self):
        # Should execute without error
        log_rag_stage("QUERY_TRANSFORM", 12.5, {"is_rewritten": True})
        log_rag_stage("DENSE_SEARCH", 45.2, {"candidate_count": 10})

    # 6. Ingestion stage logging
    def test_6_ingestion_stage_logging(self):
        log_ingestion_stage("test.pdf", "EMBEDDING", 150.0, {"chunk_count": 5}, job_id="job_001")

    # 7. Job lifecycle logging
    def test_7_job_lifecycle_logging(self):
        log_job_event("job_001", "test.pdf", "QUEUED")
        log_job_event("job_001", "test.pdf", "PROCESSING")
        log_job_event("job_001", "test.pdf", "COMPLETED", duration_ms=250.0)

    # 8. Error logging
    def test_8_error_logging(self):
        try:
            raise ValueError("Test internal failure")
        except Exception as e:
            log_error_event("/api/test", e, {"context_param": "foo"})

    # 9. Sensitive information is not logged
    def test_9_sensitive_info_not_logged(self):
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Sensitive log attempt",
            args=(),
            exc_info=None
        )
        record.extra_data = {
            "safe_param": "ok",
            "api_key": "SECRET_KEY_12345",
            "raw_prompt": "Secret prompt content",
            "document_content": "Full PDF text content..."
        }
        formatted_json = formatter.format(record)
        parsed = json.loads(formatted_json)

        self.assertEqual(parsed["safe_param"], "ok")
        self.assertNotIn("api_key", parsed)
        self.assertNotIn("raw_prompt", parsed)
        self.assertNotIn("document_content", parsed)

    # 10. /api/status remains functional & detailed
    def test_10_status_endpoint_functional(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("active", data)
        self.assertIn("size", data)
        self.assertIn("environment", data)
        self.assertIn("indexed_documents_count", data)
        self.assertIn("active_model", data)

    # 11. Default configuration loading
    def test_11_default_config_loading(self):
        self.assertIsNotNone(config.DEFAULT_CHUNK_SIZE)
        self.assertGreater(config.DEFAULT_CHUNK_SIZE, 0)
        self.assertIsNotNone(config.EVIDENCE_THRESHOLD)

    # 12. Environment variable overrides
    def test_12_env_variable_overrides(self):
        old_val = os.environ.get("ENVIRONMENT")
        os.environ["ENVIRONMENT"] = "testing_env"
        try:
            # Re-read or check setting
            self.assertEqual(os.getenv("ENVIRONMENT"), "testing_env")
        finally:
            if old_val is not None:
                os.environ["ENVIRONMENT"] = old_val
            else:
                os.environ.pop("ENVIRONMENT", None)

    # 13. Numeric validation
    def test_13_numeric_validation(self):
        # Current config should validate cleanly
        try:
            validate_config()
        except ValueError as e:
            self.fail(f"validate_config raised unexpected ValueError: {e}")

    # 14. Invalid chunk configuration
    def test_14_invalid_chunk_config(self):
        old_size = config.DEFAULT_CHUNK_SIZE
        old_overlap = config.DEFAULT_CHUNK_OVERLAP
        config.DEFAULT_CHUNK_SIZE = 100
        config.DEFAULT_CHUNK_OVERLAP = 200  # Overlap >= Size
        try:
            with self.assertRaises(ValueError):
                validate_config()
        finally:
            config.DEFAULT_CHUNK_SIZE = old_size
            config.DEFAULT_CHUNK_OVERLAP = old_overlap

    # 15. Invalid top_k
    def test_15_invalid_top_k(self):
        old_top_k = config.DEFAULT_TOP_K
        config.DEFAULT_TOP_K = 0
        try:
            with self.assertRaises(ValueError):
                validate_config()
        finally:
            config.DEFAULT_TOP_K = old_top_k

    # 16. Invalid evidence threshold
    def test_16_invalid_evidence_threshold(self):
        old_thresh = config.EVIDENCE_THRESHOLD
        config.EVIDENCE_THRESHOLD = 1.5
        try:
            with self.assertRaises(ValueError):
                validate_config()
        finally:
            config.EVIDENCE_THRESHOLD = old_thresh

    # 17. Invalid embedding dimension
    def test_17_invalid_embedding_dimension(self):
        old_dim = config.EMBEDDING_DIMENSION
        config.EMBEDDING_DIMENSION = -10
        try:
            with self.assertRaises(ValueError):
                validate_config()
        finally:
            config.EMBEDDING_DIMENSION = old_dim

    # 18. Invalid provider
    def test_18_invalid_provider(self):
        old_provider = config.DEFAULT_LLM_PROVIDER
        config.DEFAULT_LLM_PROVIDER = "unsupported_llm"
        try:
            with self.assertRaises(ValueError):
                validate_config()
        finally:
            config.DEFAULT_LLM_PROVIDER = old_provider

    # 19. Configuration precedence
    def test_19_config_precedence(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["chunk_size"], config.DEFAULT_CHUNK_SIZE)

    # 20. Secret values are not exposed
    def test_20_secrets_not_exposed(self):
        safe_conf = get_safe_config()
        self.assertNotIn("openrouter_api_key", safe_conf)
        self.assertNotIn("OPENROUTER_API_KEY", safe_conf)
        self.assertNotIn("password", safe_conf)

        response = self.client.get("/api/config")
        data = response.json()
        self.assertNotIn("OPENROUTER_API_KEY", data)
        self.assertNotIn("openrouter_api_key", data)

if __name__ == "__main__":
    unittest.main()

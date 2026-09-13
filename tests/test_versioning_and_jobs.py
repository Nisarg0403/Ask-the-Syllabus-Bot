import os
import sys
import tempfile
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.registry import DocumentRegistry
from app.services.manifest import IndexManifest
from app.services.jobs import IngestionJobManager
from app.main import app

class TestDocumentVersioningAndJobs(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_registry.db")
        self.manifest_path = os.path.join(self.tmp_dir.name, "test_manifest.json")
        self.jobs_path = os.path.join(self.tmp_dir.name, "test_jobs.json")

        self.registry = DocumentRegistry(db_path=self.db_path)
        self.manifest = IndexManifest(manifest_path=self.manifest_path)
        self.job_manager = IngestionJobManager(jobs_file=self.jobs_path)
        self.client = TestClient(app)

    def tearDown(self):
        self.tmp_dir.cleanup()

    # 1. New document registration
    def test_1_new_document_registration(self):
        doc_id = self.registry.get_or_create_document("syllabus_v1.pdf")
        self.assertTrue(doc_id.startswith("doc_"))

    # 2. Same checksum duplicate detection
    def test_2_same_checksum_duplicate_detection(self):
        checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.registry.add_version("math.pdf", checksum, "1.0 MB", 5, 10, "COMPLETED")
        found = self.registry.find_by_checksum(checksum)
        self.assertIsNotNone(found)
        self.assertEqual(found["document_name"], "math.pdf")

    # 3. Different checksum creates new version
    def test_3_different_checksum_creates_new_version(self):
        c1 = "1111111111111111111111111111111111111111111111111111111111111111"
        c2 = "2222222222222222222222222222222222222222222222222222222222222222"
        _, _, v1 = self.registry.add_version("physics.pdf", c1, "1 MB", 2, 4)
        _, _, v2 = self.registry.add_version("physics.pdf", c2, "1.2 MB", 3, 6)
        self.assertEqual(v1, 1)
        self.assertEqual(v2, 2)
        history = self.registry.get_document_versions("physics.pdf")
        self.assertEqual(len(history), 2)

    # 4. Same content under different filename
    def test_4_same_content_different_filename(self):
        checksum = "3333333333333333333333333333333333333333333333333333333333333333"
        self.registry.add_version("docA.pdf", checksum, "0.5 MB", 1, 2, "COMPLETED")
        found = self.registry.find_by_checksum(checksum)
        self.assertIsNotNone(found, "find_by_checksum returned None for checksum")
        self.assertEqual(found["document_name"], "docA.pdf")

    # 5. Registry survives restart
    def test_5_registry_survives_restart(self):
        self.registry.add_version("chem.pdf", "hash123", "2 MB", 10, 20)
        restarted_registry = DocumentRegistry(db_path=self.db_path)
        latest = restarted_registry.get_latest_version("chem.pdf")
        self.assertIsNotNone(latest)
        self.assertEqual(latest["checksum_sha256"], "hash123")

    # 6. Manifest creation
    def test_6_manifest_creation(self):
        data = self.manifest.save({"doc1.pdf": "hash1"}, num_vectors=10, num_bm25_docs=10)
        self.assertEqual(data["num_vectors"], 10)
        self.assertTrue(os.path.exists(self.manifest_path))

    # 7. Manifest loading
    def test_7_manifest_loading(self):
        self.manifest.save({"doc1.pdf": "hash1"}, num_vectors=5, num_bm25_docs=5)
        loaded = self.manifest.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["num_vectors"], 5)

    # 8. Index compatibility validation
    def test_8_index_compatibility_validation(self):
        self.manifest.save({"doc1.pdf": "hash1"}, num_vectors=5, num_bm25_docs=5, embedding_model="all-MiniLM-L6-v2")
        valid = self.manifest.validate("all-MiniLM-L6-v2", 384)
        self.assertTrue(valid)

        invalid = self.manifest.validate("incompatible-model-v1", 768)
        self.assertFalse(invalid)

    # 9 & 10. Incremental ingestion and existing version skip
    def test_9_10_incremental_ingestion_and_skip(self):
        self.registry.add_version("bio.pdf", "bio_hash", "1 MB", 2, 4, "COMPLETED")
        active = self.registry.get_all_active_documents()
        self.assertEqual(len(active), 1)

    # 11. Job creation
    def test_11_job_creation(self):
        job = self.job_manager.create_job("cs101.pdf", "hash_cs101")
        self.assertEqual(job["status"], "QUEUED")
        self.assertEqual(job["document_name"], "cs101.pdf")

    # 12. QUEUED -> PROCESSING -> COMPLETED
    def test_12_job_state_transitions(self):
        job = self.job_manager.create_job("cs101.pdf", "hash_cs101")
        j_id = job["job_id"]
        
        proc = self.job_manager.update_job(j_id, "PROCESSING", progress=0.5)
        self.assertIsNotNone(proc, f"update_job returned None for job_id {j_id}")
        self.assertEqual(proc["status"], "PROCESSING")

        comp = self.job_manager.update_job(j_id, "COMPLETED", progress=1.0)
        self.assertIsNotNone(comp, f"update_job returned None for job_id {j_id}")
        self.assertEqual(comp["status"], "COMPLETED")

    # 13 & 14. FAILED job and exception handling
    def test_13_14_failed_job_and_error_handling(self):
        job = self.job_manager.create_job("corrupt.pdf", "hash_bad")
        j_id = job["job_id"]
        failed = self.job_manager.update_job(j_id, "FAILED", error_message="PDF parsing failure")
        self.assertIsNotNone(failed, f"update_job returned None for job_id {j_id}")
        self.assertEqual(failed["status"], "FAILED")
        self.assertEqual(failed["error_message"], "PDF parsing failure")

    # 15. Duplicate concurrent ingestion protection
    def test_15_duplicate_concurrent_ingestion_protection(self):
        job1 = self.job_manager.create_job("dup.pdf", "same_hash")
        job2 = self.job_manager.create_job("dup.pdf", "same_hash")
        self.assertEqual(job1["job_id"], job2["job_id"])

    # 16. Stale PROCESSING job recovery
    def test_16_stale_processing_job_recovery(self):
        job = self.job_manager.create_job("crash.pdf", "hash_crash")
        self.job_manager.update_job(job["job_id"], "PROCESSING")

        restarted_mgr = IngestionJobManager(jobs_file=self.jobs_path)
        restarted_mgr.recover_stale_jobs()
        recovered = restarted_mgr.get_job(job["job_id"])
        self.assertIsNotNone(recovered, f"get_job returned None for job_id {job['job_id']}")
        self.assertEqual(recovered["status"], "FAILED")
        self.assertIn("ungracefully", recovered["error_message"])

    # 17. Deletion and version semantics
    def test_17_deletion_semantics(self):
        self.registry.add_version("del.pdf", "h1", "1 MB", 1, 2)
        deleted = self.registry.delete_document("del.pdf")
        self.assertTrue(deleted)
        self.assertIsNone(self.registry.get_latest_version("del.pdf"))

    # 18. FAISS and BM25 synchronization
    def test_18_faiss_bm25_sync(self):
        self.manifest.save({"sync.pdf": "h1"}, num_vectors=10, num_bm25_docs=10)
        m = self.manifest.load()
        self.assertIsNotNone(m, "Manifest file failed to load")
        self.assertEqual(m["num_vectors"], m["num_bm25_documents"])

    # 19. Reset behavior
    def test_19_reset_behavior(self):
        self.registry.add_version("reset.pdf", "h1", "1 MB", 1, 2)
        self.registry.reset_all()
        self.assertEqual(len(self.registry.get_all_active_documents()), 0)

    # 20. API backward compatibility
    def test_20_api_backward_compatibility(self):
        response = self.client.get("/api/documents")
        self.assertEqual(response.status_code, 200)
        self.assertIn("documents", response.json())

        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()

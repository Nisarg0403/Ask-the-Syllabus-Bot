import os
import json
import datetime
from typing import Dict, Any, Optional, List
from app.core.config import STORAGE_DIR, EMBEDDING_MODEL_NAME

MANIFEST_PATH = os.path.join(STORAGE_DIR, "index_manifest.json")

class IndexManifest:
    """
    Persistent Index Manifest describing FAISS/BM25 schema, active document versions,
    vector counts, and embedding model parameters.
    """

    def __init__(self, manifest_path: str = MANIFEST_PATH):
        self.manifest_path = manifest_path

    def load(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def save(
        self,
        active_checksums: Dict[str, str],
        num_vectors: int,
        num_bm25_docs: int,
        embedding_model: str = EMBEDDING_MODEL_NAME,
        embedding_dim: int = 384,
        indexed_version_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        manifest_data = {
            "schema_version": "1.0",
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dim,
            "num_vectors": num_vectors,
            "num_bm25_documents": num_bm25_docs,
            "active_checksums": active_checksums,
            "indexed_version_ids": indexed_version_ids or [],
            "chunking_config": {
                "chunk_size": 1000,
                "chunk_overlap": 200
            },
            "status": "VALID"
        }
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        with open(self.manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=4)
        return manifest_data

    def validate(
        self,
        expected_model: str = EMBEDDING_MODEL_NAME,
        expected_dim: int = 384
    ) -> bool:
        """
        Validates index compatibility against expected embedding model and schema.
        """
        data = self.load()
        if not data:
            return False
        if data.get("status") != "VALID":
            return False
        if data.get("embedding_model") != expected_model:
            return False
        if data.get("embedding_dimension") != expected_dim:
            return False
        return True

    def invalidate(self):
        """
        Marks manifest as invalid (e.g. during incomplete rebuild or reset).
        """
        data = self.load() or {}
        data["status"] = "INVALID"
        data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        if os.path.exists(os.path.dirname(self.manifest_path)):
            with open(self.manifest_path, "w") as f:
                json.dump(data, f, indent=4)

    def clear(self):
        """
        Removes manifest file from disk.
        """
        if os.path.exists(self.manifest_path):
            try:
                os.remove(self.manifest_path)
            except Exception:
                pass

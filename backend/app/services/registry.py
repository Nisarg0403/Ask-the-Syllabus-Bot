import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import STORAGE_DIR

DB_PATH = os.path.join(STORAGE_DIR, "registry.db")

class DocumentRegistry:
    """
    Lightweight Persistent Document Registry backed by SQLite.
    Manages document identity, SHA-256 versioning history, and indexing status.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                document_name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
                version_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                checksum_sha256 TEXT NOT NULL,
                file_size TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                chunk_count INTEGER NOT NULL,
                indexed_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(document_id)
            );
            """)
            conn.commit()
        finally:
            conn.close()

    def get_or_create_document(self, document_name: str) -> str:
        """
        Gets existing document_id or creates a new document entry.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT document_id FROM documents WHERE document_name = ?", (document_name,))
            row = cursor.fetchone()
            if row:
                return row["document_id"]
            
            doc_id = f"doc_{hash(document_name) & 0xffffffff:08x}"
            now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            cursor.execute(
                "INSERT INTO documents (document_id, document_name, created_at) VALUES (?, ?, ?)",
                (doc_id, document_name, now)
            )
            conn.commit()
            return doc_id
        finally:
            conn.close()

    def add_version(
        self,
        document_name: str,
        checksum: str,
        file_size: str,
        page_count: int,
        chunk_count: int,
        status: str = "COMPLETED",
        error_message: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Registers a new version for a document under its SHA-256 checksum.
        Returns (document_id, version_id, version_number).
        """
        doc_id = self.get_or_create_document(document_name)
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Find current highest version_number for this document
            cursor.execute(
                "SELECT MAX(version_number) as max_v FROM document_versions WHERE document_id = ?",
                (doc_id,)
            )
            row = cursor.fetchone()
            next_v = (row["max_v"] or 0) + 1 if row and row["max_v"] is not None else 1

            version_id = f"{checksum[:8]}_v{next_v}"
            cursor.execute("""
            INSERT INTO document_versions (
                version_id, document_id, version_number, checksum_sha256,
                file_size, page_count, chunk_count, indexed_at, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_id, doc_id, next_v, checksum,
                file_size, page_count, chunk_count, now, status, error_message
            ))
            conn.commit()
            return doc_id, version_id, next_v
        finally:
            conn.close()

    def find_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """
        Finds any existing document version with matching SHA-256 checksum across all documents.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT v.*, d.document_name
            FROM document_versions v
            JOIN documents d ON v.document_id = d.document_id
            WHERE v.checksum_sha256 = ? AND v.status = 'COMPLETED'
            ORDER BY v.version_number DESC LIMIT 1
            """, (checksum,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_latest_version(self, document_name: str) -> Optional[Dict[str, Any]]:
        """
        Gets the latest completed version metadata for a document name.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT v.*, d.document_name
            FROM document_versions v
            JOIN documents d ON v.document_id = d.document_id
            WHERE d.document_name = ? AND v.status = 'COMPLETED'
            ORDER BY v.version_number DESC LIMIT 1
            """, (document_name,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_all_active_documents(self) -> List[Dict[str, Any]]:
        """
        Gets all active documents and their latest completed version metadata.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT d.document_name, d.created_at, v.version_id, v.checksum_sha256,
                   v.file_size, v.page_count, v.chunk_count, v.indexed_at, v.version_number
            FROM documents d
            JOIN document_versions v ON d.document_id = v.document_id
            WHERE v.version_number = (
                SELECT MAX(v2.version_number)
                FROM document_versions v2
                WHERE v2.document_id = d.document_id AND v2.status = 'COMPLETED'
            )
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_document_versions(self, document_name: str) -> List[Dict[str, Any]]:
        """
        Gets full version history for a specific document name.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT v.*, d.document_name
            FROM document_versions v
            JOIN documents d ON v.document_id = d.document_id
            WHERE d.document_name = ?
            ORDER BY v.version_number DESC
            """, (document_name,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def delete_document(self, document_name: str) -> bool:
        """
        Removes document and its version history from registry.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT document_id FROM documents WHERE document_name = ?", (document_name,))
            row = cursor.fetchone()
            if not row:
                return False
            doc_id = row["document_id"]
            cursor.execute("DELETE FROM document_versions WHERE document_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE document_id = ?", (doc_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def reset_all(self):
        """
        Clears all tables in registry.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_versions;")
            cursor.execute("DELETE FROM documents;")
            conn.commit()
        finally:
            conn.close()

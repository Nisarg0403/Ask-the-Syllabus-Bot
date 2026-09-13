import os
import json
import uuid
import datetime
import threading
from typing import Dict, Any, Optional, List
from app.core.config import STORAGE_DIR

JOBS_FILE = os.path.join(STORAGE_DIR, "jobs.json")
INGESTION_LOCK = threading.Lock()

class IngestionJobManager:
    """
    Lightweight, thread-safe background ingestion job manager.
    Tracks job status transitions: QUEUED -> PROCESSING -> COMPLETED / FAILED.
    Survives restart and recovers stale jobs on application launch.
    """

    def __init__(self, jobs_file: str = JOBS_FILE):
        self.jobs_file = jobs_file
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.jobs_file), exist_ok=True)
        self._init_jobs_file()

    def _init_jobs_file(self):
        if not os.path.exists(self.jobs_file):
            self._save_jobs({})

    def _load_jobs(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            if os.path.exists(self.jobs_file):
                try:
                    with open(self.jobs_file, "r") as f:
                        return json.load(f)
                except Exception:
                    pass
            return {}

    def _save_jobs(self, jobs: Dict[str, Dict[str, Any]]):
        with self._lock:
            os.makedirs(os.path.dirname(self.jobs_file), exist_ok=True)
            with open(self.jobs_file, "w") as f:
                json.dump(jobs, f, indent=4)

    def create_job(self, document_name: str, checksum: str) -> Dict[str, Any]:
        """
        Creates a new ingestion job in QUEUED status.
        Prevents concurrent duplicate queued jobs for identical checksum.
        """
        jobs = self._load_jobs()

        # Check for active concurrent job for same checksum
        for j_id, j_data in jobs.items():
            if j_data.get("checksum") == checksum and j_data.get("status") in ("QUEUED", "PROCESSING"):
                return j_data

        job_id = f"job_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        job_data = {
            "job_id": job_id,
            "document_name": document_name,
            "checksum": checksum,
            "status": "QUEUED",
            "progress": 0.0,
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "error_message": None
        }

        jobs[job_id] = job_data
        self._save_jobs(jobs)
        return job_data

    def update_job(
        self,
        job_id: str,
        status: str,
        progress: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Updates job status, progress, and timestamps.
        """
        jobs = self._load_jobs()
        if job_id not in jobs:
            return None

        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        job = jobs[job_id]
        job["status"] = status

        if status == "PROCESSING" and not job.get("started_at"):
            job["started_at"] = now
        elif status in ("COMPLETED", "FAILED"):
            job["completed_at"] = now

        if progress is not None:
            job["progress"] = progress
        if error_message is not None:
            job["error_message"] = error_message

        jobs[job_id] = job
        self._save_jobs(jobs)
        return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets current job info by job_id.
        """
        jobs = self._load_jobs()
        return jobs.get(job_id)

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Gets list of all tracked ingestion jobs.
        """
        jobs = self._load_jobs()
        return list(jobs.values())

    def recover_stale_jobs(self):
        """
        On application startup, detects any jobs left in PROCESSING status (due to crash)
        and marks them as FAILED.
        """
        jobs = self._load_jobs()
        modified = False
        now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        for job_id, job in jobs.items():
            if job.get("status") in ("PROCESSING", "QUEUED"):
                job["status"] = "FAILED"
                job["error_message"] = "Process terminated ungracefully before completion."
                job["completed_at"] = now
                modified = True

        if modified:
            self._save_jobs(jobs)

    def clear_all(self):
        """
        Clears job history.
        """
        self._save_jobs({})

_job_manager_instance = None

def get_job_manager() -> IngestionJobManager:
    global _job_manager_instance
    if _job_manager_instance is None:
        _job_manager_instance = IngestionJobManager()
    return _job_manager_instance

import time
import logging
from typing import Dict, Any, Optional, List
from app.core.logging_config import app_logger, request_id_var

def get_current_request_id() -> Optional[str]:
    """Returns the current request ID from context."""
    return request_id_var.get()

def log_rag_stage(
    stage: str,
    duration_ms: float,
    metrics: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    """
    Logs structured RAG pipeline stage performance and telemetry.
    Stages: QUERY_TRANSFORM, DENSE_SEARCH, SPARSE_SEARCH, RRF_FUSION, RERANKING, EVIDENCE_GATE, GENERATION, CITATION_VERIFICATION.
    """
    extra_data = {
        "event_type": "rag_stage",
        "stage": stage,
        "duration_ms": round(duration_ms, 2),
        "status": "FAILED" if error else "SUCCESS"
    }
    if metrics:
        # Sanitize metrics to avoid dumping full text or prompts
        safe_metrics = {
            k: v for k, v in metrics.items()
            if k not in ("raw_prompt", "full_text", "document_content")
        }
        extra_data.update(safe_metrics)

    if error:
        extra_data["error"] = error
        app_logger.error(f"RAG Stage {stage} failed in {duration_ms:.2f}ms: {error}", extra={"extra_data": extra_data})
    else:
        app_logger.info(f"RAG Stage {stage} completed in {duration_ms:.2f}ms", extra={"extra_data": extra_data})

def log_ingestion_stage(
    document_name: str,
    stage: str,
    duration_ms: float,
    metrics: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    error: Optional[str] = None
):
    """
    Logs structured document ingestion telemetry.
    Stages: CHECKSUM, REGISTRATION, PDF_EXTRACTION, CHUNKING, EMBEDDING, FAISS_UPDATE, BM25_UPDATE, MANIFEST_UPDATE, COMPLETED.
    """
    extra_data = {
        "event_type": "ingestion_stage",
        "document_name": document_name,
        "stage": stage,
        "duration_ms": round(duration_ms, 2),
        "job_id": job_id,
        "status": "FAILED" if error else "SUCCESS"
    }
    if metrics:
        extra_data.update(metrics)

    if error:
        extra_data["error"] = error
        app_logger.error(f"Ingestion Stage {stage} failed for {document_name}: {error}", extra={"extra_data": extra_data})
    else:
        app_logger.info(f"Ingestion Stage {stage} completed for {document_name} in {duration_ms:.2f}ms", extra={"extra_data": extra_data})

def log_job_event(
    job_id: str,
    document_name: str,
    status: str,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
):
    """
    Logs background job state transitions: QUEUED, PROCESSING, COMPLETED, FAILED.
    """
    extra_data = {
        "event_type": "job_event",
        "job_id": job_id,
        "document_name": document_name,
        "job_status": status
    }
    if duration_ms is not None:
        extra_data["duration_ms"] = round(duration_ms, 2)
    if error:
        extra_data["error"] = error

    log_msg = f"Job {job_id} ({document_name}) transitioned to {status}"
    if error:
        app_logger.error(log_msg, extra={"extra_data": extra_data})
    else:
        app_logger.info(log_msg, extra={"extra_data": extra_data})

def log_error_event(
    endpoint: str,
    error: Exception,
    extra_context: Optional[Dict[str, Any]] = None
):
    """
    Logs application error events with context.
    """
    extra_data = {
        "event_type": "app_error",
        "endpoint": endpoint,
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    if extra_context:
        extra_data.update(extra_context)

    app_logger.error(f"Error on {endpoint}: {str(error)}", exc_info=True, extra={"extra_data": extra_data})

import os
import shutil
import json
import datetime
import requests
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.core.config import DATA_DIR, FAISS_DIR, METADATA_FILE, OLLAMA_BASE_URL
from app.models.schemas import QueryRequest
from app.rag.ingestion import (
    load_metadata,
    save_metadata,
    rebuild_vector_store,
    calculate_file_checksum
)
from app.rag.pipeline import (
    load_vector_store,
    retrieve_context,
    stream_answer
)

router = APIRouter(prefix="/api")

@router.get("/health")
async def get_health():
    """Liveness probe: Returns HTTP 200 if API process is running."""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@router.get("/evaluation/results")
async def get_evaluation_results():
    """Returns generated benchmark evaluation results, controlled experiments, and metrics."""
    eval_dir = os.path.join(os.path.dirname(__file__), "..", "evaluation", "results")
    final_file = os.path.join(eval_dir, "final.json")
    exp_file = os.path.join(eval_dir, "experiments.json")
    comp_file = os.path.join(eval_dir, "comparison.json")
    fail_file = os.path.join(eval_dir, "failures.json")

    def read_json_if_exists(p):
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    return {
        "final": read_json_if_exists(final_file) or read_json_if_exists(os.path.join(eval_dir, "baseline.json")),
        "experiments": read_json_if_exists(exp_file),
        "comparison": read_json_if_exists(comp_file),
        "failures": read_json_if_exists(fail_file)
    }

@router.get("/ready")
async def get_readiness():
    """Readiness probe: Validates backend configuration, vector store, storage dirs, and DB registry."""
    from app.core.config import DATA_DIR, FAISS_DIR, STORAGE_DIR, DEFAULT_LLM_MODEL
    try:
        registry_ok = os.path.exists(STORAGE_DIR)
        faiss_ok = os.path.exists(FAISS_DIR)
        data_ok = os.path.exists(DATA_DIR)
        
        ready = registry_ok and data_ok
        return {
            "status": "ready" if ready else "not_ready",
            "components": {
                "storage_directory": registry_ok,
                "data_directory": data_ok,
                "faiss_index_exists": faiss_ok,
            },
            "active_model": DEFAULT_LLM_MODEL
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")

@router.get("/models")
async def get_models():
    """Get the list of active local models from Ollama."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            return {"online": True, "models": [m["name"] for m in models_data]}
    except Exception:
        pass
    return {"online": False, "models": []}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    """Upload a syllabus PDF file, save it to disk, and trigger re-indexing."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(DATA_DIR, file.filename)

    try:
        content = await file.read()
        checksum = calculate_file_checksum(content)

        metadata = load_metadata()
        existing_doc = metadata.get(file.filename, {})
        is_duplicate = existing_doc.get("checksum") == checksum and os.path.exists(file_path)

        with open(file_path, "wb") as buffer:
            buffer.write(content)

        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = max(round(file_size_bytes / (1024 * 1024), 2), 0.01)

        db, num_chunks = rebuild_vector_store(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            force_rebuild=False
        )

        return {
            "success": True,
            "filename": file.filename,
            "size": f"{file_size_mb} MB",
            "chunks": num_chunks,
            "checksum": checksum,
            "duplicate": is_duplicate
        }
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error indexing document: {str(e)}")

@router.get("/documents")
async def get_documents():
    """List all currently indexed syllabus files and their metadata."""
    metadata = load_metadata()
    docs_list = [
        {
            "filename": filename,
            "size": info.get("size", "Unknown size"),
            "indexed_at": info.get("indexed_at", "N/A")
        }
        for filename, info in metadata.items()
    ]
    return {"documents": docs_list}

from app.services.jobs import get_job_manager
from app.services.registry import DocumentRegistry
from app.services.manifest import IndexManifest
from app.rag.ingestion import delete_document_with_registry

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of an ingestion background job."""
    job_mgr = get_job_manager()
    job = job_mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "document_name": job["document_name"],
        "progress": job.get("progress", 0.0),
        "error": job.get("error_message")
    }

@router.get("/documents/{doc_name}/versions")
async def get_document_versions(doc_name: str):
    """Get version history for a specific document."""
    registry = DocumentRegistry()
    versions = registry.get_document_versions(doc_name)
    if not versions:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document_name": doc_name, "versions": versions}

@router.delete("/documents/{doc_name}")
async def delete_document(doc_name: str):
    """Delete a document from indexing database and rebuild index."""
    file_path = os.path.join(DATA_DIR, doc_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        db, num_chunks = delete_document_with_registry(doc_name)
        return {
            "success": True,
            "message": f"Successfully deleted {doc_name}.",
            "remaining_chunks": num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding database: {str(e)}")

@router.post("/reset")
async def reset_database():
    """Clear all documents, vector store index, metadata, registry, manifest, and jobs."""
    try:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        os.makedirs(DATA_DIR, exist_ok=True)

        if os.path.exists(FAISS_DIR):
            shutil.rmtree(FAISS_DIR)

        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)

        DocumentRegistry().reset_all()
        IndexManifest().clear()
        get_job_manager().clear_all()

        return {"success": True, "message": "Database successfully reset."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")

@router.get("/config")
async def get_app_config():
    """Returns safe, non-secret configuration information."""
    from app.core.config import get_safe_config
    return get_safe_config()

@router.get("/status")
async def get_status():
    """Return detailed health, index status, and safe operational metrics."""
    vector_store_active = os.path.exists(FAISS_DIR) and len(os.listdir(FAISS_DIR)) > 0
    db_size_bytes = 0
    if vector_store_active:
        for root, dirs, files in os.walk(FAISS_DIR):
            for f in files:
                db_size_bytes += os.path.getsize(os.path.join(root, f))

    db_size_mb = round(db_size_bytes / (1024 * 1024), 2)

    # Gather registry, manifest, and job metrics safely
    try:
        registry = DocumentRegistry()
        active_docs = registry.get_all_active_documents()
        doc_count = len(active_docs)
    except Exception:
        doc_count = 0

    try:
        manifest_data = IndexManifest().load()
        num_vectors = manifest_data.num_vectors
        num_bm25_docs = manifest_data.num_bm25_docs
        index_version = manifest_data.index_version
        embedding_model = manifest_data.embedding_model
        embedding_dim = manifest_data.embedding_dimension
        manifest_status = "healthy"
    except Exception:
        num_vectors = 0
        num_bm25_docs = 0
        index_version = "1.0.0"
        embedding_model = "all-MiniLM-L6-v2"
        embedding_dim = 384
        manifest_status = "uninitialized"

    try:
        job_mgr = get_job_manager()
        all_jobs = job_mgr.get_all_jobs()
        pending_jobs = sum(1 for j in all_jobs if j.status in ("QUEUED", "PROCESSING"))
    except Exception:
        pending_jobs = 0

    from app.core.config import DEFAULT_LLM_MODEL, ENVIRONMENT

    return {
        "active": vector_store_active,
        "size": f"{db_size_mb} MB",
        "raw_size_bytes": db_size_bytes,
        "environment": ENVIRONMENT,
        "indexed_documents_count": doc_count,
        "num_vectors": num_vectors,
        "num_bm25_docs": num_bm25_docs,
        "index_version": index_version,
        "embedding_model": embedding_model,
        "embedding_dimension": embedding_dim,
        "pending_jobs_count": pending_jobs,
        "manifest_status": manifest_status,
        "active_model": DEFAULT_LLM_MODEL
    }

@router.post("/query")
async def query_syllabus(payload: QueryRequest):
    """Streams a RAG-based answer for a query using Server-Sent Events (SSE)."""
    db = load_vector_store()

    async def event_generator():
        if db is None:
            yield {
                "event": "error",
                "data": json.dumps({"detail": "Please upload and process at least one syllabus PDF first."})
            }
            yield {"event": "done", "data": ""}
            return

        retrieved_docs, has_sufficient_evidence = retrieve_context(
            query=payload.query,
            db=db,
            k=payload.k,
            chat_history=payload.chat_history
        )

        t0 = datetime.datetime.now()
        from app.rag.citation_verifier import CitationVerifier
        from app.core.observability import log_rag_stage
        
        verifier = CitationVerifier(retrieved_docs=retrieved_docs)
        verified_citations = verifier.get_valid_sources()
        t_cit = (datetime.datetime.now() - t0).total_seconds() * 1000.0

        sources = [
            {
                "source": cit.document_name,
                "page": cit.page_number,
                "section": cit.section,
                "chapter": cit.chapter,
                "topic": cit.topic,
                "chunk_id": cit.chunk_id,
                "content": cit.excerpt
            }
            for cit in verified_citations
        ]

        log_rag_stage("CITATION_VERIFICATION", t_cit, {
            "retrieved_sources_count": len(retrieved_docs),
            "verified_sources_count": len(verified_citations),
            "has_sufficient_evidence": has_sufficient_evidence
        })

        yield {
            "event": "sources",
            "data": json.dumps(sources if has_sufficient_evidence else [])
        }

        try:
            generator = stream_answer(
                query=payload.query,
                retrieved_docs=retrieved_docs,
                llm_provider=payload.provider,
                model_name=payload.model,
                api_key=payload.api_key,
                temperature=payload.temperature,
                has_sufficient_evidence=has_sufficient_evidence
            )
            for token in generator:
                if token:
                    yield {
                        "event": "token",
                        "data": token
                    }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"detail": f"Model stream error: {str(e)}"})
            }

        yield {
            "event": "done",
            "data": ""
        }

    return EventSourceResponse(event_generator())

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
    rebuild_vector_store
)
from app.rag.pipeline import (
    load_vector_store,
    retrieve_context,
    stream_answer
)

router = APIRouter(prefix="/api")

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
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = max(round(file_size_bytes / (1024 * 1024), 2), 0.01)

        metadata = load_metadata()
        metadata[file.filename] = {
            "size": f"{file_size_mb} MB",
            "indexed_at": datetime.datetime.now().strftime("%b %d, %Y")
        }
        save_metadata(metadata)

        db, num_chunks = rebuild_vector_store(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        return {
            "success": True,
            "filename": file.filename,
            "size": f"{file_size_mb} MB",
            "chunks": num_chunks
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

@router.delete("/documents/{doc_name}")
async def delete_document(doc_name: str):
    """Delete a document from indexing database and rebuild index."""
    file_path = os.path.join(DATA_DIR, doc_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        os.remove(file_path)
        db, num_chunks = rebuild_vector_store()
        return {
            "success": True,
            "message": f"Successfully deleted {doc_name}.",
            "remaining_chunks": num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding database: {str(e)}")

@router.post("/reset")
async def reset_database():
    """Clear all documents, vector store index, and metadata."""
    try:
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        os.makedirs(DATA_DIR, exist_ok=True)

        if os.path.exists(FAISS_DIR):
            shutil.rmtree(FAISS_DIR)

        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)

        return {"success": True, "message": "Database successfully reset."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")

@router.get("/status")
async def get_status():
    """Return FAISS database status and index sizes."""
    vector_store_active = os.path.exists(FAISS_DIR) and len(os.listdir(FAISS_DIR)) > 0
    db_size_bytes = 0
    if vector_store_active:
        for root, dirs, files in os.walk(FAISS_DIR):
            for f in files:
                db_size_bytes += os.path.getsize(os.path.join(root, f))

    db_size_mb = round(db_size_bytes / (1024 * 1024), 2)
    return {
        "active": vector_store_active,
        "size": f"{db_size_mb} MB",
        "raw_size_bytes": db_size_bytes
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

        retrieved_docs = retrieve_context(payload.query, db, k=payload.k)

        sources = [
            {
                "source": doc.metadata.get("source", "Unknown Source"),
                "page": doc.metadata.get("page", "N/A"),
                "content": doc.page_content
            }
            for doc in retrieved_docs
        ]

        yield {
            "event": "sources",
            "data": json.dumps(sources)
        }

        try:
            generator = stream_answer(
                query=payload.query,
                retrieved_docs=retrieved_docs,
                llm_provider=payload.provider,
                model_name=payload.model,
                api_key=payload.api_key,
                temperature=payload.temperature
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

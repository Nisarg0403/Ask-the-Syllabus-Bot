import os
import shutil
import json
import datetime
import requests
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from typing import Optional

from rag_pipeline import (
    DOCS_DIR,
    FAISS_DIR,
    METADATA_FILE,
    load_metadata,
    save_metadata,
    rebuild_vector_store,
    load_vector_store,
    retrieve_context,
    stream_answer
)

app = FastAPI(title="Ask-the-Syllabus Bot API")

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # During development, allow all origins. Can be restricted to localhost:5173 later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/models")
async def get_models():
    """
    Get the list of active local models from Ollama.
    """
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models_data = response.json().get("models", [])
            return {"online": True, "models": [m["name"] for m in models_data]}
    except Exception:
        pass
    return {"online": False, "models": []}

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200)
):
    """
    Upload a syllabus PDF file, save it to disk, and trigger re-indexing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(DOCS_DIR, file.filename)
    
    try:
        # Save file contents
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate file size
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        if file_size_mb == 0.0:
            file_size_mb = 0.01

        # Update metadata JSON
        metadata = load_metadata()
        metadata[file.filename] = {
            "size": f"{file_size_mb} MB",
            "indexed_at": datetime.datetime.now().strftime("%b %d, %Y")
        }
        save_metadata(metadata)

        # Rebuild vector store
        db, num_chunks = rebuild_vector_store(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        return {
            "success": True,
            "filename": file.filename,
            "size": f"{file_size_mb} MB",
            "chunks": num_chunks
        }
    except Exception as e:
        # Clean up file if save/indexing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error indexing document: {str(e)}")

@app.get("/api/documents")
async def get_documents():
    """
    List all currently indexed syllabus files and their metadata.
    """
    metadata = load_metadata()
    docs_list = []
    for filename, info in metadata.items():
        docs_list.append({
            "filename": filename,
            "size": info.get("size", "Unknown size"),
            "indexed_at": info.get("indexed_at", "N/A")
        })
    return {"documents": docs_list}

@app.delete("/api/documents/{doc_name}")
async def delete_document(doc_name: str):
    """
    Delete a document from indexing database and rebuild index.
    """
    file_path = os.path.join(DOCS_DIR, doc_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        os.remove(file_path)
        
        # Rebuild database with remaining documents
        db, num_chunks = rebuild_vector_store()
        
        return {
            "success": True,
            "message": f"Successfully deleted {doc_name}.",
            "remaining_chunks": num_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding database: {str(e)}")

@app.post("/api/reset")
async def reset_database():
    """
    Clear all documents, vector store index, and metadata.
    """
    try:
        # Clear docs directory
        if os.path.exists(DOCS_DIR):
            shutil.rmtree(DOCS_DIR)
        os.makedirs(DOCS_DIR, exist_ok=True)

        # Clear FAISS index
        if os.path.exists(FAISS_DIR):
            shutil.rmtree(FAISS_DIR)

        # Clear metadata file
        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)

        return {"success": True, "message": "Database successfully reset."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting database: {str(e)}")

@app.get("/api/status")
async def get_status():
    """
    Return FAISS database status and index sizes.
    """
    vector_store_active = os.path.exists(FAISS_DIR)
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

class QueryPayload:
    def __init__(self, query: str, provider: str, model: str, api_key: Optional[str] = None, chunk_size: int = 1024, chunk_overlap: int = 200, k: int = 4, temperature: float = 0.2):
        self.query = query
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k = k
        self.temperature = temperature

@app.post("/api/query")
async def query_syllabus(payload: dict):
    """
    Streams a RAG-based answer for a query using Server-Sent Events (SSE).
    """
    query = payload.get("query")
    provider = payload.get("provider", "Ollama")
    model = payload.get("model")
    api_key = payload.get("api_key")
    k = payload.get("k", 4)
    temperature = payload.get("temperature", 0.2)

    if not query:
        raise HTTPException(status_code=400, detail="Query string is required.")
    if not model:
        raise HTTPException(status_code=400, detail="Model name is required.")

    # Load vector store
    db = load_vector_store()

    async def event_generator():
        if db is None:
            yield {
                "event": "error",
                "data": json.dumps({"detail": "Please upload and process at least one syllabus PDF first."})
            }
            yield {"event": "done", "data": ""}
            return

        # 1. Retrieve Chunks
        retrieved_docs = retrieve_context(query, db, k=k)
        
        # Format sources citation details
        sources = []
        for doc in retrieved_docs:
            sources.append({
                "source": doc.metadata.get("source", "Unknown Source"),
                "page": doc.metadata.get("page", "N/A"),
                "content": doc.page_content
            })
        
        # Yield sources as the first SSE message
        yield {
            "event": "sources",
            "data": json.dumps(sources)
        }

        # 2. Run LLM stream
        try:
            generator = stream_answer(
                query=query,
                retrieved_docs=retrieved_docs,
                llm_provider=provider,
                model_name=model,
                api_key=api_key,
                temperature=temperature
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
            
        # Signal completion
        yield {
            "event": "done",
            "data": ""
        }

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

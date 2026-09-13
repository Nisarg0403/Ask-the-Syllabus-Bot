import os
import io
import time
import shutil
import json
import hashlib
import datetime
import re
from typing import Any, List, Dict, Tuple, Optional, Union
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from app.core.config import DATA_DIR, FAISS_DIR, METADATA_FILE, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from app.core.observability import log_ingestion_stage, log_job_event, log_error_event
from app.rag.embeddings import get_embeddings
from app.rag.bm25 import get_bm25_index
from app.services.registry import DocumentRegistry
from app.services.manifest import IndexManifest
from app.services.jobs import INGESTION_LOCK, get_job_manager

def calculate_file_checksum(file_input: Union[bytes, str]) -> str:
    """Calculates SHA-256 checksum from bytes or file path/string."""
    if isinstance(file_input, str):
        if os.path.exists(file_input) and os.path.isfile(file_input):
            with open(file_input, "rb") as f:
                content = f.read()
        else:
            content = file_input.encode("utf-8")
    else:
        content = file_input
    return hashlib.sha256(content).hexdigest()

def detect_structure(text: str) -> Dict[str, str]:
    """Detects section, chapter, and topic headings from chunk text."""
    section, chapter, topic = "General", "General", "General"
    lines = text.split("\n")
    for line in lines[:5]:
        line_clean = line.strip()
        if not line_clean:
            continue
        if re.match(r'^(Module|Chapter|Unit)\s+\d+', line_clean, re.I):
            chapter = line_clean
        elif re.match(r'^(Section|Part|Grading Policy)', line_clean, re.I):
            section = line_clean
        elif re.match(r'^\d+\.\d+\s+[A-Z]', line_clean):
            topic = line_clean
    return {"section": section, "chapter": chapter, "topic": topic}

def extract_section_headers(text: str) -> Tuple[str, str, str]:
    """Returns (section, chapter, topic) tuple for backward test compatibility."""
    res = detect_structure(text)
    return res["section"], res["chapter"], res["topic"]

def structure_aware_split(
    documents: List[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> List[Document]:
    """Structure-aware Document Splitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = splitter.split_documents(documents)
    enriched = []
    for idx, c in enumerate(chunks):
        st = detect_structure(c.page_content)
        checksum = c.metadata.get("document_checksum") or "00000000"
        page = c.metadata.get("page", 1)
        chunk_id = f"{checksum[:8]}_p{page}_c{idx+1}"
        c.metadata.update(st)
        c.metadata["chunk_id"] = chunk_id
        enriched.append(c)
    return enriched

def extract_text_from_pdf_bytes(pdf_bytes: bytes, filename: str, checksum: str) -> Tuple[List[Document], int]:
    """
    Extracts text page-by-page from raw PDF bytes.
    Returns (list of Document objects with rich metadata, page_count).
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    docs = []
    page_count = len(reader.pages)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "page": i + 1,
                    "document_name": filename,
                    "document_checksum": checksum,
                    "page_number": i + 1
                }
            ))
    return docs, page_count

def extract_text_from_pdf(pdf_path: str, filename: str) -> List[Document]:
    """Legacy helper for file path extraction."""
    if not os.path.exists(pdf_path):
        return []
    with open(pdf_path, "rb") as f:
        content = f.read()
    checksum = calculate_file_checksum(content)
    docs, _ = extract_text_from_pdf_bytes(content, filename, checksum)
    return docs

def load_metadata() -> Dict[str, Dict]:
    """Loads document indexing metadata from storage JSON."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_metadata(metadata: Dict[str, Dict]) -> None:
    """Saves document indexing metadata to storage JSON."""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

async def run_ingestion_pipeline(
    pdf_bytes: bytes,
    document_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    custom_index_dir: Optional[str] = None,
    registry: Optional[DocumentRegistry] = None,
    manifest: Optional[IndexManifest] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Incremental Document Ingestion Pipeline:
    1. Compute SHA-256 Checksum
    2. Check Document Registry for duplicate or new version
    3. Extract text page-by-page
    4. Structure-aware chunking & rich metadata assignment
    5. Compute embeddings & incrementally update FAISS vector store
    6. Update BM25 sparse index
    7. Atomically persist Document Registry & Index Manifest
    """
    target_faiss_dir = custom_index_dir or FAISS_DIR
    reg = registry or DocumentRegistry()
    man = manifest or IndexManifest()

    # 1. SHA-256 Checksum Stage
    t0 = time.time()
    checksum = calculate_file_checksum(pdf_bytes)
    file_size_bytes = len(pdf_bytes)
    file_size_mb = max(round(file_size_bytes / (1024 * 1024), 2), 0.01)
    size_str = f"{file_size_mb} MB"
    t_chk = (time.time() - t0) * 1000.0
    log_ingestion_stage(document_name, "CHECKSUM", t_chk, {"checksum": checksum}, job_id=job_id)

    with INGESTION_LOCK:
        # Check duplicate content across registry
        existing_version = reg.get_latest_version(document_name)
        if existing_version and existing_version.get("checksum_sha256") == checksum:
            log_ingestion_stage(document_name, "COMPLETED", 0.0, {"status": "DUPLICATE"}, job_id=job_id)
            return {
                "status": "DUPLICATE",
                "document_name": document_name,
                "version_number": existing_version["version_number"],
                "checksum": checksum,
                "chunks": existing_version["chunk_count"],
                "message": f"Document {document_name} with checksum {checksum[:8]} is already indexed."
            }

        # 2. Registration Stage
        t0 = time.time()
        doc_id = reg.get_or_create_document(document_name)
        log_ingestion_stage(document_name, "REGISTRATION", (time.time() - t0) * 1000.0, {"document_id": doc_id}, job_id=job_id)

        # 3. PDF Extraction Stage
        t0 = time.time()
        page_docs, page_count = extract_text_from_pdf_bytes(pdf_bytes, document_name, checksum)
        if not page_docs:
            raise ValueError(f"No extractable text found in PDF: {document_name}")
        log_ingestion_stage(document_name, "PDF_EXTRACTION", (time.time() - t0) * 1000.0, {"page_count": page_count}, job_id=job_id)

        # 4. Structure-Aware Chunking Stage
        t0 = time.time()
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        raw_chunks = splitter.split_documents(page_docs)

        # Enrich chunk metadata
        enriched_chunks = []
        for idx, chunk in enumerate(raw_chunks):
            struct_info = detect_structure(chunk.page_content)
            chunk_id = f"{checksum[:8]}_chunk_{idx+1}"
            chunk.metadata.update({
                "document_id": doc_id,
                "document_name": document_name,
                "document_checksum": checksum,
                "chunk_id": chunk_id,
                "section": struct_info["section"],
                "chapter": struct_info["chapter"],
                "topic": struct_info["topic"],
                "source": document_name,
                "page": chunk.metadata.get("page", 1)
            })
            enriched_chunks.append(chunk)

        chunk_count = len(enriched_chunks)
        log_ingestion_stage(document_name, "CHUNKING", (time.time() - t0) * 1000.0, {"chunk_count": chunk_count}, job_id=job_id)

        # 5. Embedding & FAISS Update Stage
        t0 = time.time()
        embeddings = get_embeddings()
        if os.path.exists(target_faiss_dir) and len(os.listdir(target_faiss_dir)) > 0:
            db = FAISS.load_local(target_faiss_dir, embeddings, allow_dangerous_deserialization=True)
            db.add_documents(enriched_chunks)
        else:
            db = FAISS.from_documents(enriched_chunks, embeddings)
        db.save_local(target_faiss_dir)
        t_faiss = (time.time() - t0) * 1000.0
        log_ingestion_stage(document_name, "FAISS_UPDATE", t_faiss, {"chunks_added": chunk_count}, job_id=job_id)

        # 6. BM25 Update Stage
        t0 = time.time()
        bm25_index = get_bm25_index()
        bm25_index.add_documents(enriched_chunks)
        t_bm25 = (time.time() - t0) * 1000.0
        log_ingestion_stage(document_name, "BM25_UPDATE", t_bm25, {"bm25_doc_count": len(bm25_index.documents)}, job_id=job_id)

        # 7. Registry & Manifest Update Stage
        t0 = time.time()
        doc_id, version_id, version_number = reg.add_version(
            document_name=document_name,
            checksum=checksum,
            file_size=size_str,
            page_count=page_count,
            chunk_count=chunk_count,
            status="COMPLETED"
        )
        
        # Save legacy metadata for backward compatibility
        legacy_meta = load_metadata()
        legacy_meta[document_name] = {
            "checksum": checksum,
            "size": size_str,
            "indexed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_metadata(legacy_meta)

        # Update persistent Index Manifest
        total_vectors = db.index.ntotal if hasattr(db, "index") and hasattr(db.index, "ntotal") else chunk_count
        man.update(
            num_vectors=total_vectors,
            num_bm25_docs=len(bm25_index.documents),
            document_ids=[doc_id],
            version_ids=[version_id],
            checksums=[checksum]
        )
        t_meta = (time.time() - t0) * 1000.0
        log_ingestion_stage(document_name, "MANIFEST_UPDATE", t_meta, {"version_number": version_number}, job_id=job_id)

        log_ingestion_stage(document_name, "COMPLETED", (t_chk + t_faiss + t_bm25 + t_meta), {
            "status": "COMPLETED",
            "version_number": version_number
        }, job_id=job_id)

        return {
            "status": "COMPLETED",
            "document_name": document_name,
            "document_id": doc_id,
            "version_id": version_id,
            "version_number": version_number,
            "checksum": checksum,
            "chunks": chunk_count,
            "size": size_str
        }

async def process_background_ingestion(
    job_id: str,
    pdf_bytes: bytes,
    document_name: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    custom_index_dir: Optional[str] = None,
    registry: Optional[DocumentRegistry] = None,
    manifest: Optional[IndexManifest] = None,
    job_manager = None
):
    """Background task wrapper managing job state transitions & errors."""
    job_mgr = job_manager or get_job_manager()
    job_mgr.update_job(job_id, "PROCESSING", progress=0.2)
    log_job_event(job_id, document_name, "PROCESSING")

    t0 = time.time()
    try:
        res = await run_ingestion_pipeline(
            pdf_bytes=pdf_bytes,
            document_name=document_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            custom_index_dir=custom_index_dir,
            registry=registry,
            manifest=manifest,
            job_id=job_id
        )
        duration_ms = (time.time() - t0) * 1000.0
        job_mgr.update_job(job_id, "COMPLETED", progress=1.0)
        log_job_event(job_id, document_name, "COMPLETED", duration_ms=duration_ms)
    except Exception as e:
        duration_ms = (time.time() - t0) * 1000.0
        err_msg = str(e)
        job_mgr.update_job(job_id, "FAILED", error_message=err_msg)
        log_job_event(job_id, document_name, "FAILED", duration_ms=duration_ms, error=err_msg)
        log_error_event(f"background_job_{job_id}", e)

def rebuild_vector_store(chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP, force_rebuild: bool = False) -> Tuple[Optional[FAISS], int]:
    """Rebuilds vector store from DATA_DIR documents."""
    if not os.path.exists(DATA_DIR):
        return None, 0

    all_docs = []
    metadata = load_metadata()
    active_filenames = []

    for filename in os.listdir(DATA_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(DATA_DIR, filename)
            docs = extract_text_from_pdf(pdf_path, filename)
            all_docs.extend(docs)
            active_filenames.append(filename)

    metadata = {k: v for k, v in metadata.items() if k in active_filenames}
    save_metadata(metadata)

    if not all_docs:
        if os.path.exists(FAISS_DIR):
            shutil.rmtree(FAISS_DIR)
        return None, 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = splitter.split_documents(all_docs)
    embeddings = get_embeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(FAISS_DIR)

    bm25_index = get_bm25_index()
    bm25_index.clear()
    bm25_index.add_documents(chunks)

    return db, len(chunks)

def delete_document_with_registry(document_name: str) -> Tuple[Optional[FAISS], int]:
    """Deletes document from file storage, registry, manifest, and rebuilds FAISS & BM25."""
    with INGESTION_LOCK:
        file_path = os.path.join(DATA_DIR, document_name)
        if os.path.exists(file_path):
            os.remove(file_path)

        reg = DocumentRegistry()
        reg.delete_document(document_name)

        legacy_meta = load_metadata()
        if document_name in legacy_meta:
            del legacy_meta[document_name]
            save_metadata(legacy_meta)

        db, num_chunks = rebuild_vector_store()

        man = IndexManifest()
        if db and num_chunks > 0:
            man.update(
                num_vectors=db.index.ntotal if hasattr(db, "index") and hasattr(db.index, "ntotal") else num_chunks,
                num_bm25_docs=num_chunks
            )
        else:
            man.clear()

        return db, num_chunks

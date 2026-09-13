import os
import shutil
import json
from typing import List, Dict, Tuple, Optional
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from app.core.config import DATA_DIR, FAISS_DIR, METADATA_FILE
from app.rag.embeddings import get_embeddings

def extract_text_from_pdf(pdf_path: str, filename: str) -> List[Document]:
    """
    Extracts text page-by-page from a PDF file path and returns
    a list of LangChain Document objects with page metadata.
    """
    reader = PdfReader(pdf_path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            docs.append(Document(
                page_content=text,
                metadata={"source": filename, "page": i + 1}
            ))
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

def rebuild_vector_store(chunk_size: int = 1000, chunk_overlap: int = 200) -> Tuple[Optional[FAISS], int]:
    """
    Rebuilds the FAISS database using all PDF files in the documents directory.
    Returns (FAISS instance, total chunk count).
    """
    if os.path.exists(FAISS_DIR):
        shutil.rmtree(FAISS_DIR)

    all_docs = []
    metadata = load_metadata()
    active_filenames = []

    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(DATA_DIR, filename)
                docs = extract_text_from_pdf(pdf_path, filename)
                all_docs.extend(docs)
                active_filenames.append(filename)

    # Filter metadata for currently present files
    metadata = {k: v for k, v in metadata.items() if k in active_filenames}
    save_metadata(metadata)

    if not all_docs:
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
    return db, len(chunks)

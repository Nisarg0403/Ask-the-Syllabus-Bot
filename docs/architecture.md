# 🏛️ Ask-the-Syllabus Bot — System Architecture

The **Ask-the-Syllabus Bot** architecture is engineered for low latency, zero-hallucination grounded retrieval, and multi-provider flexibility.

---

## High-Level Component Diagram

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|                     React (Vite) + Tailwind CSS + Lucide Icons                    |
+------------------------------------------+----------------------------------------+
                                           |
                                           | HTTP REST (Upload / Status) & SSE Stream
                                           v
+-----------------------------------------------------------------------------------+
|                                  FASTAPI BACKEND                                  |
|                         `app/main.py` + `app/api/routes.py`                       |
+--------------------+-------------------------------------+------------------------+
                     |                                     |
                     v                                     v
       +---------------------------+             +-------------------+
       | Document Ingestion Engine |             | Vector Retriever  |
       |  - PyPDF Parser           |             |  - Hugging Face   |
       |  - Recursive Text Split   |             |    MiniLM-L6-v2   |
       +-------------+-------------+             |  - FAISS Store    |
                     |                           +---------+---------+
                     v                                     |
            +-----------------+                            | Relevant Chunks
            | Storage & Data  |                            v
            | data/documents/ |                  +-------------------+
            | storage/faiss/  |                  | Prompt Generator  |
            +-----------------+                  +---------+---------+
                                                           |
                                                           v
                                                 +-------------------+
                                                 | LLM Provider      |
                                                 | - Ollama (Local)  |
                                                 | - OpenRouter      |
                                                 +-------------------+
```

---

## Backend Subsystems (`backend/app/`)

### 1. `core/` (Configuration & Environment)
Centralizes system paths (`DATA_DIR`, `STORAGE_DIR`, `FAISS_DIR`) and model parameters. Environment variables are loaded dynamically with sensible defaults.

### 2. `rag/` (Retrieval-Augmented Generation Engine)
- **`embeddings.py`**: Initializes local Hugging Face `all-MiniLM-L6-v2` embedding pipeline with automatic GPU CUDA acceleration fallback to CPU.
- **`ingestion.py`**: Page-by-page PDF extraction using `pypdf`, chunk splitting using `RecursiveCharacterTextSplitter`, metadata persistence, and index building.
- **`pipeline.py`**: Local FAISS vector search, similarity ranking, prompt context assembly, and SSE streaming token generation.

### 3. `services/` (Model Provider Layer)
- **`llm.py`**: Decoupled LLM factory routing requests between local Ollama instances (`ChatOllama`) and OpenRouter cloud APIs (`ChatOpenAI`).

### 4. `api/` (HTTP & SSE Interface)
Exposes REST endpoints for uploading documents, querying vector status, resetting knowledge base, and streaming answers via Server-Sent Events (`EventSourceResponse`).

---

## Storage & Data Layout (`storage/` & `data/`)

- `data/documents/`: Contains active PDF syllabus files currently indexed.
- `data/sample/`: Contains reference/demo syllabus PDFs.
- `storage/faiss/`: Holds serialized FAISS index files (`index.faiss`, `index.pkl`).
- `storage/indexed_documents.json`: Stores document metadata (size, upload timestamp, page count).

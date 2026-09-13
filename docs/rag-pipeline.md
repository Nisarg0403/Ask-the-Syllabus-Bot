# 🔄 The 10-Stage Grounded RAG Pipeline

The **Ask-the-Syllabus Bot** uses a strict 10-stage RAG execution pipeline designed to deliver fast, accurate, and verifiable answers.

---

```
[1] Document Ingestion
         │
         ▼
[2] PDF Extraction (pypdf)
         │
         ▼
[3] Text Cleaning
         │
         ▼
[4] Recursive Chunking (1000 chars / 200 overlap)
         │
         ▼
[5] Local Vector Embedding Generation (all-MiniLM-L6-v2)
         │
         ▼
[6] FAISS Index Storage
         │
         ▼
[7] User Query Processing & Vector Similarity Search
         │
         ▼
[8] Context Assembly with Document & Page Metadata
         │
         ▼
[9] LLM Stream Generation (Ollama Qwen3 / Llama3)
         │
         ▼
[10] Grounded Response with Page Citations (SSE)
```

---

## Detailed Stage Breakdown

### 1. Document Ingestion
Users upload PDF syllabi via the web interface or CLI (`scripts/ingest.py`). The files are placed in `data/documents/`.

### 2. PDF Extraction
`pypdf.PdfReader` parses documents page by page, preserving page numbers in chunk metadata.

### 3. Text Cleaning
Strips empty lines, normalizes whitespace, and filters unreadable binary contents.

### 4. Chunking
`RecursiveCharacterTextSplitter` divides text into overlapping chunks (default: `chunk_size=1000`, `chunk_overlap=200`). This ensures sentence context is preserved across split boundaries.

### 5. Vector Embeddings
Each chunk is mapped to a 384-dimensional dense vector using Hugging Face's `all-MiniLM-L6-v2`. Embeddings are normalized for cosine similarity distance.

### 6. FAISS Indexing
Vector representations along with Document payloads are saved locally in `storage/faiss/`.

### 7. Retrieval
For a user query, top-$k$ (default: $k=4$) most similar chunks are retrieved using L2 / Cosine vector distance in FAISS.

### 8. Context Construction
Retrieved chunks are structured into a grounded system prompt:
```text
Context:
[Source: CS101_Syllabus.pdf, Page: 4]
Grading criteria: Midterm 30%, Final Exam 40%, Homework 30%.
```

### 9. LLM Execution
The prompt is fed into Ollama (Qwen3 / Llama3) or OpenRouter API with a low temperature ($0.2$) to minimize hallucination.

### 10. Streaming & Citations
Response tokens are streamed to the frontend in real time via Server-Sent Events (SSE). Source document names, page numbers, and snippet previews are emitted as an initial `sources` event payload.

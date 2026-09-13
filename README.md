# Ask-the-Syllabus Bot ⚡ (Production-Grade RAG System)

> A modular, production-oriented Retrieval-Augmented Generation (RAG) academic assistant for parsing, indexing, and querying course syllabi with strict grounding, precise page-level citations, and real-time streaming answers.

---

## 📌 Problem Statement

Students and educators frequently spend valuable time searching through long, multi-page course syllabi, policy PDFs, and academic schedules to locate critical details (such as grading breakdowns, exam dates, office hours, and assignment policies). Traditional keyword searches fail when queries do not match exact wording. Standard Large Language Models (LLMs) often hallucinate policies or state incorrect information when ungrounded.

**Ask-the-Syllabus Bot** solves this by embedding uploaded academic documents into a local vector index (FAISS), retrieving exact context passages, and synthesizing precise, grounded responses with verifiable page citations using local or cloud LLMs.

---

## ✨ Key Features

- ⚡ **Real-Time Token Streaming**: Server-Sent Events (SSE) stream responses instantaneously from LLMs.
- 🎯 **Strict Grounding & Citation Accordion**: Every answer displays the exact source filename, page number, and text snippet used to generate it.
- 🔀 **Dual LLM Execution Modes**:
  - **Local & Private**: Native integration with **Ollama** (Qwen3 / Llama 3) for 100% offline, privacy-first inference.
  - **Cloud Integration**: Compatible with **OpenRouter** API (Llama 3, Claude 3.5, Gemini 1.5, DeepSeek).
- 🧠 **Zero Cost Local Vector Embeddings**: Uses Hugging Face's `all-MiniLM-L6-v2` locally for fast 384-dimensional vector indexing.
- 🎛️ **On-the-Fly RAG Hyperparameter Tuning**: Dynamically adjust chunk size, overlap, top-$k$ document retrieval count, and temperature via the UI sidebar.
- 🎨 **Modern Split-Pane UI**: Dark/Light mode theme, glassmorphic layout, drag-and-drop PDF dropzone, and real-time status diagnostics.

---

## 🏗️ System Architecture

```
                                +-------------------+
                                | Academic PDFs     |
                                +---------+---------+
                                          |
                                          v
+-------------------+           +---------+---------+
|  React (Vite) UI  |<-- (SSE) -|  FastAPI Backend  |
+---------+---------+           +---------+---------+
          |                               |
          | (REST Upload & Query)         v
          +-------------------->+---------+---------+
                                | Document Parser   |
                                | (PyPDF / Splitter)|
                                +---------+---------+
                                          |
                                          v
                                +---------+---------+
                                | Local Embeddings  |
                                | (MiniLM-L6-v2)    |
                                +---------+---------+
                                          |
                                          v
                                +---------+---------+
                                | FAISS Vector Store|
                                +-------------------+
```

For full system architecture details, view [`docs/architecture.md`](docs/architecture.md).

---

## 🔄 10-Stage RAG Pipeline

1. **Document Ingestion**: Upload academic PDFs via web UI or CLI.
2. **Text Extraction**: Page-level parsing using `pypdf`.
3. **Text Cleaning**: Whitespace normalization and header cleanup.
4. **Recursive Chunking**: Splitting into overlapping character blocks (`chunk_size=1000`, `chunk_overlap=200`).
5. **Vector Embedding**: Mapping chunks to 384-dim dense vectors (`all-MiniLM-L6-v2`).
6. **FAISS Storage**: Persisting index locally in `storage/faiss/`.
7. **Query Processing**: Vector similarity search for top-$k$ context chunks.
8. **Context Assembly**: Constructing grounded prompts with metadata citations.
9. **LLM Generation**: Streaming answers via Ollama (Qwen3) or OpenRouter API.
10. **Citation Rendering**: Displaying grounded text snippets with page numbers.

For detailed pipeline documentation, view [`docs/rag-pipeline.md`](docs/rag-pipeline.md).

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, SSE-Starlette
- **RAG & ML Engine**: LangChain, FAISS (`faiss-cpu`), Hugging Face `sentence-transformers` (`all-MiniLM-L6-v2`), PyTorch, PyPDF
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons
- **Local LLM Infrastructure**: Ollama (Qwen3 / Llama 3)

---

## 📂 Project Structure

```
ask-the-syllabus-bot/
├── backend/
│   ├── app/
│   │   ├── api/routes.py         # REST & SSE API Endpoints
│   │   ├── core/config.py        # Path & Model Configuration
│   │   ├── models/schemas.py     # Pydantic Schemas
│   │   ├── rag/                  # Embeddings, Ingestion & Retrieval Pipeline
│   │   ├── services/llm.py       # Ollama & OpenRouter Factory
│   │   └── main.py               # FastAPI App Entrypoint
│   ├── tests/test_api.py         # FastAPI Integration Tests
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/           # Header, Sidebar, KnowledgeBase, ChatSection
│   │   ├── services/api.js       # Centralized API Client
│   │   ├── utils/markdown.js     # Text Formatter Utility
│   │   ├── App.jsx, main.jsx, index.css, App.css
│   ├── package.json, vite.config.js, README.md
├── data/
│   ├── documents/                # Active Syllabus PDFs
│   └── sample/                   # Reference Sample Syllabi
├── storage/
│   └── faiss/                    # Vector Index Storage
├── scripts/
│   ├── ingest.py                 # CLI Batch Ingestion Tool
│   ├── rebuild_index.py          # Force Index Rebuild Tool
│   └── evaluate.py               # Benchmark Evaluation Tool
├── tests/
│   ├── test_retrieval.py         # FAISS Vector Search Unit Tests
│   └── test_rag.py               # Context Builder Unit Tests
├── docs/
│   ├── architecture.md
│   ├── rag-pipeline.md
│   ├── evaluation.md
│   └── project-plan.md
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **[Ollama](https://ollama.com/)** (Optional, for offline execution)

### 2. Ollama & Qwen3 Setup (Local Execution)
Install Ollama and pull the recommended model:
```bash
ollama pull qwen2.5:7b
# or
ollama pull llama3:8b
```

### 3. Backend Setup
```bash
# Clone the repository
git clone https://github.com/your-username/ask-the-syllabus-bot.git
cd ask-the-syllabus-bot

# Install Python dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server
python -m uvicorn backend.app.main:app --reload --port 8000
```
*API interactive documentation will be live at `http://127.0.0.1:8000/docs`.*

### 4. Frontend Setup
```bash
# Open a new terminal and navigate to frontend/
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
*Web application will be accessible at `http://localhost:5173`.*

---

## 💻 Batch CLI Ingestion & Benchmark Scripts

### Ingest Documents via CLI
Place PDF syllabus files inside `data/documents/` and run:
```bash
python scripts/ingest.py --chunk-size 1000 --chunk-overlap 200
```

### Rebuild Vector Index
```bash
python scripts/rebuild_index.py
```

### Run Benchmark Evaluation
```bash
python scripts/evaluate.py --k 4
```

---

## 🧪 Running Automated Tests

Run the test suite across backend API endpoints and RAG retrieval pipelines:

```bash
# Run backend API tests
python -m unittest discover -s backend/tests

# Run RAG vector retrieval tests
python -m unittest discover -s tests
```

---

## 📊 Evaluation & Grounding

The system enforces strict grounding rules:
1. Questions directly supported by uploaded syllabi receive detailed answers with page citations.
2. Questions outside the uploaded context yield an explicit refusal: *"I cannot find the answer to this question in the provided documents."*

For complete evaluation methodology and benchmarks, see [`docs/evaluation.md`](docs/evaluation.md).

---

## 🚧 Limitations & Future Roadmap

### Current Limitations
- Supports text-based PDF extraction (`pypdf`); scanned image PDFs require an OCR pre-processing step.
- Single-node FAISS index storage.

### Planned Improvements
- [ ] **OCR Support**: Integration with `Tesseract` / `Unstructured` for scanned PDFs.
- [ ] **Hybrid Search**: Combining BM25 keyword matching with dense FAISS vector search.
- [ ] **Cross-Encoder Re-Ranking**: Cohere / BGE-Reranker integration.
- [ ] **Vector Database Migration**: Optional Qdrant / PgVector connector for enterprise scale.

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

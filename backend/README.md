# Ask-the-Syllabus Bot — Backend API

FastAPI backend service powering document parsing, Hugging Face embedding generation, FAISS vector indexing, and streaming RAG execution.

## 📁 Package Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes.py         # FastAPI endpoint handlers
│   ├── core/
│   │   └── config.py         # Path & model configuration
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response schemas
│   ├── rag/
│   │   ├── embeddings.py     # Sentence Transformers embeddings
│   │   ├── ingestion.py      # PDF parsing & FAISS index builder
│   │   └── pipeline.py       # Context retrieval & stream generator
│   ├── services/
│   │   └── llm.py            # Ollama & OpenRouter provider factory
│   └── main.py               # FastAPI application entrypoint
├── tests/
│   └── test_api.py           # Endpoint integration tests
├── requirements.txt
└── README.md
```

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run API Server
From the repository root (`GEN_AI`):
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
Or from inside `backend/`:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

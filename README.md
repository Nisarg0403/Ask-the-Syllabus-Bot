# Ask-the-Syllabus Bot ⚡ (Production-Grade RAG System)

A full-stack, enterprise-ready Retrieval-Augmented Generation (RAG) platform designed to parse, index, and query complex academic syllabi and documents with strict grounding, precise page-level citations, and real-time streaming answers.

Built with a high-performance **FastAPI** backend and a modern, reactive **React (Vite) + Tailwind CSS** frontend.

---

## ✨ Highlights & Key Features

- ⚡ **Real-Time SSE Streaming**: Low-latency token streaming powered by FastAPI and Server-Sent Events (SSE).
- 🎯 **Strict Grounding & Citation**: Verifiable response citations showing exact document sources, page numbers, and chunk previews to eliminate LLM hallucinations.
- 🔀 **Hybrid LLM Provider Support**:
  - **Local Execution**: Integrated with **Ollama** for 100% offline, privacy-first inference.
  - **Cloud Execution**: Integrated with **OpenRouter** API (Llama 3, Claude 3, Qwen, Gemini, etc.).
- 🧠 **Local Vector Embeddings**: Uses Hugging Face's `all-MiniLM-L6-v2` locally for zero API embedding costs and high accuracy.
- 🎨 **Modern Minimalist UI**: Responsive Dark/Light theme, glassmorphic layout, real-time chunk & server diagnostics indicator.
- ⚙️ **Configurable Hyperparameters**: Adjust chunk size, overlap, top-K retrieval count, and LLM temperature on the fly.

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

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS + Custom CSS Design System
- **Icons**: Lucide React / SVG Icons

### Backend
- **Framework**: FastAPI (Uvicorn ASGI server)
- **RAG Pipeline**: LangChain Ecosystem
- **Vector Index**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: HuggingFace Sentence Transformers (`all-MiniLM-L6-v2`)
- **LLM Integrations**: `langchain-ollama`, `langchain-openai` (via OpenRouter)

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- (Optional) [Ollama](https://ollama.com/) for local offline LLMs

### 2. Backend Setup
```bash
# Navigate to root directory
cd GEN_AI

# Install Python dependencies
pip install -r backend/requirements.txt

# Run the FastAPI backend server
python backend/main.py
```
*The backend API server will run at `http://127.0.0.1:8000`.*

### 3. Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev
```
*The frontend application will be accessible at `http://localhost:5173`.*

---

## 🧭 Production RAG Roadmap

This project is built to scale into a enterprise production RAG platform. Planned upgrades include:

- [ ] **Asynchronous Task Queue**: Offload document parsing and vector embedding tasks using Redis & Celery to prevent API blocking.
- [ ] **Managed Vector Database**: Migrate from local FAISS files to Qdrant/pgvector for real-time CRUD and multi-tenant scaling.
- [ ] **Advanced Retrieval Strategies**:
  - Hybrid Search (BM25 Keyword Search + Semantic Vector Search).
  - Cross-Encoder Re-Ranking (Cohere / BGE-Reranker).
- [ ] **Conversational Memory**: Stateful session management with Redis for multi-turn dialogue context.
- [ ] **Advanced Document Parsing**: Integration with `unstructured.io` / LlamaParse for complex tabular and multi-column PDF layouts.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

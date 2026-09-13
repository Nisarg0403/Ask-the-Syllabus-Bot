# Ask-the-Syllabus Bot - Version 1.0 Release Documentation

> **Version**: 1.0.0  
> **Date**: September 13, 2026  
> **System**: Production-Grade Retrieval-Augmented Generation (RAG) Academic Assistant  

---

## 📌 Executive Summary

**Ask-the-Syllabus Bot v1.0** is a full-stack, privacy-first Retrieval-Augmented Generation (RAG) application designed to assist students and educators in querying course syllabi, academic guidelines, and policy PDFs with 100% grounded accuracy and verifiable page-level citations.

This document provides a comprehensive breakdown of all features, architecture components, UI/UX enhancements, bug fixes, and API specifications implemented in **Version 1.0**.

---

## 🏗️ System Architecture & Technology Stack

```
+-----------------------------------------------------------------------+
|                            React (Vite) UI                            |
| (Sidebar, ChatThread, KnowledgeBase Modal, SettingsPanel, Auto-Scroll)|
+-----------------------------------+-----------------------------------+
                                    |
                            (REST / SSE Stream)
                                    |
                                    v
+-----------------------------------------------------------------------+
|                            FastAPI Backend                            |
|             (CORS, SSE EventSourceResponse, Modular Routes)           |
+-----------------+-----------------------------------+-----------------+
                  |                                   |
                  v                                   v
+-----------------------------------+   +-------------------------------+
|          RAG Pipeline             |   |         LLM Engine            |
|  • PyPDF Document Parsing         |   |  • Ollama (Qwen3 / Llama 3.2) |
|  • Recursive Character Splitter   |   |  • OpenRouter API (Cloud)     |
|  • MiniLM-L6-v2 Vector Embeddings |   +-------------------------------+
|  • FAISS CPU Vector Index Storage |
+-----------------------------------+
```

### Stack Breakdown
- **Frontend**: React 18, Vite 5, Tailwind CSS 3, Lucide React Icons.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic, SSE-Starlette.
- **RAG & ML Infrastructure**: LangChain Community, FAISS (`faiss-cpu`), Hugging Face `sentence-transformers` (`all-MiniLM-L6-v2`), PyPDF.
- **LLM Support**: Local inference via Ollama (`qwen3:8b`, `llama3.2:latest`) & Cloud inference via OpenRouter API.

---

## ✨ Comprehensive Features Implemented in Version 1.0

### 1. ⚡ 10-Stage RAG Pipeline
1. **Document Ingestion**: Upload academic PDFs via web UI dropzone or CLI script (`scripts/ingest.py`).
2. **Text Extraction**: Page-level extraction utilizing `pypdf`.
3. **Text Cleaning**: Whitespace normalization and header/footer cleanup.
4. **Recursive Chunking**: Configurable character chunking (`chunk_size=1000`, `chunk_overlap=200`).
5. **Vector Embedding**: Zero-cost local 384-dimensional vector embedding generation (`all-MiniLM-L6-v2`).
6. **FAISS Local Vector Index**: Local vector database persistence in `storage/faiss/`.
7. **Similarity Search**: Top-$k$ document passage retrieval ($k=1 \dots 10$).
8. **Context Assembly**: Prompt engineering with strict grounding instructions to eliminate hallucinations.
9. **SSE Token Streaming**: Real-time token streaming from LLM to frontend over Server-Sent Events.
10. **Page-Level Citations**: Exact file name, page number, and text snippet citations rendered per response.

---

### 2. 🎨 Modern Split-Pane Web Interface

* **Glassmorphic Responsive Design**: Sleek dark/light theme support with CSS variable design tokens.
* **Collapsible Left Sidebar**:
  * Brand header & system status indicators.
  * Local Ollama model selector dropdown.
  * RAG hyperparameter configuration modal trigger.
  * PDF file upload button with hidden file input.
  * Real-time FAISS storage size meter & **Clear Database** wipe trigger.
  * Dark / Light mode toggle switch.
* **Interactive Knowledge Base Modal**:
  * Drag-and-drop PDF dropzone with visual indexing progress bar.
  * Detailed list of active indexed syllabi displaying file size and indexing timestamp.
  * Individual file deletion with automatic FAISS index re-building.

---

### 3. 💬 Advanced Chat Thread & UX Enhancements

* **Conditional Home Screen Prompts**: Quick-start prompt chips (*"What topics are covered in Unit 3?"*, *"Explain backpropagation"*, *"Final module topics"*) appear on the initial empty home screen and automatically hide when a conversation begins to maximize vertical chat space.
* **Animated Thinking & Context Retrieval Loader**:
  * Shows a pulsing loader box with 3 bouncing dots (*"Thinking and retrieving context..."*) as soon as a query is submitted.
* **Real-time Answer Generation Indicator**:
  * Displays an inline active status (*"Generating answer..."*) with animated bouncing dots while tokens stream into the chat bubble.
* **Citations Displayed Strictly After Completion**:
  * The **"Grounded in X retrieved sources"** accordion is hidden during thinking and token streaming.
  * The accordion smoothly animates into view **only after the complete response has finished streaming**.
* **Query Autocompletion**:
  * Typing 2+ characters in the input bar triggers a popup displaying document-grounded syllabus questions.
* **Smooth Auto-Scroll**:
  * React `useEffect` hook ensures the chat container automatically scrolls to the bottom on new messages and streaming updates.

---

## 🛠️ Bug Fixes & Stability Improvements

1. **React Reference Error Fix**:
   * Fixed missing `UploadCloud` icon import in `frontend/src/components/ChatSection.jsx` that caused a dark blank screen runtime crash.
2. **Backend Execution Directory Fix**:
   * Resolved `ModuleNotFoundError: No module named 'app'` by standardizing execution from the `backend/` working directory (`python -m uvicorn app.main:app`).
3. **Ollama CUDA / Memory Overrun Graceful Recovery**:
   * Added clear diagnostic error reporting and model recommendations (`llama3.2:latest`) when local GPU VRAM allocation fails on Ollama.
4. **Clean Component Architecture**:
   * Modularized UI into focused components: `Header.jsx`, `Sidebar.jsx`, `ChatSection.jsx`, `ChatInput.jsx`, `KnowledgeBase.jsx`, `ModelSelector.jsx`, and `SettingsPanel.jsx`.

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/models` | Returns Ollama online status and list of pulled local models. |
| `POST` | `/api/upload` | Uploads a syllabus PDF, extracts text, and rebuilds the FAISS index. |
| `GET` | `/api/documents` | Lists all currently indexed documents and their metadata. |
| `DELETE` | `/api/documents/{doc_name}` | Deletes a document and updates the vector store. |
| `POST` | `/api/reset` | Resets the entire knowledge base, deletes raw files, and clears FAISS index. |
| `GET` | `/api/status` | Returns active status and raw/formatted storage size of FAISS vector database. |
| `POST` | `/api/query` | Executes RAG query and streams answer via Server-Sent Events (`event: sources`, `event: token`, `event: done`). |

---

## 💻 Setup & Execution Commands

### Backend Server
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Server
```bash
cd frontend
npm run dev
```

### Verification & Build
```bash
cd frontend
npm run build
```

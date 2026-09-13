# Ask-the-Syllabus Bot ⚡ (Production-Grade RAG System)

> A modular, production-grade Retrieval-Augmented Generation (RAG) academic assistant for parsing, indexing, and querying course syllabi with strict grounding, SHA-256 document versioning, hybrid dense/sparse retrieval, cross-encoder reranking, evidence abstention, and precise page-level citations.

---

## 📌 Problem Statement

Students and educators frequently spend valuable time searching through long, multi-page course syllabi, policy PDFs, and academic schedules to locate critical details (such as grading breakdowns, exam dates, office hours, and assignment policies). Traditional keyword searches fail when queries do not match exact wording. Standard Large Language Models (LLMs) often hallucinate policies or state incorrect information when ungrounded.

**Ask-the-Syllabus Bot** solves this by storing uploaded academic documents with SHA-256 checksum versioning, embedding chunks into a hybrid FAISS & BM25 retrieval pipeline, ranking candidates with Reciprocal Rank Fusion (RRF) and FlashRank cross-encoder reranking, validating evidence thresholds, and synthesizing precise, grounded responses with verifiable citations using Qwen3 / Ollama.

---

## ✨ Key Features

- ⚡ **Real-Time Token Streaming**: Server-Sent Events (SSE) stream responses instantaneously from LLMs.
- 🔀 **Hybrid Retrieval Pipeline**: FAISS dense vector search + BM25 sparse keyword search combined via Reciprocal Rank Fusion (RRF).
- 🎯 **FlashRank Re-Ranking & Evidence Gate**: Cross-encoder reranking with configurable evidence thresholding (`0.25`) for hallucination-free abstention on out-of-scope queries.
- 📜 **SHA-256 Checksum & Versioning Registry**: Persistent SQLite document registry tracking document identity, version increments, and duplicate prevention.
- ⚡ **Background Ingestion & Job Manager**: In-memory job manager (`QUEUED` → `PROCESSING` → `COMPLETED` / `FAILED`) with automatic crash recovery.
- 📊 **Index Manifest**: Persistent JSON index manifest storing embedding dimensions (384), vector counts, and model compatibility checks.
- 🛡️ **Citation Verification Engine**: Validates every inline citation against actual retrieved document content before delivery.
- 🔍 **Structured JSON Observability**: Request-ID (`X-Request-ID`) propagation, stage-by-stage telemetry, and secret masking.

---

## 🏗️ System Architecture

```
React (Vite) UI
      │
      ▼
FastAPI Gateway (Request ID & CORS)
      │
      ▼
Query Transformation (Normalization & Reference Resolution)
      │
      ├───► FAISS Dense Retrieval (all-MiniLM-L6-v2) ───┐
      │                                                ├──► RRF Fusion ──► FlashRank Reranker ──► Evidence Gate
      └───► BM25 Sparse Keyword Search ────────────────┘                                                │
                                                                                                        ▼
                                                                                            Qwen3 / Ollama Generator
                                                                                                        │
                                                                                                        ▼
                                                                                           Citation Verifier & SSE Stream
```

---

## 📊 Benchmark Evaluation Results

Evaluated against the **105-Question Academic Benchmark Dataset** (See [`version_2.md`](version_2.md) for full report & controlled experiment matrix):

| Metric | Baseline | Version 2.0 Production |
|---|---:|---:|
| **Recall@1** | 0.00% | **67.50%** |
| **Recall@3** | 0.00% | **96.88%** |
| **Recall@5** | 0.00% | **99.38%** |
| **Recall@10** | 0.00% | **99.38%** |
| **Precision@5** | 0.00% | **81.50%** |
| **MRR** | 0.00 | **0.8500** |
| **nDCG@5** | 0.00 | **0.8866** |
| **Abstention Accuracy** | 34.29% | **95.24%** |
| **False Answer Rate on evaluation benchmark** | 0.00% | **0.00%** |
| **False Abstention Rate** | 86.25% | **6.25%** |
| **Mean End-to-End RAG Latency** | 31.8ms | **47.25ms** |

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **[Ollama](https://ollama.com/)** (`ollama pull qwen3:8b`)

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run Unit Tests (72/72 passing)
python -m unittest discover -s tests -p "test_*.py"

# Start FastAPI backend
python -m uvicorn backend.app.main:app --reload --port 8000
```
*API Swagger documentation available at `http://127.0.0.1:8000/docs`.*

### 3. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
*Web application available at `http://localhost:5173`.*

---

## 🎬 Jury Demonstration Procedure

1. **Dashboard Load**: Open `http://localhost:5173/`. Verify status pill (`QWEN3:8B` online) and 0 console errors.
2. **Document Upload**: Click **Upload PDF** in sidebar, drag and drop `1. Final GenAI_200PS_Implementation GUIDE (1).pdf`. Observe background job status (`QUEUED` → `PROCESSING` → `COMPLETED`).
3. **Factual Grounded Query**: Ask: *"What are the tentative exam dates for the Generative AI Jury Examination?"* Observe real-time token stream and page 1 citation source drawer.
4. **Multi-Chunk / Cross-Doc Query**: Upload `sample_syllabus.pdf`. Ask: *"Compare the jury marking breakdown in the implementation guide with the company details of Hyperlink Infosystem."* Verify dual-document citations.
5. **Abstention Check**: Ask: *"What is the professor's personal bank account password?"* Observe evidence gate trigger: *"I couldn't find sufficient evidence in the uploaded documents to answer this question."*
6. **Version History**: Re-upload modified version of `sample_syllabus.pdf`. Open Knowledge Base modal and view incremented `version_number` (v2).

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

# Ask-the-Syllabus Bot — Production-Grade RAG Upgrade Plan

**Project:** Ask-the-Syllabus Bot (Topic 162 — RAG)  
**Target:** Production-oriented academic RAG application  
**Current baseline:** Version 1.0  
**Primary stack:** React + Vite + Tailwind, FastAPI, LangChain, FAISS, Sentence-Transformers, Ollama, Qwen3

---

## 1. Objective

Upgrade the current working Version 1.0 application into a robust, evaluated, maintainable, production-oriented RAG system without unnecessarily rebuilding working functionality.

The final system should demonstrate:

- reliable retrieval
- hybrid search
- reranking
- strong grounding
- abstention when evidence is insufficient
- verifiable citations
- multi-document reasoning
- objective evaluation
- observability
- security
- incremental document processing
- automated testing
- deployment readiness

**Core principle:** Do not add complexity merely to make the project look advanced. Every major component should be justified by measurable improvement.

---

# 2. Current Version 1.0 Baseline

The existing application already provides:

- React/Vite frontend
- FastAPI backend
- PDF upload and ingestion
- page-level PDF extraction
- text cleaning
- recursive character chunking
- Sentence-Transformer embeddings (`all-MiniLM-L6-v2`)
- FAISS local vector search
- configurable Top-K retrieval
- Ollama/local LLM inference
- Qwen3/Llama model support
- OpenRouter cloud-model support
- strict grounding prompt
- SSE token streaming
- page-level citations
- multi-document knowledge-base management
- document deletion and FAISS rebuild
- model selection
- RAG settings
- responsive chat UI
- knowledge-base status/document management

**Rule:** Preserve currently working behavior. Refactor incrementally rather than starting again.

---

# 3. Target Architecture

```text
React UI
   │
   │ REST + SSE
   ▼
FastAPI API
   │
   ▼
Query Processor
   ├── query normalization
   ├── conversation context
   └── query rewriting
   │
   ▼
Hybrid Retrieval
   ├── Dense Search / FAISS
   ├── BM25 / keyword search
   └── RRF fusion
   │
   ▼
Re-Ranker
   │
   ▼
Evidence / Relevance Gate
   │
   ├── sufficient evidence ──► LLM
   │                            │
   │                            ▼
   │                     Citation Verification
   │                            │
   │                            ▼
   │                    Answer + Citations
   │
   └── insufficient evidence ─► Abstention
```

Cross-cutting services:

```text
Evaluation
Logging
Observability
Caching
Security
Configuration
Testing
```

---

# 4. Phase 1 — Stabilize Version 1.0

Before adding advanced features:

- [ ] Audit the complete repository.
- [ ] Identify existing ingestion, retrieval, generation, citation, and UI components.
- [ ] Document current APIs.
- [ ] Add tests around currently working behavior.
- [ ] Establish a baseline benchmark.
- [ ] Record current latency and retrieval results.
- [ ] Confirm Ollama and cloud-provider model switching works.
- [ ] Confirm upload → index → query works.
- [ ] Confirm multi-document querying works.
- [ ] Confirm deletion works.
- [ ] Confirm unsupported questions do not cause obvious hallucinations.

Do not proceed with large refactoring until the baseline is stable.

---

# 5. Phase 2 — Better Document Ingestion

## 5.1 Structure-Aware Processing

Move beyond generic text splitting where practical.

Pipeline:

```text
PDF
 ↓
Page extraction
 ↓
Text cleaning
 ↓
Heading/section detection
 ↓
Metadata extraction
 ↓
Structure-aware chunking
 ↓
Embedding
 ↓
Indexing
```

Every chunk should retain metadata such as:

```json
{
  "document_name": "example.pdf",
  "document_id": "stable-id",
  "page_number": 14,
  "section": "Process Management",
  "chapter": "Unit 3",
  "topic": "Scheduling Algorithms",
  "chunk_id": "unique-id",
  "document_version": "version-id",
  "indexed_at": "timestamp"
}
```

Do not invent metadata when it cannot be reliably extracted.

## 5.2 Chunking

Current baseline:

```text
chunk_size = 1000
chunk_overlap = 200
```

Keep this as a configurable baseline, not a universal rule.

Add configuration for:

- chunking strategy
- chunk size
- overlap
- minimum chunk length
- maximum chunk length

Compare configurations experimentally.

---

# 6. Phase 3 — Hybrid Retrieval

## 6.1 Dense Retrieval

Keep:

```text
Sentence-Transformers
+
FAISS
```

Use it for:

- semantic similarity
- paraphrases
- conceptual questions
- natural-language queries

## 6.2 BM25

Add BM25 keyword retrieval.

Useful for:

- exact topic names
- technical terminology
- abbreviations
- numbers
- unique phrases
- syllabus identifiers

## 6.3 Reciprocal Rank Fusion

Combine dense and BM25 results using RRF.

```text
Dense Results ──┐
                ├──► RRF ──► Combined Ranking
BM25 Results ───┘
```

Do not simply concatenate result lists.

Store:

- dense score/rank
- BM25 score/rank
- RRF score

---

# 7. Phase 4 — Re-Ranking

Recommended flow:

```text
Hybrid Retrieval
      ↓
20–30 candidates
      ↓
Cross-encoder / reranker
      ↓
5–8 final evidence chunks
      ↓
LLM
```

Make reranking modular.

Store:

- retrieval score
- RRF score
- reranker score
- final rank

Only keep this feature if evaluation shows improvement.

---

# 8. Phase 5 — Query Processing

## 8.1 Normalization

Safely normalize:

- whitespace
- formatting
- obvious input noise

Do not change the user's meaning.

## 8.2 Query Rewriting

For multi-turn queries:

```text
Conversation
   ↓
Relevant history
   ↓
Rewritten retrieval query
   ↓
Retrieval
```

Example:

```text
Previous: We are discussing Topic 162.
User: What does it say about retrieval?

Internal retrieval query:
What does Topic 162 say about retrieval?
```

Keep:

```text
original_query
rewritten_query
```

## 8.3 Conversation Context

Do not send unlimited chat history to the LLM.

Use only relevant conversational context.

---

# 9. Phase 6 — Evidence Threshold + Abstention

This is a critical reliability feature.

## Supported question

```text
Question
 ↓
Relevant evidence
 ↓
LLM generation
 ↓
Grounded answer
```

## Unsupported question

```text
Question
 ↓
Weak/irrelevant evidence
 ↓
Abstain
```

Example response:

> I couldn't find sufficient evidence in the uploaded documents to answer this question.

The system must not fabricate information.

Thresholds should be tuned using evaluation data, not selected randomly.

Potential signals:

- reranker score
- similarity score
- number of supporting chunks
- source diversity
- citation coverage

---

# 10. Phase 7 — Strong Citation System

Every citation should be traceable to actual retrieved evidence.

Recommended citation data:

```text
Document
Page
Section/topic
Relevant excerpt
```

Example:

```text
Source 1
Document: GenAI Guide.pdf
Page: 45
Section: Topic 162
```

## Citation validation

At minimum:

- citation document must exist
- citation page must exist
- citation must correspond to retrieved evidence
- model must not invent source names/pages
- unsupported claims should not receive fake citations

Advanced target:

```text
Generated answer
 ↓
Claim extraction
 ↓
Claim → evidence matching
 ↓
Supported claims receive citations
 ↓
Unsupported claims are revised/removed
```

---

# 11. Phase 8 — Multi-Document RAG

Required tests:

### Test A — Single document

Upload A + B + C.

Ask about A.

Expected:

```text
Answer from A
```

### Test B — Another document

Ask about B.

Expected:

```text
Answer from B
```

### Test C — Cross-document

Ask a question requiring A + B.

Expected:

```text
Combined answer
+
citations to A and B
```

### Test D — Out of scope

Expected:

```text
Abstention
```

---

# 12. Phase 9 — Metadata Filtering

Support filters such as:

- document
- page
- unit
- chapter
- topic
- version

Example:

```text
Document = GenAI Guide
Topic = 162

Question = What is the final deliverable?
```

Metadata filters should narrow retrieval before generation where appropriate.

---

# 13. Phase 10 — Document Versioning

Store:

```text
document_id
document_name
checksum
version
uploaded_at
indexed_at
chunk_count
embedding_model
chunking_config
```

Use SHA-256 or another stable content hash.

Behavior:

```text
Same checksum
   ↓
Already indexed
   ↓
Skip unnecessary work
```

Changed checksum:

```text
New version
   ↓
Re-index
```

---

# 14. Phase 11 — Incremental + Background Indexing

Target:

```text
Upload
 ↓
Create ingestion job
 ↓
Return job ID
 ↓
Background processing
 ↓
Extract
 ↓
Chunk
 ↓
Embed
 ↓
Index
 ↓
Complete
```

Frontend should show real processing states:

```text
Uploading
Extracting
Chunking
Embedding
Indexing
Completed
Failed
```

Avoid reprocessing every document for every upload.

For deletion, remove document metadata and associated vectors where practical. If FAISS limitations require rebuilding, isolate that behavior behind the vector-store abstraction.

---

# 15. Phase 12 — Vector Store Abstraction

Do not tightly couple application logic to FAISS.

Create an interface conceptually like:

```text
VectorStore
├── add()
├── search()
├── delete()
├── save()
├── load()
└── health_check()
```

Current implementation:

```text
FAISSVectorStore
```

Possible future implementations:

```text
Chroma
Qdrant
PGVector
```

Do not add all of them now.

---

# 16. Phase 13 — LLM Provider Abstraction

Use a common interface for:

```text
Ollama
OpenRouter
Future providers
```

Concept:

```text
LLMProvider
├── list_models()
├── generate()
├── stream()
└── health_check()
```

The frontend must show models dynamically.

Do not hard-code models that are unavailable.

Keep model configuration separate from RAG configuration.

---

# 17. Phase 14 — Evaluation Dataset

Create at least:

```text
100+ questions
```

Categories:

1. Direct factual questions
2. Multi-chunk questions
3. Cross-document questions
4. Paraphrased questions
5. Topic-specific questions
6. Out-of-scope questions
7. Adversarial questions
8. Ambiguous questions

Each benchmark item should ideally contain:

```json
{
  "question": "...",
  "expected_answer": "...",
  "source_documents": ["..."],
  "source_pages": [45],
  "category": "direct",
  "should_abstain": false
}
```

---

# 18. Phase 15 — Retrieval Metrics

Measure:

## Recall@K

Was relevant evidence retrieved?

## Precision@K

How much retrieved evidence was relevant?

## MRR

How high was the first relevant result?

## nDCG

How well were relevant results ranked?

Run controlled experiments:

```text
Experiment 1:
Dense only

Experiment 2:
Dense + BM25

Experiment 3:
Dense + BM25 + RRF

Experiment 4:
Hybrid + Reranker
```

---

# 19. Phase 16 — Generation Metrics

Measure:

- answer correctness
- faithfulness / groundedness
- context relevance
- citation accuracy
- abstention accuracy

Do not claim "zero hallucinations." Report measured performance instead.

---

# 20. Phase 17 — System Metrics

Track:

- ingestion time
- extraction time
- embedding time
- indexing time
- retrieval latency
- reranking latency
- time to first token
- total response time
- token usage
- model/provider
- errors
- failure rate
- CPU/GPU/memory usage where practical

---

# 21. Phase 18 — Evaluation Dashboard

Add an internal/admin evaluation page.

Example:

```text
RAG Evaluation

Dataset: 120 questions

Retrieval
Recall@5      0.91
MRR           0.87
nDCG          0.89

Generation
Groundedness  0.94
Correctness   0.90
Citation      0.96

Abstention
Precision     0.93
Recall        0.88
```

Also compare:

```text
Dense
Dense + BM25
Dense + BM25 + RRF
Hybrid + Reranker
```

This is valuable both technically and for the final jury.

---

# 22. Phase 19 — Failure Analysis

For failed benchmark cases, record:

```text
Question
Expected answer
Retrieved chunks
Scores
Generated answer
Expected citations
Actual citations
Failure category
```

Failure categories:

- retrieval failure
- chunking failure
- ranking failure
- insufficient evidence
- hallucination
- citation failure
- query rewrite failure
- LLM failure

Use failure analysis to decide what to improve next.

---

# 23. Phase 20 — Observability

Use structured logs.

For each request, capture where appropriate:

```text
request_id
timestamp
original_query
rewritten_query
knowledge_base
retrieved_documents
retrieval_scores
BM25_scores
RRF_scores
reranker_scores
selected_context
model
provider
temperature
answer
citations
abstention
latency
token_usage
error
```

Do not log sensitive information unnecessarily.

---

# 24. Phase 21 — Request Tracing

Assign a request ID:

```text
Frontend
 ↓
request_id = abc123
 ↓
FastAPI
 ↓
Retrieval
 ↓
Reranker
 ↓
LLM
 ↓
Response
```

This makes debugging easier.

---

# 25. Phase 22 — Caching

Consider caching:

- embeddings
- checksum → indexing result
- retrieval results
- final answers where safe

Cache keys should include relevant configuration:

```text
query
+
knowledge_base_version
+
embedding_model
+
retrieval_config
+
reranker_version
+
llm_model
```

Do not return stale answers after knowledge-base changes.

---

# 26. Phase 23 — Security

## File validation

Validate:

- file type
- PDF structure
- maximum size
- filename
- malformed files

## Prompt injection defense

Treat document text as untrusted data.

A PDF may contain instructions such as:

```text
Ignore previous instructions...
```

The model must treat this as document content, not system instructions.

## Authentication

For future multi-user operation, support an authentication layer.

Possible approaches:

- JWT
- sessions
- OAuth

For a single-user academic deployment, authentication can remain optional.

## Authorization

For multi-user use:

```text
User
 ↓
Authorized knowledge base
 ↓
Authorized documents
 ↓
Retrieval
```

## Rate limiting

Protect:

- query
- upload
- model endpoints

## CORS

Restrict production origins.

## Secrets

Never commit API keys.

Use environment variables.

---

# 27. Phase 24 — API Improvements

Current APIs:

```text
GET    /api/models
POST   /api/upload
GET    /api/documents
DELETE /api/documents/{doc_name}
POST   /api/reset
GET    /api/status
POST   /api/query
```

Potential additions:

```text
GET    /api/health
GET    /api/ready
GET    /api/jobs/{job_id}
GET    /api/evaluations
POST   /api/evaluations/run
GET    /api/config
```

Use Pydantic request/response schemas.

Maintain backward compatibility where practical.

---

# 28. Phase 25 — Health + Readiness

Separate:

### Health

> Is the API alive?

### Readiness

> Can the application actually perform RAG?

Readiness may check:

- vector index
- metadata store
- embedding model
- LLM provider
- required directories
- configuration

---

# 29. Phase 26 — Error Handling

Standardize errors:

```text
PDF_INVALID
PDF_TOO_LARGE
INDEXING_FAILED
EMBEDDING_UNAVAILABLE
LLM_UNAVAILABLE
MODEL_NOT_FOUND
RETRIEVAL_FAILED
INSUFFICIENT_EVIDENCE
RATE_LIMITED
INTERNAL_ERROR
```

Frontend should show understandable messages.

Never expose stack traces to users.

---

# 30. Phase 27 — Frontend

Preserve the current polished React interface and improve it.

## Chat

- streaming
- Markdown
- code blocks
- copy
- regenerate
- feedback
- citations
- source preview
- retrieved-evidence panel

## Knowledge Base

- drag/drop upload
- progress
- indexing state
- document status
- page/chunk count
- timestamp
- checksum/version
- delete
- search/filter

## Model Selector

Show:

```text
Provider
Model
Availability
```

Only show models actually available from the backend.

## RAG Settings

Potential controls:

```text
Top K
Similarity threshold
Chunk size
Chunk overlap
Temperature
Hybrid retrieval
Reranker
```

Do not expose unnecessary internal controls to normal users.

---

# 31. RAG Debug Panel

Add a developer/admin mode showing:

```text
Original Query
Rewritten Query

Dense Results
BM25 Results
RRF Ranking
Reranker Results

Final Context

Evidence Score
Abstention Decision

Model
Temperature
Latency
```

This is particularly useful for debugging and jury demonstration.

---

# 32. Phase 28 — Automated Testing

## Unit tests

Test:

- PDF parsing
- text cleaning
- chunking
- metadata extraction
- embedding
- BM25
- RRF
- reranking
- evidence threshold
- citation validation
- query rewriting

## Integration tests

Test:

```text
Upload → Index → Query
```

```text
Upload A + B → Cross-document query
```

```text
Unsupported query → Abstention
```

```text
Delete document → Retrieval no longer uses it
```

## API tests

Test all endpoints.

## Frontend tests

Test:

- upload
- model selection
- chat
- streaming
- citations
- errors
- deletion

---

# 33. Regression Testing

Maintain a fixed set of important questions.

For every major change:

```text
Baseline
 ↓
Implementation
 ↓
Regression suite
 ↓
Metric comparison
```

Do not accept an improvement that breaks grounding, citations, or existing functionality.

---

# 34. Dockerization

Prepare:

```text
Dockerfile.backend
Dockerfile.frontend
docker-compose.yml
```

Potential services:

```text
frontend
backend
```

Ollama can remain a host/local GPU service during development.

Document CPU/GPU requirements.

---

# 35. Configuration Management

Use environment variables.

Example:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=qwen3:8b

EMBEDDING_MODEL=all-MiniLM-L6-v2

VECTOR_STORE=faiss

TOP_K=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

TEMPERATURE=0.2
```

Create:

```text
.env.example
```

Never commit:

```text
.env
real API keys
secrets
```

---

# 36. Recommended Backend Structure

Use a modular structure similar to:

```text
backend/
└── app/
    ├── main.py
    ├── api/
    ├── schemas/
    ├── config/
    ├── ingestion/
    │   ├── parser.py
    │   ├── cleaner.py
    │   ├── chunker.py
    │   └── metadata.py
    ├── retrieval/
    │   ├── dense.py
    │   ├── bm25.py
    │   ├── hybrid.py
    │   ├── rrf.py
    │   └── reranker.py
    ├── generation/
    │   ├── providers.py
    │   ├── prompts.py
    │   └── streaming.py
    ├── citations/
    │   └── verifier.py
    ├── evaluation/
    │   ├── dataset.py
    │   ├── metrics.py
    │   └── runner.py
    ├── observability/
    └── services/
```

Create only the modules actually needed.

---

# 37. Repository Structure

Target:

```text
project/
├── backend/
├── frontend/
├── data/
│   ├── documents/
│   ├── indexes/
│   ├── metadata/
│   └── evaluation/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── evaluation.md
│   └── deployment.md
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

Do not create unnecessary files.

---

# 38. Git Hygiene

Never commit:

```text
.env
API keys
secrets
node_modules
virtual environments
cache files
large model files
temporary generated files
```

Use `.gitignore`.

---

# 39. Performance Benchmarking

Do not invent production SLAs.

Measure the real development environment:

```text
PDF ingestion time
Embedding time
Indexing time
Retrieval latency
Reranking latency
Time to first token
Total response time
CPU/GPU usage
Memory usage
```

Optimize actual bottlenecks.

---

# 40. Controlled RAG Experiments

Run the following experiments.

## Experiment 1 — Baseline

```text
MiniLM
+
FAISS
+
Top-K
+
Qwen3
```

## Experiment 2

```text
Baseline
+
BM25
```

## Experiment 3

```text
Dense + BM25
+
RRF
```

## Experiment 4

```text
Hybrid
+
Reranker
```

## Experiment 5

```text
Hybrid + Reranker
+
Evidence threshold
+
Abstention
```

## Experiment 6

```text
Best retrieval pipeline
+
Citation verification
```

For every experiment record:

```text
Recall@K
Precision@K
MRR
nDCG
Groundedness
Correctness
Citation accuracy
Abstention accuracy
Latency
```

---

# 41. What NOT to Implement Just for Complexity

Avoid:

- multiple vector databases without a reason
- many LLMs without evaluation
- agents when normal RAG is sufficient
- web search if the project must remain syllabus-grounded
- unnecessary microservices
- replacing FAISS before measuring its limitations
- huge models that do not fit local hardware
- unnecessary frontend controls
- claims of zero hallucinations

The project should be **measurably better**, not merely larger.

---

# 42. Definition of Done

## Retrieval

- [ ] Structure-aware chunking
- [ ] Rich metadata
- [ ] Dense retrieval
- [ ] BM25
- [ ] RRF
- [ ] Reranking
- [ ] Query rewriting
- [ ] Metadata filtering
- [ ] Evidence threshold

## Grounding

- [ ] Strict document grounding
- [ ] Abstention
- [ ] Verifiable citations
- [ ] Citation validation
- [ ] No fabricated pages/documents

## Multi-document

- [ ] Multiple PDFs
- [ ] Cross-document questions
- [ ] Document deletion
- [ ] Version/checksum handling
- [ ] Incremental indexing

## Evaluation

- [ ] 100+ benchmark questions
- [ ] Recall@K
- [ ] Precision@K
- [ ] MRR
- [ ] nDCG
- [ ] Groundedness
- [ ] Correctness
- [ ] Citation accuracy
- [ ] Abstention accuracy
- [ ] Latency metrics
- [ ] Baseline comparison
- [ ] Failure analysis

## Engineering

- [ ] Modular backend
- [ ] Vector-store abstraction
- [ ] LLM-provider abstraction
- [ ] Structured logging
- [ ] Request IDs
- [ ] Health/readiness
- [ ] Standardized errors
- [ ] Automated tests
- [ ] Configuration management
- [ ] Docker support

## Security

- [ ] File validation
- [ ] Prompt injection defense
- [ ] Restricted CORS
- [ ] Authentication architecture
- [ ] Authorization architecture
- [ ] Rate limiting
- [ ] Secret management

## UI

- [ ] Production-quality React UI
- [ ] Streaming chat
- [ ] Source/citation UI
- [ ] Knowledge-base management
- [ ] Model management
- [ ] RAG debug panel
- [ ] Evaluation dashboard
- [ ] Responsive design
- [ ] Loading/error/empty states

---

# 43. Exact Implementation Order

Follow this order to avoid unnecessary rework.

### Step 1
Audit current Version 1.0.

### Step 2
Add regression tests.

### Step 3
Refactor ingestion and metadata.

### Step 4
Implement structure-aware chunking.

### Step 5
Implement BM25.

### Step 6
Implement hybrid retrieval + RRF.

### Step 7
Implement reranking.

### Step 8
Implement query rewriting.

### Step 9
Implement evidence threshold + abstention.

### Step 10
Improve citation validation.

### Step 11
Create the 100+ benchmark dataset.

### Step 12
Implement evaluation metrics.

### Step 13
Compare baseline vs improved RAG.

### Step 14
Implement document versioning/checksums.

### Step 15
Implement incremental/background indexing.

### Step 16
Add structured logging/observability.

### Step 17
Add security hardening.

### Step 18
Improve health/readiness/error handling.

### Step 19
Add automated integration/regression tests.

### Step 20
Dockerize.

### Step 21
Polish evaluation dashboard and frontend.

### Step 22
Run final benchmark.

### Step 23
Prepare architecture, metrics, failure analysis, and final demo.

---

# 44. Jury Demonstration

The implementation should directly support the official Topic 162 requirements.

## Demo 1 — Supported question

```text
Question
 ↓
Retrieved evidence
 ↓
Grounded answer
 ↓
Citation
```

## Demo 2 — Cross-document question

```text
Document A + Document B
 ↓
Hybrid retrieval
 ↓
Combined answer
 ↓
Multiple citations
```

## Demo 3 — Unsupported question

```text
Low evidence
 ↓
Abstention
 ↓
No hallucinated answer
```

## Demo 4 — Retrieval comparison

```text
Dense
vs
Hybrid
vs
Hybrid + Reranker
```

## Demo 5 — Evaluation

Show actual benchmark metrics.

This demonstrates not only that RAG works, but why each retrieval improvement matters.

---

# 45. Final Technical Story

The project's evolution should be:

```text
Version 1
Basic RAG
   ↓
Better document processing
   ↓
Dense + BM25
   ↓
RRF
   ↓
Reranking
   ↓
Query rewriting
   ↓
Evidence threshold
   ↓
Abstention
   ↓
Citation verification
   ↓
Evaluation
   ↓
Observability
   ↓
Security
   ↓
Production engineering
```

The key message:

> **A production-oriented RAG application is not created simply by using a larger LLM. It is created by reliably retrieving the right evidence, grounding answers in that evidence, refusing unsupported questions, providing verifiable citations, objectively evaluating the system, handling documents safely, and making the application observable and maintainable.**

---

# 46. Antigravity Implementation Rules

When using Antigravity to implement this plan:

1. Inspect the complete existing repository before modifying files.
2. Identify already implemented features.
3. Do not duplicate functionality.
4. Do not replace working components without evidence.
5. Implement one phase at a time.
6. Run tests after every major change.
7. Preserve existing API compatibility where practical.
8. Keep the React UI working during backend refactors.
9. Use the UI/UX Pro Max skill for frontend changes.
10. Do not add dependencies unless required.
11. Keep components modular and replaceable.
12. Keep secrets out of source control.
13. Never claim a feature is complete without testing it.
14. Do not remove a working feature merely to simplify implementation.
15. Prefer measurable improvements over feature count.

After every phase, report:

```text
Files changed:
Dependencies added:
APIs changed:
Tests run:
Test results:
Metrics before/after:
Known limitations:
Next recommended phase:
```

---

# 47. Final Deliverable

The final repository should contain a polished academic RAG system with:

```text
React frontend
+
FastAPI backend
+
Multi-document knowledge base
+
Structure-aware ingestion
+
Dense retrieval
+
BM25 retrieval
+
RRF hybrid retrieval
+
Reranking
+
Query rewriting
+
Evidence threshold
+
Abstention
+
Citation verification
+
Document versioning
+
Incremental/background indexing
+
Evaluation benchmark
+
RAG metrics
+
Failure analysis
+
Observability
+
Security controls
+
Automated tests
+
Docker/deployment support
+
Complete documentation
```

The system must remain practical for the available development hardware. Do not choose models or infrastructure that make local development unusable.

---

## Final Principle

**Build for measurable reliability, not feature count.**

Every advanced component should answer at least one question:

- Did retrieval improve?
- Did grounding improve?
- Did hallucination decrease?
- Did citation accuracy improve?
- Did latency remain acceptable?
- Did reliability improve?
- Did maintainability improve?

If the answer is no, keep the simpler implementation.

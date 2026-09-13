# Ask-the-Syllabus Bot — RAG-Based Academic Assistant

## 1. Project Overview

**Project Title:** Ask-the-Syllabus Bot  
**Project Type:** Generative AI — Model Making  
**Academic Level:** PG / MSc AI-ML  
**Assessment Structure:** Phase 1 (Jury 1) → Phase 2 (Jury 2) → Final Phase (ESE / Final Jury)

### Problem Statement

Students often need to search through syllabi, lecture notes, academic PDFs, and other course documents to find specific information. Traditional keyword-based search can be inefficient because it does not understand the semantic meaning of a user's question.

The **Ask-the-Syllabus Bot** is a Retrieval-Augmented Generation (RAG) application that allows a user to ask questions about uploaded academic documents. The system retrieves relevant information from the documents and provides an LLM-generated answer grounded in that retrieved context.

### Main Objective

Build an academic question-answering assistant that:

- Accepts syllabus and academic PDF documents.
- Extracts and processes their text.
- Splits documents into useful chunks.
- Converts chunks into vector embeddings.
- Stores embeddings in a vector database.
- Retrieves relevant document chunks for a user query.
- Uses an LLM to generate a grounded answer.
- Provides source/citation information where possible.
- Reduces unsupported answers and hallucinations.
- Progressively improves through the three project phases.

---

# 2. Project Workflow

The overall RAG workflow is:

```text
                Academic Documents
                 (PDF / Notes)
                       |
                       v
                Text Extraction
                       |
                       v
                    Chunking
                       |
                       v
                 Text Embeddings
                       |
                       v
                Vector Database
                 (FAISS/Chroma)
                       |
                       |
User Question --------+
       |
       v
Question Embedding
       |
       v
Similarity Search
       |
       v
Relevant Document Chunks
       |
       v
       LLM
       |
       v
Grounded Answer
       |
       v
Source / Citation
```

## Detailed Workflow

### Step 1 — Document Ingestion

The user uploads academic documents such as:

- Course syllabus
- Lecture notes
- Unit-wise PDFs
- Study material
- Question papers

### Step 2 — Text Extraction

Text is extracted from the uploaded documents using a PDF/document parser.

### Step 3 — Chunking

Long documents are divided into smaller chunks.

Example:

```text
Document
   ↓
Paragraphs / Sections
   ↓
Chunks
   ↓
Chunk 1
Chunk 2
Chunk 3
...
```

Chunk size and overlap will be experimented with in later phases.

### Step 4 — Embedding Generation

Each text chunk is converted into a numerical vector representation using an embedding model.

Conceptually:

```text
"Transformer uses self-attention"
              ↓
       Embedding Model
              ↓
       [0.12, -0.43, ...]
```

### Step 5 — Vector Storage

The embeddings are stored in a vector database such as:

- FAISS
- ChromaDB

### Step 6 — Query Processing

The user's question is also converted into an embedding.

### Step 7 — Retrieval

The system compares the question embedding with stored document embeddings and retrieves the most relevant chunks.

### Step 8 — Generation

The retrieved chunks are provided as context to the LLM.

The LLM generates an answer based on the retrieved information.

### Step 9 — Source/Citation

The application displays the source document and, where supported, page/chunk information used to generate the answer.

---

# 3. Technology Stack

## Core Language

- **Python**

## GenAI / LLM Layer

- Large Language Model (LLM)
- Prompt engineering
- Hugging Face models and/or an LLM API depending on availability

## RAG Framework

One of:

- **LangChain**
- **LlamaIndex**

The final implementation may use one primary framework rather than both.

## Embeddings

A suitable sentence/document embedding model, such as a Hugging Face sentence-transformer model.

## Vector Database

Primary options:

- **FAISS**
- **ChromaDB**

## Document Processing

- PDF/document text extraction library
- Chunking and preprocessing utilities

## Frontend / Application

- **Streamlit**

Streamlit will provide the interface for:

- PDF upload
- Question input
- Answer display
- Source/citation display

## Development Environment

- VS Code / PyCharm
- Google Colab where GPU or notebook-based experimentation is useful
- Git/GitHub for version control

## Possible Supporting Libraries

```text
Python
├── LangChain / LlamaIndex
├── Hugging Face / Sentence Transformers
├── FAISS / ChromaDB
├── PDF parser
├── Streamlit
└── NumPy / Pandas
```

The exact libraries may be adjusted during implementation based on compatibility, performance, and project requirements.

---

# 4. Project Phases

The project will be developed progressively across the three jury stages.

```text
PHASE 1
Jury 1
Basic Working RAG
      |
      v
PHASE 2
Jury 2
Improved + Evaluated RAG
      |
      v
FINAL PHASE
Final Jury / ESE
Complete In-Depth System
```

Because this is a **Model Making** topic, the same project will be continued and expanded across the phases rather than being replaced with a new topic.

---

# 5. Phase 1 — Jury 1

## Goal

> **Build and demonstrate a basic working RAG-based Ask-the-Syllabus Bot.**

The main objective of Phase 1 is to establish the complete core RAG pipeline and demonstrate that the system can answer questions using information from the provided academic documents.

## Phase 1 Scope

### 1. Basic UI

Create a simple Streamlit interface with:

- PDF upload
- Question input
- Ask button
- Answer display

Example:

```text
+---------------------------------------+
|       ASK-THE-SYLLABUS BOT            |
+---------------------------------------+
| Upload PDF                            |
| [ syllabus.pdf ]                      |
|                                       |
| Question:                             |
| [ What is covered in Unit 2? ]        |
|                                       |
|              [ ASK ]                  |
|                                       |
| Answer:                               |
| ...                                   |
+---------------------------------------+
```

### 2. PDF Processing

Implement:

```text
PDF
 ↓
Text Extraction
 ↓
Clean Text
```

### 3. Basic Chunking

Split extracted text into manageable chunks.

Initial chunk size and overlap can be selected as reasonable baseline values.

The important goal in Phase 1 is to establish a functioning pipeline, not to optimise chunking completely.

### 4. Embeddings

Generate embeddings for each document chunk.

### 5. Vector Database

Store the embeddings in:

- FAISS or
- ChromaDB

### 6. Basic Retrieval

For a user's question:

```text
Question
   ↓
Question Embedding
   ↓
Similarity Search
   ↓
Top-K Relevant Chunks
```

### 7. LLM Generation

Pass the retrieved chunks to the LLM as context.

The prompt should instruct the model to answer using the supplied context.

### 8. Basic Grounding

The system should avoid confidently answering questions that cannot be supported by the provided documents.

### 9. Initial Testing

Test the system with several questions:

- Questions whose answers are present in the documents.
- Questions whose answers are not present in the documents.

## Phase 1 Deliverables

- Working RAG prototype
- Basic Streamlit interface
- PDF ingestion pipeline
- Text chunking
- Embedding generation
- Vector database
- Similarity retrieval
- LLM-based answer generation
- Basic test cases
- System architecture diagram
- Jury 1 presentation

## Phase 1 Presentation Focus

The Jury 1 presentation should explain:

1. Problem statement
2. Objectives
3. What is RAG?
4. Why RAG is useful for this problem
5. System architecture
6. Technology stack
7. Implementation workflow
8. Working demo
9. Initial results
10. Syllabus concept mapping
11. Limitations
12. Future improvements

## Expected Phase 1 Outcome

At the end of Phase 1:

> **A functional prototype that can ingest an academic document, retrieve relevant information, and generate an answer using an LLM.**

---

# 6. Phase 2 — Jury 2

## Goal

> **Improve the basic RAG system and demonstrate that retrieval and answer quality can be evaluated.**

Phase 2 should move the project beyond a simple demonstration and introduce better retrieval, multiple documents, citations, and systematic evaluation.

## Phase 2 Scope

### 1. Multi-Document Support

Move from a single PDF to multiple academic documents.

Example:

```text
Syllabus.pdf
Unit1.pdf
Unit2.pdf
Unit3.pdf
LectureNotes.pdf
QuestionPaper.pdf
       |
       v
   RAG System
```

### 2. Improved Chunking

Experiment with:

- Different chunk sizes
- Chunk overlap
- Paragraph/section-based splitting

Compare the effect on retrieval quality.

### 3. Improved Retrieval

Experiment with:

- Different `top-k` values
- Similarity thresholds
- Better embedding models
- Retrieval strategies

If appropriate, introduce a reranking stage:

```text
Question
   ↓
Vector Retrieval
   ↓
Top-K Chunks
   ↓
Reranking
   ↓
Best Context
   ↓
LLM
```

### 4. Source Citations

The generated answer should show supporting sources.

Example:

```text
Answer:
Transformers use self-attention to model relationships
between tokens.

Sources:
- Unit2.pdf — Page 12
- Lecture3.pdf — Page 7
```

### 5. Hallucination Testing

Create questions in two categories:

```text
Category A:
Answer exists in documents

Category B:
Answer does NOT exist in documents
```

Measure how frequently the system provides grounded answers versus unsupported answers.

### 6. Evaluation Dataset

Create a small test set containing representative academic questions.

Example:

```text
Q1: What is RAG?
Q2: What is self-attention?
Q3: What topics are in Unit 2?
Q4: What is the definition of GAN?
Q5: Ask something not present in the documents.
```

### 7. Evaluation Metrics

Depending on implementation, evaluate:

- Retrieval relevance
- Answer groundedness
- Citation accuracy
- Response time
- Retrieval success rate

The exact metrics will be selected based on what can be reliably measured.

### 8. Failure Analysis

Document cases where the system fails.

Examples:

- Wrong chunk retrieved
- Insufficient context
- Ambiguous question
- Missing information
- Incorrect citation
- Hallucinated answer

Then explain how the system was improved.

### 9. UI Improvements

Improve the Streamlit interface:

- Multiple document upload
- Document list
- Better answer formatting
- Source display
- Loading/status indicators
- Clear chat history
- Basic error handling

## Phase 2 Deliverables

- Improved RAG application
- Multi-document support
- Improved retrieval
- Better chunking
- Source citations
- Evaluation dataset
- Evaluation results
- Failure-case analysis
- Updated architecture
- Improved Streamlit interface
- Jury 2 presentation

## Expected Phase 2 Outcome

At the end of Phase 2:

> **A multi-document RAG system with improved retrieval, source citations, and measurable evaluation of grounded answers and failure cases.**

---

# 7. Final Phase — Final Jury / ESE

## Goal

> **Deliver a complete, robust, evaluated, and well-documented academic RAG assistant.**

The final phase should take the Phase 2 system and make it the most complete and in-depth version of the project.

## Final Phase Scope

### 1. Robust Document Pipeline

Support a wider range of academic documents and improve:

- Text extraction
- Cleaning
- Chunking
- Metadata handling
- Document/page tracking

### 2. Advanced Retrieval

Depending on Phase 2 results, implement the most useful retrieval improvements.

Possible components:

```text
User Question
      ↓
Query Processing
      ↓
Embedding
      ↓
Vector Search
      ↓
Metadata Filtering
      ↓
Reranking
      ↓
Relevant Context
      ↓
LLM
```

### 3. Strong Citation System

Ensure that generated answers can be traced back to the source documents wherever possible.

### 4. Comprehensive Evaluation

Create a proper evaluation dataset and report:

- Retrieval performance
- Groundedness
- Citation accuracy
- Response quality
- Failure cases
- Response latency

Where practical, compare different configurations.

Example:

```text
Baseline RAG
      vs
Improved RAG
```

### 5. Hallucination and Robustness Testing

Test:

- Questions outside the document
- Ambiguous questions
- Very short questions
- Long questions
- Questions spanning multiple documents
- Similar concepts from different documents
- Missing information
- Conflicting information

### 6. User Experience

Finalize the Streamlit application with:

- Clean UI
- Document management
- Chat interface
- Source/citation display
- Error handling
- Clear system status
- Useful response formatting

### 7. Documentation

Prepare:

- Project README
- Architecture diagram
- Workflow diagram
- Technology explanation
- Installation instructions
- Usage instructions
- Evaluation methodology
- Results
- Limitations
- Future scope

### 8. Final Demonstration

The final demo should show an end-to-end workflow:

```text
Upload Multiple Documents
          ↓
Document Processing
          ↓
Embedding + Indexing
          ↓
Ask Question
          ↓
Retrieve Relevant Context
          ↓
Rerank / Filter
          ↓
LLM Generation
          ↓
Grounded Answer
          ↓
Sources / Citations
```

## Final Deliverables

- Complete RAG application
- Final Streamlit UI
- Multi-document knowledge base
- Improved retrieval pipeline
- Citation system
- Evaluation framework
- Evaluation results
- Failure analysis
- Architecture and workflow diagrams
- Final documentation
- Final presentation
- Working demo / backup recording

## Expected Final Outcome

> **A complete academic RAG assistant capable of answering questions from multiple academic documents using retrieval-grounded generation, providing supporting sources, and demonstrating measurable performance and limitations.**

---

# 8. Phase Comparison

| Feature | Phase 1 — Jury 1 | Phase 2 — Jury 2 | Final Phase |
|---|---|---|---|
| Basic RAG | ✓ | ✓ | ✓ |
| PDF ingestion | ✓ | ✓ | ✓ |
| Text chunking | Basic | Improved/experimented | Optimised |
| Embeddings | ✓ | Improved if needed | Final |
| Vector DB | ✓ | ✓ | ✓ |
| Single document | ✓ | ✓ | ✓ |
| Multiple documents | Optional/basic | ✓ | ✓ |
| Basic retrieval | ✓ | ✓ | ✓ |
| Improved retrieval | — | ✓ | ✓ |
| Reranking | — | Optional/Recommended | If beneficial |
| Citations | Basic/Initial | ✓ | ✓ |
| Hallucination testing | Basic | ✓ | Comprehensive |
| Evaluation | Initial tests | Systematic | Comprehensive |
| Failure analysis | Basic | ✓ | ✓ |
| Streamlit UI | Basic | Improved | Final |
| Architecture | Initial | Updated | Final |
| Documentation | Basic | Expanded | Complete |
| Demo | ✓ | ✓ | ✓ |

---

# 9. Syllabus Concept Mapping

The project should explicitly connect to relevant Generative AI syllabus concepts.

Potential concepts include:

1. **Generative AI**
2. **Large Language Models**
3. **Transformers**
4. **Embeddings / Vector Representations**
5. **Prompt Engineering**
6. **Retrieval-Augmented Generation (RAG)**
7. **Hallucination and Grounding**
8. **Vector Databases**
9. **Information Retrieval**

The final mapping should use the exact concepts included in the official course syllabus.

---

# 10. Expected Jury Questions

## Phase 1

- What is Generative AI?
- What is RAG?
- Why use RAG instead of directly asking an LLM?
- What is an embedding?
- What is a vector database?
- How does similarity search work?
- Why do we chunk documents?
- How does the LLM receive the retrieved information?
- What is hallucination?
- How does RAG reduce hallucination?

## Phase 2

- How did you improve retrieval?
- Why did you choose your chunk size?
- Why did you choose your embedding model?
- What is top-k retrieval?
- Why are citations important?
- How did you evaluate groundedness?
- What happens when the answer is not in the documents?
- What are your failure cases?
- Why would reranking improve retrieval?
- How is your Phase 2 system better than Phase 1?

## Final Jury

- Explain the complete RAG architecture.
- What are the limitations of RAG?
- How would you handle conflicting documents?
- How would you scale the vector database?
- How would you reduce latency?
- How would you improve retrieval further?
- How do you prevent hallucination?
- How reliable are your citations?
- How did you evaluate the system?
- What would you change if you deployed this in a real university?

---

# 11. Development Philosophy

The project should follow an incremental approach:

```text
BUILD
  ↓
TEST
  ↓
MEASURE
  ↓
IDENTIFY FAILURE
  ↓
IMPROVE
  ↓
RE-EVALUATE
```

The goal is **not** to build the largest possible GenAI application.

The goal is to demonstrate:

> **Understanding → Implementation → Experimentation → Evaluation → Improvement**

This progression is especially important for a PG-level individual project.

---

# 12. Final Project Vision

The final Ask-the-Syllabus Bot should function as an academic knowledge assistant rather than a generic chatbot.

A user should be able to:

```text
Upload academic documents
        ↓
Ask natural-language questions
        ↓
Receive an answer grounded in those documents
        ↓
See supporting sources
        ↓
Trust the system more because its answer
can be traced back to the provided material
```

The project will therefore demonstrate practical application of **Generative AI, LLMs, embeddings, vector search, RAG, prompt engineering, grounding, and evaluation** in an academic use case.

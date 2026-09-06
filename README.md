# Ask-the-Syllabus Bot 🎓

A Retrieval-Augmented Generation (RAG) academic question-answering assistant. The application parses syllabus or lecture note PDFs, splits them into semantic chunks, creates local vector embeddings, indexes them using FAISS, and answers user questions grounded in the context of the files with clear citations.

## 🚀 Key Features
- **Flexible LLM Backend**: Use **Ollama** locally (100% offline generation) or **OpenRouter** (cloud-based inference featuring Llama, Mistral, Qwen, Gemini, and Claude).
- **Local Embedding Engine**: Generates embeddings locally using Hugging Face's `all-MiniLM-L6-v2` (sentence-transformers), requiring no embedding API keys.
- **Accurate Source Citation**: Displays an expandable viewer showing the exact context snippet, source document name, and page number referenced for the answer.
- **Strict Grounding**: Prompt engineering ensures the model doesn't hallucinate. It will state when it cannot find the answer in the provided documents.
- **Adaptive UI**: Modern design built using Streamlit with rich CSS styling, custom title cards, and support for light/dark mode.

---

## 🛠️ Architecture Workflow

```
            +---------------------------+
            |    Academic Documents     |
            |     (Syllabus PDFs)       |
            +-------------+-------------+
                          |
                          v
            +-------------+-------------+
            |  Text Extraction (pypdf)  |
            +-------------+-------------+
                          |
                          v
            +-------------+-------------+
            | Recursive Character Split  |
            +-------------+-------------+
                          |
                          v
            +-------------+-------------+
            |    Local Embeddings       |
            |   (all-MiniLM-L6-v2)      |
            +-------------+-------------+
                          |
                          v
            +-------------+-------------+
            |   Vector Database (FAISS)  |
            +-------------+-------------+
                          |
              [Similarity Search]
                          |
                          v
+--------------+    +-----+-----+    +-------------------+
| User Query   |--->| Retrieve  |--->| Prompt + Context  |
+--------------+    +-----------+    +---------+---------+
                                               |
                                               v
                                     +---------+---------+
                                     |    LLM Engine     |
                                     | Ollama/OpenRouter |
                                     +---------+---------+
                                               |
                                               v
                                     +---------+---------+
                                     |  Grounded Answer  |
                                     |   & Citations     |
                                     +-------------------+
```

---

## 💻 Setup Instructions

### 1. Prerequisite Installations
- Ensure you have **Python 3.10+** installed.
- (Optional) Start your local **Ollama** server if running local models.

### 2. Dependency Installation
Navigate to your workspace directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Ollama Setup (Local LLM Mode)
To run a local LLM, make sure the Ollama application is running on your computer.
Pull a model (such as Llama 3 or Phi 3):
```bash
# Pull Llama 3 (8B)
ollama pull llama3

# Or pull Phi 3 (3.8B)
ollama pull phi3
```
When you run the Streamlit app, it will auto-detect your local Ollama server and list the pulled models in the sidebar.

### 4. OpenRouter Setup (Cloud LLM Mode)
If you prefer running models via the cloud without using your local CPU/GPU:
1. Go to [OpenRouter](https://openrouter.ai/) and create an account.
2. Generate an API key.
3. Select "OpenRouter" in the Streamlit app sidebar, enter your API key, and choose your preferred model (including free models like `meta-llama/llama-3-8b-instruct:free`).

---

## 🏃 Running the Application

Launch the Streamlit dashboard by running:
```bash
streamlit run app.py
```
This will open the application in your default web browser (typically at `http://localhost:8501`).

---

## 🧪 Phase 1 Verification Guide
1. **Model Connection**: Connect to Ollama or OpenRouter. Check the sidebar for the online server confirmation badge.
2. **Document Upload**: Ingest a course syllabus PDF. Click the **"Process & Index Documents"** button. Check the success indicator displaying the page/chunk count.
3. **Query Grounding**:
   - Ask a question present in the document (e.g. *"What are the topics in Unit 1?"* or *"When is the final exam?"*). Verify that the system responds with a correct, structured answer and shows the correct source page.
   - Ask an out-of-bounds question (e.g. *"How do I bake bread?"*). Verify that the system refuses to answer and states the information is missing from the document.

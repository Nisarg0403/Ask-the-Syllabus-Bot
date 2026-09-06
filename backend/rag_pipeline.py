import os
import shutil
import json
import datetime
import torch
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Define directory paths relative to backend directory
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BACKEND_DIR, "documents")
FAISS_DIR = os.path.join(BACKEND_DIR, "faiss_index")
METADATA_FILE = os.path.join(BACKEND_DIR, "indexed_documents.json")

# Ensure directories exist
os.makedirs(DOCS_DIR, exist_ok=True)

def get_device():
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def get_embeddings():
    device = get_device()
    model_kwargs = {"device": device}
    encode_kwargs = {"normalize_embeddings": True}
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

def extract_text_from_pdf(pdf_path, filename):
    """
    Extracts text page-by-page from a PDF file path and returns
    a list of LangChain Document objects.
    """
    reader = PdfReader(pdf_path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            docs.append(Document(
                page_content=text,
                metadata={"source": filename, "page": i + 1}
            ))
    return docs

def load_metadata():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

def rebuild_vector_store(chunk_size=1000, chunk_overlap=200):
    """
    Rebuilds the FAISS database using all PDF files in the documents directory.
    """
    # Clean up old FAISS directory first
    if os.path.exists(FAISS_DIR):
        shutil.rmtree(FAISS_DIR)

    all_docs = []
    metadata = load_metadata()
    active_filenames = []

    # Get list of pdfs in DOCS_DIR
    for filename in os.listdir(DOCS_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(DOCS_DIR, filename)
            docs = extract_text_from_pdf(pdf_path, filename)
            all_docs.extend(docs)
            active_filenames.append(filename)

    # Clean metadata for deleted files
    metadata = {k: v for k, v in metadata.items() if k in active_filenames}
    save_metadata(metadata)

    if not all_docs:
        return None, 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = splitter.split_documents(all_docs)
    
    embeddings = get_embeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(FAISS_DIR)
    return db, len(chunks)

def load_vector_store():
    """
    Loads FAISS index from disk.
    """
    embeddings = get_embeddings()
    if os.path.exists(FAISS_DIR):
        return FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    return None

def retrieve_context(query, db, k=4):
    """
    Performs similarity search against the FAISS index.
    """
    if db is None:
        return []
    return db.similarity_search(query, k=k)

def get_llm(llm_provider, model_name, api_key=None, temperature=0.2):
    """
    Factory to return the selected LLM wrapper.
    """
    if llm_provider == "Ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://127.0.0.1:11434"
        )
    elif llm_provider == "OpenRouter":
        from langchain_openai import ChatOpenAI
        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature,
            default_headers={
                "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
                "X-Title": "Ask-the-Syllabus Bot"
            }
        )
    else:
        raise ValueError(f"Unknown LLM provider: {llm_provider}")

def stream_answer(query, retrieved_docs, llm_provider, model_name, api_key=None, temperature=0.2):
    """
    Generator yielding response tokens from the LLM.
    """
    context_str = ""
    for doc in retrieved_docs:
        source = doc.metadata.get("source", "Unknown Source")
        page = doc.metadata.get("page", "N/A")
        context_str += f"[Source: {source}, Page: {page}]\n{doc.page_content}\n\n"
        
    from langchain_core.prompts import ChatPromptTemplate
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an academic assistant called 'Ask-the-Syllabus Bot'.
Your task is to answer the student's question based strictly on the provided context.
If the context does not contain the information needed to answer the question, state clearly: "I cannot find the answer to this question in the provided documents."
Do not make up facts, guess, or use external knowledge. Keep your answer professional, accurate, and structured. Use bullet points or code formatting where appropriate.

Context:
{context}"""),
        ("human", "{question}")
    ])
    
    llm = get_llm(llm_provider, model_name, api_key, temperature)
    chain = prompt | llm
    
    for chunk in chain.stream({"context": context_str, "question": query}):
        yield chunk.content

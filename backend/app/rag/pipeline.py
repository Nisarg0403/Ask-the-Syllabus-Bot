import os
from typing import List, Generator, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import FAISS_DIR
from app.rag.embeddings import get_embeddings
from app.services.llm import get_llm

def load_vector_store() -> Optional[FAISS]:
    """Loads existing FAISS vector store index from storage."""
    embeddings = get_embeddings()
    if os.path.exists(FAISS_DIR) and len(os.listdir(FAISS_DIR)) > 0:
        return FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    return None

def retrieve_context(query: str, db: FAISS, k: int = 4) -> List[Document]:
    """Performs similarity search against the loaded FAISS index."""
    if db is None:
        return []
    return db.similarity_search(query, k=k)

def stream_answer(
    query: str,
    retrieved_docs: List[Document],
    llm_provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    temperature: float = 0.2
) -> Generator[str, None, None]:
    """
    Constructs grounded prompt context and yields token chunks from LLM.
    """
    context_str = ""
    for doc in retrieved_docs:
        source = doc.metadata.get("source", "Unknown Source")
        page = doc.metadata.get("page", "N/A")
        context_str += f"[Source: {source}, Page: {page}]\n{doc.page_content}\n\n"

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

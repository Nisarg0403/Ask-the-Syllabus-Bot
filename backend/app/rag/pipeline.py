import os
import time
from typing import List, Tuple, Generator, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import FAISS_DIR, DEFAULT_TOP_K
from app.core.observability import log_rag_stage
from app.rag.embeddings import get_embeddings
from app.services.llm import get_llm
from app.rag.bm25 import get_bm25_index
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.reranker import get_reranker
from app.rag.query_transform import rewrite_query

def load_vector_store() -> Optional[FAISS]:
    """Loads existing FAISS vector store index from storage."""
    embeddings = get_embeddings()
    if os.path.exists(FAISS_DIR) and len(os.listdir(FAISS_DIR)) > 0:
        return FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    return None

def retrieve_context(
    query: str,
    db: Optional[FAISS],
    k: int = DEFAULT_TOP_K,
    use_hybrid: bool = True,
    chat_history: Optional[List[dict]] = None
) -> Tuple[List[Document], bool]:
    """
    Hybrid Context Retrieval Engine with Query Transformation & Stage Telemetry:
    1. Query normalization and multi-turn reference resolution.
    2. Dense similarity search via FAISS.
    3. Sparse keyword search via BM25.
    4. Merged candidate ranking via Reciprocal Rank Fusion (RRF).
    5. Cross-Encoder Re-Ranking & Evidence Score Thresholding.
    
    Returns:
        - List[Document]: Reranked evidence chunks
        - bool: has_sufficient_evidence (False if abstention gate triggered)
    """
    if db is None:
        return [], False

    # 1. Query Transformation Stage
    t0 = time.time()
    original_query, search_query = rewrite_query(query, chat_history=chat_history)
    t_transform = (time.time() - t0) * 1000.0
    is_rewritten = (original_query != search_query)
    log_rag_stage("QUERY_TRANSFORM", t_transform, {"is_rewritten": is_rewritten})

    candidate_k = max(k * 4, 15)

    # 2. Dense FAISS Retrieval Stage
    t0 = time.time()
    try:
        dense_results = db.similarity_search_with_score(search_query, k=candidate_k)
        # Convert FAISS L2 distance score to similarity score (higher = better)
        dense_docs = [(doc, 1.0 / (1.0 + score)) for doc, score in dense_results]
    except Exception as e:
        dense_docs = []
        log_rag_stage("DENSE_SEARCH", (time.time() - t0) * 1000.0, error=str(e))
    else:
        log_rag_stage("DENSE_SEARCH", (time.time() - t0) * 1000.0, {"candidate_count": len(dense_docs)})

    # 3. Sparse BM25 Retrieval Stage
    t0 = time.time()
    bm25_index = get_bm25_index()
    bm25_docs = bm25_index.search(search_query, top_k=candidate_k)
    log_rag_stage("SPARSE_SEARCH", (time.time() - t0) * 1000.0, {"candidate_count": len(bm25_docs)})

    if not dense_docs and not bm25_docs:
        return [], False

    # 4. Reciprocal Rank Fusion Stage
    t0 = time.time()
    if use_hybrid and bm25_docs and dense_docs:
        fused_candidates = reciprocal_rank_fusion(dense_docs, bm25_docs, k=60, top_n=candidate_k)
    else:
        fused_candidates = dense_docs if dense_docs else bm25_docs
    log_rag_stage("RRF_FUSION", (time.time() - t0) * 1000.0, {"fused_count": len(fused_candidates)})

    # 5. Cross-Encoder Re-Ranking & Evidence Thresholding (Abstention Gate) Stage
    t0 = time.time()
    reranker = get_reranker()
    reranked_tuples, has_sufficient_evidence = reranker.rerank(search_query, fused_candidates, top_n=k)
    t_rerank = (time.time() - t0) * 1000.0

    max_score = reranked_tuples[0][1] if reranked_tuples else 0.0
    log_rag_stage("RERANKING", t_rerank, {
        "candidate_count_before": len(fused_candidates),
        "candidate_count_after": len(reranked_tuples),
        "top_score": round(max_score, 4),
        "has_sufficient_evidence": has_sufficient_evidence
    })

    final_docs = [doc for doc, _score in reranked_tuples]
    return final_docs, has_sufficient_evidence

def stream_answer(
    query: str,
    retrieved_docs: List[Document],
    llm_provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    temperature: float = 0.2,
    has_sufficient_evidence: bool = True
) -> Generator[str, None, None]:
    """
    Constructs grounded prompt context and yields token chunks from LLM.
    If evidence is insufficient (abstention gate), yields a polite abstention response.
    """
    if not has_sufficient_evidence or not retrieved_docs:
        yield "I couldn't find sufficient evidence in the uploaded documents to answer this question."
        return

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

    t0 = time.time()
    llm = get_llm(llm_provider, model_name, api_key, temperature)
    chain = prompt | llm | StrOutputParser()

    token_count = 0
    for chunk in chain.stream({"context": context_str, "question": query}):
        if chunk:
            token_count += 1
            yield chunk

    t_gen = (time.time() - t0) * 1000.0
    log_rag_stage("GENERATION", t_gen, {
        "provider": llm_provider,
        "model": model_name,
        "tokens_yielded": token_count
    })

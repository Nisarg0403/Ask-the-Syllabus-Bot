import pytest
from langchain_core.documents import Document
from app.rag.bm25 import BM25Index, build_bm25_index
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.reranker import get_reranker
from app.rag.pipeline import retrieve_context

def test_bm25_indexing_and_search():
    sample_docs = [
        Document(page_content="Unit 3 covers neural networks, backpropagation, and deep learning.", metadata={"source": "syllabus.pdf", "page": 3}),
        Document(page_content="Grading policy: Final exam is 40%, quizzes are 20%, assignments are 40%.", metadata={"source": "syllabus.pdf", "page": 1}),
        Document(page_content="Late submissions incur a 10% penalty per day up to 3 days maximum.", metadata={"source": "policies.pdf", "page": 2}),
    ]
    
    bm25_index = build_bm25_index(sample_docs)
    results = bm25_index.search("backpropagation neural networks", top_k=2)
    
    assert len(results) > 0
    top_doc, score = results[0]
    assert "neural networks" in top_doc.page_content.lower()
    assert score > 0.0

def test_reciprocal_rank_fusion():
    doc1 = Document(page_content="Backpropagation algorithm derivation", metadata={"source": "a.pdf", "page": 1})
    doc2 = Document(page_content="Gradient descent optimization", metadata={"source": "b.pdf", "page": 2})
    
    dense_results = [(doc1, 0.9), (doc2, 0.7)]
    bm25_results = [(doc2, 5.0), (doc1, 2.0)]
    
    fused = reciprocal_rank_fusion(dense_results, bm25_results, k=60, top_n=2)
    assert len(fused) == 2
    # Both documents should be ranked
    fused_docs = [d[0].page_content for d in fused]
    assert doc1.page_content in fused_docs
    assert doc2.page_content in fused_docs

def test_reranker_and_abstention_gate():
    reranker = get_reranker()
    doc_relevant = Document(page_content="The final jury exam consists of case study, model making, and real-time scenario.", metadata={"source": "jury.pdf", "page": 5})
    
    candidates = [(doc_relevant, 0.8)]
    reranked, has_evidence = reranker.rerank("What are the jury exam topics?", candidates, top_n=1)
    
    assert len(reranked) > 0
    assert has_evidence is True

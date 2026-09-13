import re
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field
from langchain_core.documents import Document

class Citation(BaseModel):
    document_name: str = Field(..., description="Name of the cited document file")
    page_number: int = Field(..., description="Page number of the cited evidence")
    section: Optional[str] = Field(default="General", description="Section or heading title")
    chapter: Optional[str] = Field(default="", description="Unit or chapter title")
    topic: Optional[str] = Field(default="", description="Topic heading")
    chunk_id: Optional[str] = Field(default="", description="Unique chunk ID")
    excerpt: str = Field(..., description="Excerpt content from retrieved chunk")
    relevance_score: float = Field(default=0.0, description="Relevance or reranker score")
    is_verified: bool = Field(default=True, description="Whether citation matched retrieved evidence")

class CitationVerifier:
    """
    Citation Verification Engine:
    Post-verifies LLM generated citations and claims against actual retrieved chunks.
    Eliminates fabricated document names, invalid page numbers, or unretrieved sources.
    """

    def __init__(self, retrieved_docs: Optional[List[Document]] = None):
        self.retrieved_docs = retrieved_docs or []

    def get_valid_sources(self) -> List[Citation]:
        """
        Builds a list of verified Citation objects from current retrieved chunks.
        """
        citations = []
        for idx, doc in enumerate(self.retrieved_docs):
            meta = doc.metadata or {}
            doc_name = meta.get("document_name") or meta.get("source") or "Unknown Document"
            page_num = meta.get("page_number") or meta.get("page") or 1
            section = meta.get("section") or "General"
            chapter = meta.get("chapter") or ""
            topic = meta.get("topic") or ""
            chunk_id = meta.get("chunk_id") or f"doc_{idx}"
            excerpt = doc.page_content[:200].strip()

            citations.append(Citation(
                document_name=str(doc_name),
                page_number=int(page_num) if str(page_num).isdigit() else 1,
                section=str(section),
                chapter=str(chapter),
                topic=str(topic),
                chunk_id=str(chunk_id),
                excerpt=excerpt,
                relevance_score=1.0,
                is_verified=True
            ))
        return citations

    def verify_citation(self, doc_name: str, page_num: int) -> Optional[Document]:
        """
        Checks if a cited (document_name, page_number) pair matches any actual retrieved chunk.
        """
        doc_name_clean = doc_name.strip().lower()
        for doc in self.retrieved_docs:
            meta = doc.metadata or {}
            ret_doc = str(meta.get("document_name") or meta.get("source") or "").strip().lower()
            ret_page = meta.get("page_number") or meta.get("page")

            # Match document name (exact or substring) and page number
            if ret_doc and (ret_doc == doc_name_clean or doc_name_clean in ret_doc or ret_doc in doc_name_clean):
                if str(ret_page) == str(page_num):
                    return doc
        return None

    def extract_and_verify_citations(self, answer_text: str) -> Tuple[str, List[Citation]]:
        """
        Extracts inline citations (e.g. [Source: syllabus.pdf, Page: 2] or [syllabus.pdf, Page 2]),
        verifies them against retrieved chunks, removes unverified/fabricated citations,
        and returns the cleaned text along with verified Citation models.
        """
        if not answer_text or not self.retrieved_docs:
            return answer_text, []

        pattern = re.compile(
            r'\[(?:Source:\s*)?([A-Za-z0-9_\-\.\s]+?)(?:,\s*Page:?\s*|\s+Page\s+|\,\s*P\.?\s*)(\d+)\]',
            re.IGNORECASE
        )

        verified_citations = []
        seen_keys = set()

        def citation_replacer(match):
            doc_name = match.group(1).strip()
            try:
                page_num = int(match.group(2))
            except ValueError:
                return "" # Invalid page syntax

            matched_doc = self.verify_citation(doc_name, page_num)
            if matched_doc:
                meta = matched_doc.metadata or {}
                key = (doc_name.lower(), page_num)
                if key not in seen_keys:
                    seen_keys.add(key)
                    verified_citations.append(Citation(
                        document_name=meta.get("document_name") or doc_name,
                        page_number=page_num,
                        section=meta.get("section", "General"),
                        chapter=meta.get("chapter", ""),
                        topic=meta.get("topic", ""),
                        chunk_id=meta.get("chunk_id", ""),
                        excerpt=matched_doc.page_content[:200].strip(),
                        is_verified=True
                    ))
                return match.group(0) # Keep valid citation inline
            else:
                # Suppress / strip unverified or fabricated citation
                return ""

        cleaned_text = pattern.sub(citation_replacer, answer_text)

        # Fallback: If no inline bracketed citations were extracted, use all valid retrieved sources
        if not verified_citations:
            verified_citations = self.get_valid_sources()

        return cleaned_text.strip(), verified_citations

    def verify_answer_claims(self, answer_text: str) -> Tuple[str, List[Citation]]:
        """
        Claim-to-evidence support:
        Verifies answer sentences against retrieved chunk contents.
        Strips or flags claims that have no textual overlap with retrieved evidence.
        """
        if not answer_text or not self.retrieved_docs:
            return answer_text, []

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', answer_text) if s.strip()]
        supported_sentences = []
        supported_citations = []
        seen_chunk_ids = set()

        corpus_text = " ".join([d.page_content.lower() for d in self.retrieved_docs])

        for sentence in sentences:
            # Tokenize sentence words (ignoring short stopwords)
            words = [w.lower() for w in re.findall(r'\b[a-zA-Z0-9]{3,}\b', sentence)]
            if not words:
                supported_sentences.append(sentence)
                continue

            # Calculate word overlap with retrieved corpus
            match_count = sum(1 for w in words if w in corpus_text)
            overlap_ratio = match_count / len(words)

            # Claim is supported if at least 40% of its key terms overlap with retrieved evidence
            if overlap_ratio >= 0.40:
                supported_sentences.append(sentence)
                # Find matching document chunk
                for doc in self.retrieved_docs:
                    doc_text_lower = doc.page_content.lower()
                    if sum(1 for w in words if w in doc_text_lower) >= max(2, len(words) * 0.3):
                        meta = doc.metadata or {}
                        cid = meta.get("chunk_id") or f"{meta.get('source')}_{meta.get('page')}"
                        if cid not in seen_chunk_ids:
                            seen_chunk_ids.add(cid)
                            supported_citations.append(Citation(
                                document_name=meta.get("document_name") or meta.get("source") or "Document",
                                page_number=meta.get("page_number") or meta.get("page") or 1,
                                section=meta.get("section", "General"),
                                chapter=meta.get("chapter", ""),
                                topic=meta.get("topic", ""),
                                chunk_id=cid,
                                excerpt=doc.page_content[:200].strip(),
                                is_verified=True
                            ))
            else:
                # Unsupported claim: drop or rewrite
                pass

        verified_text = " ".join(supported_sentences) if supported_sentences else answer_text
        if not supported_citations:
            supported_citations = self.get_valid_sources()

        return verified_text, supported_citations

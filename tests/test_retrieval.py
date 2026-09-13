import os
import sys
import unittest
from langchain_core.documents import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.embeddings import get_embeddings
from app.rag.ingestion import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

class TestRetrievalPipeline(unittest.TestCase):

    def test_text_splitting(self):
        docs = [
            Document(page_content="Unit 1 covers Introduction to Machine Learning. Linear regression, logistic regression, and evaluation metrics.", metadata={"source": "syllabus.pdf", "page": 1}),
            Document(page_content="Unit 2 covers Deep Learning and Neural Networks. Backpropagation, activation functions, and convolutional neural networks.", metadata={"source": "syllabus.pdf", "page": 2})
        ]
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        chunks = splitter.split_documents(docs)
        self.assertGreater(len(chunks), 0)
        self.assertIn("source", chunks[0].metadata)

    def test_vector_similarity_search(self):
        docs = [
            Document(page_content="The final exam will be held on December 15th and accounts for 40% of the grade.", metadata={"source": "syllabus.pdf", "page": 3}),
            Document(page_content="Office hours are held on Mondays and Wednesdays from 2 PM to 4 PM in Room 302.", metadata={"source": "syllabus.pdf", "page": 1})
        ]
        embeddings = get_embeddings()
        vector_store = FAISS.from_documents(docs, embeddings)
        
        results = vector_store.similarity_search("When is the final exam?", k=1)
        self.assertEqual(len(results), 1)
        self.assertIn("December 15th", results[0].page_content)

if __name__ == "__main__":
    unittest.main()

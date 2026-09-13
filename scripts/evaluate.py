#!/usr/bin/env python3
import io
import os
import sys
import time
import argparse

if sys.platform == "win32" and isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.pipeline import load_vector_store, retrieve_context

TEST_QUERIES = [
    "What is the grading policy and exam structure?",
    "List the required textbooks and course prerequisites.",
    "What topics are covered in Unit 2?",
    "How are late assignments handled?"
]

def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval performance and latency.")
    parser.add_argument("--k", type=int, default=4, help="Number of chunks to retrieve per query")
    args = parser.parse_args()

    print("[*] Loading FAISS Vector Store...")
    db = load_vector_store()
    if db is None:
        print("[!] Vector index is empty or missing. Please ingest documents first.")
        sys.exit(1)

    print(f"\n--- RAG Retrieval Benchmark (k={args.k}) ---")
    total_time = 0.0

    for idx, query in enumerate(TEST_QUERIES, 1):
        start = time.perf_counter()
        docs = retrieve_context(query, db, k=args.k)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        total_time += elapsed

        print(f"\nQuery {idx}: '{query}'")
        print(f"Retrieval Latency: {elapsed:.2f} ms")
        print(f"Retrieved Chunks: {len(docs)}")
        for doc_idx, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            snippet = doc.page_content[:80].replace("\n", " ")
            print(f"  [{doc_idx}] {source} (p. {page}): \"{snippet}...\"")

    avg_latency = total_time / len(TEST_QUERIES)
    print(f"\n[+] Evaluation Complete. Average Retrieval Latency: {avg_latency:.2f} ms")

if __name__ == "__main__":
    main()

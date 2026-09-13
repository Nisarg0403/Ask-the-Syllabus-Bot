#!/usr/bin/env python3
import os
import sys
import argparse

# Force UTF-8 encoding for standard output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path to allow app imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.config import DATA_DIR
from app.rag.ingestion import rebuild_vector_store

def main():
    parser = argparse.ArgumentParser(description="Ingest PDFs and build/update FAISS vector index.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Document chunk size in characters")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Document chunk overlap in characters")
    args = parser.parse_args()

    print(f"[*] Reading PDF documents from: {DATA_DIR}")
    db, num_chunks = rebuild_vector_store(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)

    if db is None:
        print("[!] No PDF documents found in data/documents directory.")
    else:
        print(f"[+] Successfully processed documents. Total chunks indexed: {num_chunks}")

if __name__ == "__main__":
    main()

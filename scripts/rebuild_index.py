#!/usr/bin/env python3
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.rag.ingestion import rebuild_vector_store

def main():
    print("[*] Rebuilding FAISS vector storage from data/documents/ ...")
    db, num_chunks = rebuild_vector_store()
    print(f"[+] Rebuild complete. Active chunks in FAISS index: {num_chunks}")

if __name__ == "__main__":
    main()

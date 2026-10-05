import sys
import os
sys.path.insert(0, os.path.abspath("."))

print("=== Step 1: Load CSV into DuckDB ===")
from src.ingestion.db_loader import load_to_duckdb
load_to_duckdb()

print("\n=== Step 2: Build RAG vector store ===")
from src.ingestion.rag_builder import build_vector_store
build_vector_store()

print("\nAll ingestion complete. Ready to run agent.")

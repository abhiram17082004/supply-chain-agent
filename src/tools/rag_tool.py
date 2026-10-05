import chromadb
from sentence_transformers import SentenceTransformer

VECTOR_PATH = "data/vector_store/"

_model = None
_collection = None


def _init():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        chroma = chromadb.PersistentClient(path=VECTOR_PATH)
        _collection = chroma.get_collection("supply_chain_knowledge")


def search_knowledge_base(query: str, n_results: int = 4) -> dict:
    """Search supply chain knowledge base semantically.
    Use for: market summaries, category profiles, shipping comparisons,
    customer segments, and any open-ended or conceptual questions."""
    _init()
    embedding = _model.encode([query]).tolist()
    results = _collection.query(
        query_embeddings=embedding,
        n_results=min(n_results, 10),
        include=["documents", "metadatas", "distances"]
    )
    return {
        "results": [
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "relevance_score": round(1 - dist, 3)
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]
    }

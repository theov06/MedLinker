"""RAG (Retrieval-Augmented Generation) module for MedLinker AI."""

from medlinker_ai.rag.faiss_store import (
    build_indexes,
    load_indexes,
    retrieve,
    is_rag_available
)

__all__ = [
    "build_indexes",
    "load_indexes", 
    "retrieve",
    "is_rag_available"
]

"""
RAG (Retrieval-Augmented Generation) MCP Server

Provides document indexing and semantic search capabilities.
Tools for adding documents, searching, and managing the knowledge base.
"""

from typing import Dict, Any, List

# Re-export tool functions
from .add_documents import add_documents
from .search_documents import search_documents
from .get_rag_stats import get_rag_stats
from .clear_rag_index import clear_rag_index

__all__ = [
    "add_documents",
    "search_documents",
    "get_rag_stats",
    "clear_rag_index",
]

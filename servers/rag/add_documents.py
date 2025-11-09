"""
Add documents to RAG index.

Tool: add_documents
Description: Index documents for semantic search and retrieval.
"""

from typing import Dict, Any, List, Optional
from servers.client import mcp_client


def add_documents(
    texts: List[str],
    source: str = "agent",
    metadatas: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Add documents to the RAG index for semantic search.
    
    Documents are automatically chunked, vectorized using embeddings,
    and stored in a FAISS index for fast similarity search.
    
    Args:
        texts: List of document texts to index
        source: Source identifier for tracking (default: "agent")
        metadatas: Optional list of metadata dicts (one per document)
    
    Returns:
        Result dictionary with structure:
        {
            "status": "success",
            "chunks_added": int,       # Number of chunks created
            "total_documents": int      # Total documents in index
        }
    
    Example:
        >>> # Add single document
        >>> result = add_documents(
        ...     texts=["Python is a high-level programming language."],
        ...     source="programming_guide"
        ... )
        >>> print(f"Added {result['chunks_added']} chunks")
        
        >>> # Add multiple documents with metadata
        >>> docs = [
        ...     "Machine learning uses statistical techniques.",
        ...     "Deep learning is a subset of machine learning."
        ... ]
        >>> metadata = [
        ...     {"topic": "ML", "difficulty": "beginner"},
        ...     {"topic": "DL", "difficulty": "intermediate"}
        ... ]
        >>> result = add_documents(texts=docs, source="ml_course", metadatas=metadata)
    
    Raises:
        ValueError: If texts list is empty
    """
    return mcp_client.call_tool("add_documents", {
        "texts": texts,
        "source": source,
        "metadatas": metadatas
    })

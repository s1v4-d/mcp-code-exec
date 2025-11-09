"""
Get RAG index statistics.

Tool: get_rag_stats
Description: Retrieve statistics about the RAG knowledge base.
"""

from typing import Dict, Any
from servers.client import mcp_client


def get_rag_stats() -> Dict[str, Any]:
    """
    Get statistics about the RAG index.
    
    Provides information about indexed documents, sources,
    and the embedding model used.
    
    Returns:
        Statistics dictionary with structure:
        {
            "total_documents": int,      # Total document chunks
            "sources": {                 # Count by source
                "source_name": int,
                ...
            },
            "index_dimension": int,      # Embedding dimension
            "embedding_model": str       # Model name
        }
    
    Example:
        >>> stats = get_rag_stats()
        >>> print(f"Total documents: {stats['total_documents']}")
        >>> print(f"Embedding model: {stats['embedding_model']}")
        >>> print("Documents by source:")
        >>> for source, count in stats['sources'].items():
        ...     print(f"  {source}: {count}")
    """
    return mcp_client.call_tool("get_rag_stats", {})

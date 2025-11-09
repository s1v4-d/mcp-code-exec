"""
Search documents in RAG index.

Tool: search_documents
Description: Perform semantic similarity search over indexed documents.
"""

from typing import Dict, Any, List
from servers.client import mcp_client


async def search_documents(query: str, k: int = 4) -> List[Dict[str, Any]]:
    """
    Search for similar documents using semantic similarity.
    
    Uses vector embeddings to find documents semantically similar
    to the query, not just keyword matching.
    
    Args:
        query: Search query text
        k: Number of results to return (default: 4, max: 20)
    
    Returns:
        List of result dictionaries, each with structure:
        {
            "text": str,           # Document chunk text
            "metadata": {          # Metadata from indexing
                "source": str,
                "doc_index": int,
                "chunk_index": int,
                "timestamp": str,
                ...                # Any custom metadata
            },
            "score": float         # Similarity score (lower = more similar)
        }
        
        Results are sorted by similarity (most similar first).
    
    Example:
        >>> # Basic search
        >>> results = await search_documents("What is Python?", k=3)
        >>> for i, result in enumerate(results, 1):
        ...     print(f"{i}. {result['text'][:100]}...")
        ...     print(f"   Score: {result['score']:.4f}")
        ...     print(f"   Source: {result['metadata']['source']}")
        
        >>> # Search and filter by metadata
        >>> results = await search_documents("machine learning algorithms", k=5)
        >>> ml_results = [r for r in results if r['metadata'].get('topic') == 'ML']
    
    Returns:
        Empty list if no documents in index
    """
    return await mcp_client.call_tool("search_documents", {
        "query": query,
        "k": k
    })

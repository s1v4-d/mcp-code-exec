"""
Clear RAG index.

Tool: clear_rag_index
Description: Delete all documents from the RAG knowledge base.
"""

from typing import Dict, Any
from servers.client import mcp_client


async def clear_rag_index() -> Dict[str, str]:
    """
    Clear the entire RAG index.
    
    **WARNING**: This deletes ALL documents from the knowledge base.
    This operation cannot be undone.
    
    Returns:
        Confirmation dictionary with structure:
        {
            "status": "success",
            "message": "Index cleared"
        }
    
    Example:
        >>> # Clear all documents
        >>> result = await clear_rag_index()
        >>> print(result['message'])
        
        >>> # Verify it's cleared
        >>> stats = await get_rag_stats()
        >>> print(f"Documents remaining: {stats['total_documents']}")
    """
    return await mcp_client.call_tool("clear_rag_index", {})

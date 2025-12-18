from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SearchDocumentsParams(BaseModel):
    """Parameters for search_documents."""
    query: str = Field(description="Search query")
    top_k: Optional[int] | None = Field(description="Number of results to return")


async def search_documents(params: SearchDocumentsParams) -> Dict[str, Any]:
    """
    Search for documents in the RAG index
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "rag__search_documents",
        params.model_dump(exclude_none=True)
    )
    
    return result

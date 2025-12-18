from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ClearRagIndexParams(BaseModel):
    """Parameters for clear_rag_index."""
    pass


async def clear_rag_index(params: ClearRagIndexParams) -> Dict[str, Any]:
    """
    Clear all documents from the RAG index
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "rag__clear_rag_index",
        params.model_dump(exclude_none=True)
    )
    
    return result

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GetRagStatsParams(BaseModel):
    """Parameters for get_rag_stats."""
    pass


async def get_rag_stats(params: GetRagStatsParams) -> Dict[str, Any]:
    """
    Get statistics about the RAG index
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "rag__get_rag_stats",
        params.model_dump(exclude_none=True)
    )
    
    return result

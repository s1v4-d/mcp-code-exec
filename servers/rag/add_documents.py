from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AddDocumentsParams(BaseModel):
    """Parameters for add_documents."""
    documents: List[Any] = Field(description="List of documents to add")


async def add_documents(params: AddDocumentsParams) -> Dict[str, Any]:
    """
    Add documents to the RAG index
    
    Args:
        params: Tool parameters
        
    Returns:
        Tool execution result
    """
    from app.runtime.mcp_manager import call_tool
    
    result = await call_tool(
        "rag__add_documents",
        params.model_dump(exclude_none=True)
    )
    
    return result

"""RAG API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.rag.service import rag_service

router = APIRouter()


class AddDocumentsRequest(BaseModel):
    """Request to add documents."""
    texts: List[str] = Field(..., description="List of document texts to add")
    source: str = Field(default="api", description="Source identifier")
    metadatas: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional metadata")


class SearchRequest(BaseModel):
    """Request to search documents."""
    query: str = Field(..., description="Search query")
    k: int = Field(default=5, description="Number of results", ge=1, le=20)


@router.post("/add")
async def add_documents(request: AddDocumentsRequest) -> Dict[str, Any]:
    """Add documents to RAG index via API."""
    if not rag_service.is_ready:
        raise HTTPException(status_code=503, detail="RAG service not initialized. Check OPENAI_API_KEY.")
    
    result = rag_service.add_documents(
        texts=request.texts,
        source=request.source,
        metadatas=request.metadatas
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return result


@router.post("/search")
async def search_documents(request: SearchRequest) -> Dict[str, Any]:
    """Search RAG index."""
    if not rag_service.is_ready:
        raise HTTPException(status_code=503, detail="RAG service not initialized. Check OPENAI_API_KEY.")
    
    results = rag_service.search(query=request.query, k=request.k)
    
    return {
        "query": request.query,
        "results": results,
        "count": len(results)
    }


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get RAG index statistics."""
    if not rag_service.is_ready:
        raise HTTPException(status_code=503, detail="RAG service not initialized. Check OPENAI_API_KEY.")
    
    return rag_service.get_stats()


@router.post("/clear")
async def clear_index() -> Dict[str, Any]:
    """Clear RAG index (WARNING: Deletes all documents)."""
    if not rag_service.is_ready:
        raise HTTPException(status_code=503, detail="RAG service not initialized. Check OPENAI_API_KEY.")
    
    return rag_service.clear_index()

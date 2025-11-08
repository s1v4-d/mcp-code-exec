"""RAG API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile

from app.rag.document_store import DocumentStore, RAGRetriever
from app.config import settings

router = APIRouter()

# Initialize document store
doc_store = DocumentStore(
    index_path=settings.rag_index_path,
    openai_api_key=settings.openai_api_key
)

# Initialize retriever
retriever = RAGRetriever(doc_store)


class DocumentAddRequest(BaseModel):
    """Request to add documents."""
    texts: List[str] = Field(..., description="List of text documents to add")
    metadatas: Optional[List[Dict[str, Any]]] = Field(None, description="Optional metadata for each document")
    source: str = Field(default="api", description="Source identifier")


class DocumentAddResponse(BaseModel):
    """Response after adding documents."""
    status: str
    chunks_added: int
    total_documents: int
    source: str


class SearchRequest(BaseModel):
    """Request to search documents."""
    query: str = Field(..., description="Search query")
    k: int = Field(default=4, description="Number of results to return", ge=1, le=20)
    filter_source: Optional[str] = Field(None, description="Filter by source")


class SearchResult(BaseModel):
    """Single search result."""
    content: str
    metadata: Dict[str, Any]
    score: float


class SearchResponse(BaseModel):
    """Response from document search."""
    query: str
    results: List[SearchResult]
    total_results: int


class ContextRequest(BaseModel):
    """Request to get context for RAG."""
    query: str = Field(..., description="Query to get context for")
    k: int = Field(default=4, description="Number of documents to retrieve", ge=1, le=20)


class ContextResponse(BaseModel):
    """Response with context."""
    query: str
    context: str
    num_documents: int


class IndexStatsResponse(BaseModel):
    """Index statistics."""
    total_chunks: int
    sources: List[str]
    source_details: Dict[str, Any]


@router.post("/documents/add", response_model=DocumentAddResponse)
async def add_documents(request: DocumentAddRequest) -> DocumentAddResponse:
    """
    Add documents to the RAG index.
    
    Accepts a list of text documents and optional metadata.
    Documents are chunked and indexed for similarity search.
    """
    try:
        chunks_added = document_store.add_documents(
            texts=request.texts,
            metadatas=request.metadatas,
            source=request.source
        )
        
        return DocumentAddResponse(
            status="success",
            chunks_added=chunks_added,
            total_documents=document_store.get_document_count(),
            source=request.source
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...), source: Optional[str] = None):
    """
    Upload a text file to the RAG index.
    
    Supports .txt, .md, and other text formats.
    """
    try:
        # Check file type
        if not file.filename.endswith(('.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.xml')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload text-based files."
            )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        # Add to document store
        try:
            chunks_added = document_store.add_text_file(
                file_path=tmp_path,
                source=source or file.filename
            )
            
            return DocumentAddResponse(
                status="success",
                chunks_added=chunks_added,
                total_documents=document_store.get_document_count(),
                source=source or file.filename
            )
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """
    Search for similar documents.
    
    Uses vector similarity search to find relevant documents
    based on the query.
    """
    try:
        results = retriever.retrieve(
            query=request.query,
            k=request.k
        )
        
        # Filter by source if specified
        if request.filter_source:
            results = [r for r in results if r['metadata'].get('source') == request.filter_source]
        
        search_results = [
            SearchResult(
                content=r['content'],
                metadata=r['metadata'],
                score=r['score']
            )
            for r in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest) -> ContextResponse:
    """
    Get concatenated context for RAG.
    
    Retrieves relevant documents and combines them into a single
    context string suitable for providing to an LLM.
    """
    try:
        context = retriever.get_context(
            query=request.query,
            k=request.k
        )
        
        num_docs = len(context.split("[Source")) - 1 if context else 0
        
        return ContextResponse(
            query=request.query,
            context=context,
            num_documents=num_docs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=IndexStatsResponse)
async def get_stats() -> IndexStatsResponse:
    """
    Get statistics about the RAG index.
    
    Returns total chunk count, sources, and per-source details.
    """
    try:
        sources = document_store.get_sources()
        source_details = {
            source: document_store.get_source_info(source)
            for source in sources
        }
        
        return IndexStatsResponse(
            total_chunks=document_store.get_document_count(),
            sources=sources,
            source_details=source_details
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index")
async def clear_index():
    """
    Clear the entire RAG index.
    
    WARNING: This deletes all indexed documents.
    """
    try:
        document_store.clear_index()
        return {"status": "success", "message": "Index cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/source/{source}")
async def delete_source(source: str):
    """
    Delete all documents from a specific source.
    
    Note: This requires rebuilding the index.
    """
    try:
        document_store.delete_source(source)
        return {"status": "success", "message": f"Source '{source}' deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

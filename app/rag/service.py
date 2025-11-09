"""RAG Service - Centralized embedding and indexing service."""

from pathlib import Path
from typing import List, Dict, Any, Optional

from app.rag.document_store import DocumentStore
from app.config import settings
from app.exceptions import RAGError, ConfigurationError


class RAGService:
    """Centralized RAG service for embedding and indexing."""
    
    _instance: Optional['RAGService'] = None
    _doc_store: Optional[DocumentStore] = None
    
    def __new__(cls):
        """Singleton pattern for RAG service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize RAG service."""
        if self._doc_store is None:
            self._initialize_store()
    
    def _initialize_store(self):
        """
        Initialize document store.
        
        Raises:
            ConfigurationError: If OpenAI API key is not configured
        """
        index_path = Path("data/rag_index")
        index_path.mkdir(parents=True, exist_ok=True)
        
        if not settings.openai_api_key or settings.openai_api_key == "your-api-key-here":
            raise ConfigurationError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )
        
        self._doc_store = DocumentStore(
            index_path=index_path,
            openai_api_key=settings.openai_api_key
        )
    
    @property
    def is_ready(self) -> bool:
        """Check if RAG service is ready."""
        return self._doc_store is not None
    
    async def add_documents(self, texts: List[str], source: str = "unknown",
                     metadatas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Add documents to the index.
        
        Args:
            texts: List of text documents to index
            source: Source identifier
            metadatas: Optional metadata for each document
            
        Returns:
            Dictionary with success status and count
            
        Raises:
            RAGError: If RAG service is not initialized or operation fails
        """
        if not self.is_ready:
            raise RAGError("RAG service not initialized. Check OPENAI_API_KEY.")
        
        return await self._doc_store.add_documents(texts, source, metadatas)
    
    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of matching documents with scores
            
        Raises:
            RAGError: If RAG service is not initialized or search fails
        """
        if not self.is_ready:
            raise RAGError("RAG service not initialized. Check OPENAI_API_KEY.")
        
        return await self._doc_store.search(query, k)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dictionary with document count and other stats
            
        Raises:
            RAGError: If RAG service is not initialized
        """
        if not self.is_ready:
            raise RAGError("RAG service not initialized. Check OPENAI_API_KEY.")
        
        return await self._doc_store.get_stats()
    
    async def clear_index(self) -> Dict[str, Any]:
        """
        Clear all documents.
        
        Returns:
            Dictionary with success status
            
        Raises:
            RAGError: If RAG service is not initialized or operation fails
        """
        if not self.is_ready:
            raise RAGError("RAG service not initialized. Check OPENAI_API_KEY.")
        
        return await self._doc_store.clear_index()


# Global RAG service instance
rag_service = RAGService()

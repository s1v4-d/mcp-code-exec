"""RAG tool for MCP - Document retrieval and search."""

from typing import Dict, Any, List
from pathlib import Path

from app.rag.service import rag_service
from app.exceptions import RAGError


class RAGTool:
    """RAG tool for MCP using centralized RAG service."""
    
    async def add_documents(self, texts: List[str], source: str = "agent", 
                     metadatas: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add documents to the RAG index.
        
        Args:
            texts: List of text documents to index
            source: Source identifier
            metadatas: Optional metadata for each document
            
        Returns:
            Dictionary with success status and count
            
        Raises:
            RAGError: If document addition fails
        """
        print(f"[RAG Tool] Adding {len(texts)} documents (source: {source})")
        return await rag_service.add_documents(texts, source, metadatas)
    
    async def search_documents(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of matching documents with scores
            
        Raises:
            RAGError: If search fails
        """
        print(f"[RAG Tool] Searching: '{query}' (k={k})")
        return await rag_service.search(query, k)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG index statistics.
        
        Returns:
            Dictionary with document count and other stats
        """
        print("[RAG Tool] Getting stats")
        return await rag_service.get_stats()
    
    async def clear_index(self) -> Dict[str, str]:
        """
        Clear the RAG index.
        
        Returns:
            Dictionary with success status
            
        Raises:
            RAGError: If clearing fails
        """
        print("[RAG Tool] Clearing index")
        return await rag_service.clear_index()
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        return {
            "add_documents": {
                "description": "Add documents to the RAG index for semantic search. Documents are chunked and vectorized.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of text documents to index"
                        },
                        "source": {
                            "type": "string",
                            "description": "Source identifier",
                            "default": "agent"
                        },
                        "metadatas": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Optional metadata for each document"
                        }
                    },
                    "required": ["texts"]
                },
                "function": self.add_documents
            },
            "search_documents": {
                "description": "Search for similar documents using semantic similarity.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of results",
                            "default": 4
                        }
                    },
                    "required": ["query"]
                },
                "function": self.search_documents
            },
            "get_rag_stats": {
                "description": "Get RAG index statistics.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                },
                "function": self.get_stats
            },
            "clear_rag_index": {
                "description": "Clear the entire RAG index (WARNING: Deletes all documents).",
                "parameters": {
                    "type": "object",
                    "properties": {}
                },
                "function": self.clear_index
            }
        }

"""RAG tool for MCP - Document retrieval and search."""

from typing import Dict, Any, List
from pathlib import Path

from app.rag.document_store import DocumentStore, RAGRetriever
from app.config import settings


class RAGTool:
    """
    RAG (Retrieval-Augmented Generation) tool for MCP.
    
    Provides document indexing, semantic search, and context retrieval
    for augmenting LLM responses with relevant information.
    """
    
    def __init__(self):
        """Initialize RAG tool with document store."""
        self.doc_store = DocumentStore(
            index_path=settings.rag_index_path,
            openai_api_key=settings.openai_api_key
        )
        self.retriever = RAGRetriever(self.doc_store)
    
    def add_documents(self, texts: List[str], source: str = "agent", 
                     metadatas: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Add documents to the RAG index.
        
        Args:
            texts: List of text documents to index
            source: Source identifier for these documents
            metadatas: Optional metadata for each document
            
        Returns:
            Dictionary with status and chunk count
        """
        print(f"[RAG Tool] Adding {len(texts)} documents to index (source: {source})")
        
        chunks_added = self.document_store.add_documents(
            texts=texts,
            metadatas=metadatas,
            source=source
        )
        
        return {
            "status": "success",
            "chunks_added": chunks_added,
            "total_documents": self.document_store.get_document_count(),
            "source": source
        }
    
    def search_documents(self, query: str, k: int = 4, 
                        filter_source: str = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using semantic search.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_source: Optional source filter
            
        Returns:
            List of search results with content, metadata, and scores
        """
        print(f"[RAG Tool] Searching for: '{query}' (k={k})")
        
        results = self.retriever.retrieve(query=query, k=k)
        
        # Filter by source if specified
        if filter_source:
            results = [r for r in results if r['metadata'].get('source') == filter_source]
        
        return results
    
    def get_context(self, query: str, k: int = 4) -> str:
        """
        Get concatenated context from retrieved documents.
        
        Useful for providing context to LLMs.
        
        Args:
            query: Query to retrieve context for
            k: Number of documents to retrieve
            
        Returns:
            Formatted context string
        """
        print(f"[RAG Tool] Getting context for: '{query}'")
        
        context = self.retriever.get_context(query=query, k=k)
        
        return context
    
    def add_file(self, file_path: str, source: str = None) -> Dict[str, Any]:
        """
        Add a text file to the RAG index.
        
        Args:
            file_path: Path to the text file
            source: Optional source identifier
            
        Returns:
            Dictionary with status and chunk count
        """
        file_path = Path(file_path)
        
        print(f"[RAG Tool] Adding file: {file_path}")
        
        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_path}",
                "chunks_added": 0
            }
        
        try:
            chunks_added = self.document_store.add_text_file(
                file_path=file_path,
                source=source or file_path.name
            )
            
            return {
                "status": "success",
                "chunks_added": chunks_added,
                "total_documents": self.document_store.get_document_count(),
                "source": source or file_path.name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "chunks_added": 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get RAG index statistics.
        
        Returns:
            Dictionary with total chunks, sources, and source details
        """
        print("[RAG Tool] Getting index statistics")
        
        sources = self.document_store.get_sources()
        source_details = {
            source: self.document_store.get_source_info(source)
            for source in sources
        }
        
        return {
            "total_chunks": self.document_store.get_document_count(),
            "sources": sources,
            "source_details": source_details
        }
    
    def clear_index(self) -> Dict[str, str]:
        """
        Clear the entire RAG index.
        
        WARNING: This deletes all indexed documents.
        
        Returns:
            Status message
        """
        print("[RAG Tool] Clearing index")
        
        self.document_store.clear_index()
        
        return {
            "status": "success",
            "message": "Index cleared successfully"
        }
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Get tool definitions for MCP registration.
        
        Returns:
            Dictionary of tool definitions
        """
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
                            "description": "Source identifier for tracking",
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
                "description": "Search for similar documents using semantic similarity. Returns relevant documents with scores.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 4
                        },
                        "filter_source": {
                            "type": "string",
                            "description": "Optional source filter"
                        }
                    },
                    "required": ["query"]
                },
                "function": self.search_documents
            },
            "get_context": {
                "description": "Get formatted context from retrieved documents for LLM prompts. Returns concatenated relevant text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query to retrieve context for"
                        },
                        "k": {
                            "type": "integer",
                            "description": "Number of documents to retrieve",
                            "default": 4
                        }
                    },
                    "required": ["query"]
                },
                "function": self.get_context
            },
            "add_file": {
                "description": "Add a text file to the RAG index. Supports .txt, .md, .py, .json, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the text file to index"
                        },
                        "source": {
                            "type": "string",
                            "description": "Optional source identifier"
                        }
                    },
                    "required": ["file_path"]
                },
                "function": self.add_file
            },
            "get_rag_stats": {
                "description": "Get statistics about the RAG index including total documents, sources, and chunk counts.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                },
                "function": self.get_stats
            }
        }

from typing import Protocol, runtime_checkable
from pathlib import Path

from app.rag.models import SearchResult, IndexStats, OperationResult


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding generation."""
    
    def embed_text(self, text: str) -> list[float]:
        ...
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector storage operations."""
    
    def add(self, embeddings: list[list[float]], metadata: list[dict]) -> None:
        ...
    
    def search(self, query_embedding: list[float], k: int) -> tuple[list[int], list[float]]:
        ...
    
    def clear(self) -> None:
        ...
    
    def save(self, path: Path) -> None:
        ...
    
    def load(self, path: Path) -> None:
        ...


@runtime_checkable
class DocumentStore(Protocol):
    """Protocol for document storage and retrieval."""
    
    def add_documents(
        self,
        texts: list[str],
        source: str = "unknown",
        metadatas: list[dict] | None = None,
    ) -> OperationResult:
        ...
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_source: str | None = None,
    ) -> list[SearchResult]:
        ...
    
    def get_stats(self) -> IndexStats:
        ...
    
    def clear_index(self) -> OperationResult:
        ...
    
    def delete_by_source(self, source: str) -> OperationResult:
        ...


@runtime_checkable
class Retriever(Protocol):
    """Protocol for RAG retrieval operations."""
    
    def get_context(self, query: str, k: int = 3) -> str:
        ...

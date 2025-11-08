from pydantic import BaseModel, Field, ConfigDict
from typing import Any


class DocumentChunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    text: str
    source: str
    doc_index: int = Field(ge=0)
    chunk_index: int = Field(ge=0)
    timestamp: str


class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    text: str
    metadata: dict[str, Any]
    score: float = Field(ge=0.0)


class IndexStats(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    total_documents: int = Field(ge=0)
    sources: dict[str, int]
    index_dimension: int
    embedding_model: str


class OperationResult(BaseModel):
    status: str = Field(pattern="^(success|error)$")
    message: str = ""
    chunks_added: int = Field(default=0, ge=0)
    total_documents: int = Field(default=0, ge=0)
    deleted_count: int = Field(default=0, ge=0)
    remaining_documents: int = Field(default=0, ge=0)

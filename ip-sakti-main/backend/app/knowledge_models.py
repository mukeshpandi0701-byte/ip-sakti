from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    authority: str = Field(..., min_length=1)
    jurisdiction: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    chunk_index: int = Field(..., ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    document_id: str = Field(..., min_length=1)
    chunk_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    excerpt: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    authority: str = Field(..., min_length=1)
    relevance_score: float = Field(..., ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = True

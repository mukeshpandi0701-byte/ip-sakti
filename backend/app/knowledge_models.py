from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunk(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    chunk_id: str = Field(..., alias="id", min_length=1)
    document_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    chunk_index: int = Field(..., ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def id(self) -> str:
        """Backward-compatible accessor for the original chunk field name."""
        return self.chunk_id


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    document_id: str = Field(..., alias="id", min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1)
    authority: str = Field(..., min_length=1)
    jurisdiction: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    publication_date: date | None = None
    last_updated: date | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunks: list[DocumentChunk] = Field(default_factory=list)

    @property
    def id(self) -> str:
        """Backward-compatible accessor for the original document field name."""
        return self.document_id


class Evidence(BaseModel):
    document_id: str = Field(..., min_length=1)
    chunk_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    excerpt: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    authority: str = Field(..., min_length=1)
    source_type: str = Field(default="unknown", min_length=1)
    relevance_score: float = Field(..., ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = True

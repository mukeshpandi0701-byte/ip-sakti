from pydantic import BaseModel, Field

from app.knowledge_models import Evidence


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class EvidenceItem(BaseModel):
    title: str
    citation: str
    excerpt: str
    is_demo: bool = True


class QueryResponse(BaseModel):
    answer: str
    evidence: list[Evidence]
    grounded: bool = False
    provider: str = "fallback"
    confidence: float = Field(default=0, ge=0, le=1)
    is_demo: bool = True
    disclaimer: str

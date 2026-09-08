from typing import Literal

from pydantic import BaseModel, Field

from app.classification_models import ClassificationResult
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
    evidence_status: Literal["sufficient", "insufficient"] = "insufficient"
    provider: str = "fallback"
    classification: ClassificationResult
    confidence: float = Field(
        default=0,
        ge=0,
        le=1,
        description=(
            "Heuristic confidence in the generated answer based on available evidence; "
            "it is always 0 when evidence_status is insufficient and is not legal certainty."
        ),
    )
    is_demo: bool = True
    disclaimer: str

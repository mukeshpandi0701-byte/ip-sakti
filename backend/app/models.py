from typing import Literal

from pydantic import BaseModel, Field

from app.classification_models import ClassificationResult
from app.knowledge_models import Evidence
from app.user_evidence_models import UserEvidence


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    response_language: Literal["en", "ta", "hi"] = "en"
    jurisdiction: Literal["india", "international"] = "india"


class EvidenceItem(BaseModel):
    title: str
    citation: str
    excerpt: str
    is_demo: bool = True


class QueryResponse(BaseModel):
    answer: str
    evidence: list[Evidence]
    user_evidence: list[UserEvidence] = Field(default_factory=list)
    classification: ClassificationResult = Field(default_factory=lambda: ClassificationResult(
        intent="UNKNOWN",
        category="UNKNOWN",
        confidence=0,
    ))
    grounded: bool = False
    evidence_status: Literal["sufficient", "insufficient"] = "insufficient"
    provider: str = "fallback"
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


class UserEvidenceIntakeResponse(BaseModel):
    user_evidence: list[UserEvidence] = Field(default_factory=list)

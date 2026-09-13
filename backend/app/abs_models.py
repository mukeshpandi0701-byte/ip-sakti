from enum import Enum

from pydantic import BaseModel, Field


class ABSRelevance(str, Enum):
    """Access and Benefit Sharing relevance status."""
    RELEVANT = "relevant"
    POSSIBLY_RELEVANT = "possibly_relevant"
    NOT_DETECTED = "not_detected"
    UNKNOWN = "unknown"


class ABSResult(BaseModel):
    """Result of Access and Benefit Sharing (ABS) consideration analysis."""
    relevance: ABSRelevance = Field(..., description="Whether ABS considerations are relevant")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in ABS relevance assessment (0-1)")
    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons why ABS is/isn't considered relevant"
    )
    considerations: list[str] = Field(
        default_factory=list,
        description="Relevant ABS considerations for this query/product"
    )

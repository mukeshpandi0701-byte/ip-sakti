from enum import Enum

from pydantic import BaseModel, Field


class TKDetection(str, Enum):
    """Traditional Knowledge detection status."""
    DETECTED = "detected"
    POSSIBLY_DETECTED = "possibly_detected"
    NOT_DETECTED = "not_detected"
    UNKNOWN = "unknown"


class TKResult(BaseModel):
    """Result of Traditional Knowledge analysis."""
    detected: TKDetection = Field(..., description="Whether traditional knowledge is detected")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in TK detection (0-1)")
    reasons: list[str] = Field(
        default_factory=list,
        description="Reasons why TK is/isn't detected"
    )
    considerations: list[str] = Field(
        default_factory=list,
        description="Relevant TK considerations for this query/product"
    )
    source_status: str = Field(
        default="unknown",
        description="Status of TK sources (e.g., 'demo_unavailable' if TKDL is not actually queried)"
    )

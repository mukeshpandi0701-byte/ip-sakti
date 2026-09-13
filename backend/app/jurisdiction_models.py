from enum import Enum

from pydantic import BaseModel, Field


class Jurisdiction(str, Enum):
    """Supported jurisdiction contexts for IP/regulatory routing."""
    INDIA = "india"
    USA = "usa"
    EU = "eu"
    INTERNATIONAL = "international"
    UNKNOWN = "unknown"


class JurisdictionResult(BaseModel):
    """Result of jurisdiction determination for a query/product context."""
    jurisdiction: Jurisdiction = Field(..., description="Determined jurisdiction context")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in jurisdiction determination (0-1)")
    reason: str = Field(..., min_length=1, description="Explanation of how jurisdiction was determined")
    source_scope: list[str] = Field(
        default_factory=list,
        description="Document/source scope filters for retrieval (e.g., ['india'], ['eu'], etc.)"
    )

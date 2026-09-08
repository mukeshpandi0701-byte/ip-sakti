"""Typed models used by deterministic query classification."""

from enum import Enum

from pydantic import BaseModel, Field


class QueryCategory(str, Enum):
    PATENT = "PATENT"
    TRADEMARK = "TRADEMARK"
    COPYRIGHT = "COPYRIGHT"
    TRADITIONAL_KNOWLEDGE = "TRADITIONAL_KNOWLEDGE"
    REGULATORY = "REGULATORY"
    GENERAL_IP = "GENERAL_IP"
    UNKNOWN = "UNKNOWN"


class QueryIntent(str, Enum):
    IP_PROTECTION = "IP_PROTECTION"
    IP_SEARCH = "IP_SEARCH"
    REGULATORY_REQUIREMENT = "REGULATORY_REQUIREMENT"
    TRADITIONAL_KNOWLEDGE = "TRADITIONAL_KNOWLEDGE"
    GENERAL_INFORMATION = "GENERAL_INFORMATION"
    UNKNOWN = "UNKNOWN"


class ClassificationResult(BaseModel):
    """Heuristic classification metadata, not legal certainty or a probability."""

    intent: QueryIntent
    category: QueryCategory
    confidence: float = Field(
        ge=0,
        le=1,
        description=(
            "Deterministic heuristic confidence: 0.95 for direct category and intent "
            "matches, 0.80 for a direct category-only match, and 0 for unknown input. "
            "This is not legal certainty or a statistical probability."
        ),
    )
    retrieval_domain: str = Field(
        default="general",
        description="Deterministic retrieval domain selected from the query category.",
    )
    source_types: list[str] = Field(
        default_factory=list,
        description=(
            "Preferred source types for retrieval. These are conservative hints, not "
            "a requirement that can suppress all available evidence."
        ),
    )

from enum import Enum

from pydantic import BaseModel, Field


class ClassificationCategory(str, Enum):
    PATENT = "PATENT"
    TRADEMARK = "TRADEMARK"
    COPYRIGHT = "COPYRIGHT"
    TRADITIONAL_KNOWLEDGE = "TRADITIONAL_KNOWLEDGE"
    REGULATORY = "REGULATORY"
    GENERAL_IP = "GENERAL_IP"
    UNKNOWN = "UNKNOWN"


class ClassificationIntent(str, Enum):
    IP_PROTECTION = "IP_PROTECTION"
    IP_SEARCH = "IP_SEARCH"
    REGULATORY_REQUIREMENT = "REGULATORY_REQUIREMENT"
    TRADITIONAL_KNOWLEDGE = "TRADITIONAL_KNOWLEDGE"
    GENERAL_INFORMATION = "GENERAL_INFORMATION"
    UNKNOWN = "UNKNOWN"


class ClassificationResult(BaseModel):
    intent: ClassificationIntent
    category: ClassificationCategory
    confidence: float = Field(..., ge=0, le=1)

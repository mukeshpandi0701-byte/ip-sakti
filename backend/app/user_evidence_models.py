from typing import Any, Literal

from pydantic import BaseModel, Field


ExtractionStatus = Literal["extracted", "unsupported", "failed", "image_pending", "image_only"]


class UserEvidencePage(BaseModel):
    page_number: int = Field(..., ge=1)
    extracted_text: str = ""


class UserEvidence(BaseModel):
    file_id: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    media_type: str = Field(default="application/octet-stream")
    file_size: int = Field(..., ge=0)
    extracted_text: str | None = None
    extraction_status: ExtractionStatus
    source_type: str = "user_upload"
    metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[UserEvidencePage] = Field(default_factory=list)

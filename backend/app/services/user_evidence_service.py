from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader

from app.user_evidence_models import UserEvidence, UserEvidencePage


MAX_FILES = 5
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

SUPPORTED_DOCUMENTS = {".pdf", ".txt", ".docx"}
SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}


class UserEvidenceValidationError(ValueError):
    """Raised when an upload violates an intake safety limit."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class UserEvidenceService:
    """Extract supported document text without persistent storage or OCR."""

    def process_files(
        self,
        files: list[tuple[str, str, bytes]],
    ) -> tuple[list[UserEvidence], str | None]:
        if len(files) > MAX_FILES:
            raise UserEvidenceValidationError(f"A maximum of {MAX_FILES} files is allowed.")

        evidence_items = [self._process_file(filename, media_type, content) for filename, media_type, content in files]
        context_parts = [
            f"User-provided document: {item.filename}\n{item.extracted_text}"
            for item in evidence_items
            if item.extraction_status == "extracted" and item.extracted_text
        ]
        return evidence_items, "\n\n".join(context_parts) or None

    def _process_file(self, filename: str, media_type: str, content: bytes) -> UserEvidence:
        file_size = len(content)
        if file_size == 0:
            raise UserEvidenceValidationError(f"File '{filename}' is empty.")
        if file_size > MAX_FILE_SIZE_BYTES:
            raise UserEvidenceValidationError(
                f"File '{filename}' exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit.",
                status_code=413,
            )

        extension = Path(filename).suffix.casefold()
        file_id = uuid4().hex
        if extension in SUPPORTED_IMAGES:
            return UserEvidence(
                file_id=file_id,
                filename=filename,
                media_type=media_type,
                file_size=file_size,
                extracted_text=None,
                extraction_status="image_pending",
                metadata={"image_analysis": "not_available"},
            )
        if extension not in SUPPORTED_DOCUMENTS:
            return UserEvidence(
                file_id=file_id,
                filename=filename,
                media_type=media_type,
                file_size=file_size,
                extracted_text=None,
                extraction_status="unsupported",
            )

        try:
            pages: list[UserEvidencePage] = []
            if extension == ".txt":
                extracted_text = content.decode("utf-8", errors="replace")
            elif extension == ".pdf":
                if not content.startswith(b"%PDF-"):
                    raise ValueError("Invalid PDF header")
                for page_number, page in enumerate(PdfReader(BytesIO(content)).pages, start=1):
                    pages.append(UserEvidencePage(page_number=page_number, extracted_text=page.extract_text() or ""))
                extracted_text = "\n\n".join(
                    f"--- Page {page.page_number} ---\n{page.extracted_text.strip()}"
                    for page in pages
                    if page.extracted_text.strip()
                ).strip()
                if not extracted_text:
                    return UserEvidence(
                        file_id=file_id,
                        filename=filename,
                        media_type=media_type,
                        file_size=file_size,
                        extracted_text=None,
                        extraction_status="image_only",
                        metadata={"ocr": "not_available"},
                        pages=pages,
                    )
            else:
                if not content.startswith(b"PK"):
                    raise ValueError("Invalid DOCX container")
                document = Document(BytesIO(content))
                extracted_text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
                if not extracted_text:
                    raise ValueError("DOCX contains no extractable paragraph text")
        except Exception:
            return UserEvidence(
                file_id=file_id,
                filename=filename,
                media_type=media_type,
                file_size=file_size,
                extracted_text=None,
                extraction_status="failed",
            )

        return UserEvidence(
            file_id=file_id,
            filename=filename,
            media_type=media_type,
            file_size=file_size,
            extracted_text=extracted_text,
            extraction_status="extracted",
            pages=pages,
        )

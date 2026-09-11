import sys
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfWriter


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402
from app.services.user_evidence_service import (  # noqa: E402
    MAX_FILE_SIZE_BYTES,
    MAX_FILES,
    UserEvidenceService,
    UserEvidenceValidationError,
)


def make_docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def make_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    )
    return bytes(pdf)


def make_blank_pdf() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output)
    return output.getvalue()


def test_txt_pdf_and_docx_extract_text() -> None:
    service = UserEvidenceService()

    items, context = service.process_files(
        [
            ("notes.txt", "text/plain", b"TXT evidence text"),
            ("notice.pdf", "application/pdf", make_pdf("PDF evidence text")),
            (
                "details.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                make_docx("DOCX evidence text"),
            ),
        ]
    )

    assert [item.extraction_status for item in items] == ["extracted"] * 3
    assert items[0].extracted_text == "TXT evidence text"
    assert "PDF evidence text" in (items[1].extracted_text or "")
    assert items[1].pages[0].page_number == 1
    assert items[2].extracted_text == "DOCX evidence text"
    assert "User-provided document: notes.txt" in (context or "")


def test_image_is_accepted_without_claiming_analysis() -> None:
    items, context = UserEvidenceService().process_files(
        [("photo.png", "image/png", b"not image analysis")]
    )

    assert items[0].extraction_status == "image_pending"
    assert items[0].extracted_text is None
    assert items[0].metadata["image_analysis"] == "not_available"
    assert context is None


def test_image_only_pdf_is_explicitly_not_ocr_processed() -> None:
    items, context = UserEvidenceService().process_files(
        [("scan.pdf", "application/pdf", make_blank_pdf())]
    )

    assert items[0].extraction_status == "image_only"
    assert items[0].extracted_text is None
    assert items[0].metadata["ocr"] == "not_available"
    assert items[0].pages[0].page_number == 1
    assert context is None


def test_unsupported_file_is_reported_cleanly() -> None:
    items, context = UserEvidenceService().process_files(
        [("archive.zip", "application/zip", b"zip content")]
    )

    assert items[0].extraction_status == "unsupported"
    assert items[0].extracted_text is None
    assert context is None


def test_empty_file_is_rejected() -> None:
    with pytest.raises(UserEvidenceValidationError):
        UserEvidenceService().process_files([("empty.txt", "text/plain", b"")])


def test_malformed_pdf_and_docx_are_explicit_failures() -> None:
    items, _ = UserEvidenceService().process_files(
        [
            ("broken.pdf", "application/pdf", b"not a pdf"),
            ("broken.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"not a docx"),
        ]
    )

    assert [item.extraction_status for item in items] == ["failed", "failed"]


def test_file_count_and_size_limits() -> None:
    service = UserEvidenceService()
    with pytest.raises(UserEvidenceValidationError):
        service.process_files([("file.txt", "text/plain", b"x")] * (MAX_FILES + 1))
    with pytest.raises(UserEvidenceValidationError):
        service.process_files([("large.txt", "text/plain", b"x" * (MAX_FILE_SIZE_BYTES + 1))])


def test_user_text_does_not_enter_the_knowledge_repository() -> None:
    service = UserEvidenceService()
    service.process_files([("private.txt", "text/plain", b"private unique upload phrase")])

    assert KnowledgeBaseService().search("private unique upload phrase") == []

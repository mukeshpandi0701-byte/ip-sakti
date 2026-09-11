import sys
from pathlib import Path

from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.main import app  # noqa: E402
from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402
from app.services.llm_service import FallbackLLMService  # noqa: E402
from app.services import query_service as query_service_module  # noqa: E402
from app.services.query_service import QueryService  # noqa: E402


query_service_module.query_service = QueryService(KnowledgeBaseService(), FallbackLLMService())


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_returns_demo_answer_and_evidence() -> None:
    response = client.post("/api/query", json={"question": "What is a trademark?"})

    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert "What is a trademark?" in body["answer"]
    assert body["evidence"][0]["is_demo"] is True
    assert body["classification"]["category"] == "TRADEMARK"
    assert body["grounded"] is True


def test_unsupported_query_returns_unknown_classification() -> None:
    response = client.post("/api/query", json={"question": "quantum spaceship"})

    assert response.status_code == 200
    body = response.json()
    assert body["classification"]["category"] == "UNKNOWN"
    assert body["classification"]["intent"] == "UNKNOWN"
    assert body["grounded"] is False
    assert body["evidence_status"] == "insufficient"
    assert body["confidence"] == 0


def test_multipart_query_returns_user_evidence_and_preserves_pipeline() -> None:
    response = client.post(
        "/api/query",
        data={"question": "What is a trademark?"},
        files=[("files", ("notes.txt", b"User-provided supporting text", "text/plain"))],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["classification"]["category"] == "TRADEMARK"
    assert body["user_evidence"][0]["filename"] == "notes.txt"
    assert body["user_evidence"][0]["extraction_status"] == "extracted"


def test_evidence_intake_endpoint_returns_structured_statuses() -> None:
    response = client.post(
        "/api/evidence/intake",
        files=[
            ("files", ("notes.txt", b"User text", "text/plain")),
            ("files", ("photo.png", b"PNG bytes", "image/png")),
        ],
    )

    assert response.status_code == 200
    statuses = {item["filename"]: item["extraction_status"] for item in response.json()["user_evidence"]}
    assert statuses == {"notes.txt": "extracted", "photo.png": "image_pending"}


def test_empty_upload_returns_clean_validation_error() -> None:
    response = client.post(
        "/api/evidence/intake",
        files=[("files", ("empty.txt", b"", "text/plain"))],
    )

    assert response.status_code == 400
    assert "Traceback" not in response.text
    assert "empty" in response.json()["detail"]


def test_knowledge_endpoints_return_documents_and_evidence() -> None:
    documents_response = client.get("/api/knowledge/documents")
    search_response = client.get("/api/knowledge/search", params={"q": "branding"})

    assert documents_response.status_code == 200
    assert documents_response.json()[0]["id"] == "demo-traditional-knowledge-01"
    assert documents_response.json()[0]["source_type"] == "synthetic_demo"
    assert search_response.status_code == 200
    assert search_response.json()[0]["document_id"] == "demo-branding-02"
    assert search_response.json()[0]["source_type"] == "synthetic_demo"

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
    assert body["grounded"] is True


def test_knowledge_endpoints_return_documents_and_evidence() -> None:
    documents_response = client.get("/api/knowledge/documents")
    search_response = client.get("/api/knowledge/search", params={"q": "branding"})

    assert documents_response.status_code == 200
    assert documents_response.json()[0]["source_type"] == "synthetic_demo"
    assert search_response.status_code == 200
    assert search_response.json()[0]["document_id"] == "demo-branding-02"

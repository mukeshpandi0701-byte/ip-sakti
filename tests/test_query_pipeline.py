import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.knowledge_models import Evidence  # noqa: E402
from app.models import QueryRequest  # noqa: E402
from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402
from app.services.llm_service import GeneratedAnswer  # noqa: E402
from app.services.query_service import NO_EVIDENCE_ANSWER, QueryService  # noqa: E402


class FakeLLM:
    def generate_answer(self, query: str, evidence: list[Evidence]) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer=f"Answer for {query} using [{evidence[0].chunk_id}]",
            provider="fake-test",
            grounded=True,
            confidence=0.9,
        )


class FailingLLM:
    def generate_answer(self, query: str, evidence: list[Evidence]) -> GeneratedAnswer:
        raise RuntimeError("simulated provider failure")


def test_query_retrieves_evidence_and_returns_grounded_response() -> None:
    service = QueryService(KnowledgeBaseService(), FakeLLM())

    response = service.answer_query(QueryRequest(question="traditional knowledge"))

    assert response.grounded is True
    assert response.provider == "fake-test"
    assert response.evidence
    assert response.evidence[0].document_id == "demo-traditional-knowledge-01"


def test_query_with_no_evidence_returns_safe_response() -> None:
    service = QueryService(KnowledgeBaseService(), FakeLLM())

    response = service.answer_query(QueryRequest(question="quantum spaceship patent"))

    assert response.answer == NO_EVIDENCE_ANSWER
    assert response.grounded is False
    assert response.evidence == []
    assert response.provider == "none"


def test_llm_failure_falls_back_without_crashing() -> None:
    service = QueryService(KnowledgeBaseService(), FailingLLM())

    response = service.answer_query(QueryRequest(question="branding"))

    assert response.grounded is True
    assert response.provider == "fallback-demo"
    assert response.evidence

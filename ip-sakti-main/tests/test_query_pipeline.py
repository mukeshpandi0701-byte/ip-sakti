import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.knowledge_models import Evidence  # noqa: E402
from app.models import QueryRequest  # noqa: E402
from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402
from app.services.llm_service import GeneratedAnswer, OllamaLLMService  # noqa: E402
from app.services.query_service import NO_EVIDENCE_ANSWER, QueryService  # noqa: E402
from app.config import Settings  # noqa: E402


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


class InsufficientLLM:
    def generate_answer(self, query: str, evidence: list[Evidence]) -> GeneratedAnswer:
        return GeneratedAnswer(
            answer="There is insufficient evidence to answer reliably.",
            provider="fake-insufficient",
            grounded=False,
            confidence=0.8,
        )


def test_query_retrieves_evidence_and_returns_grounded_response() -> None:
    service = QueryService(KnowledgeBaseService(), FakeLLM())

    response = service.answer_query(QueryRequest(question="traditional knowledge"))

    assert response.grounded is True
    assert response.evidence_status == "sufficient"
    assert response.provider == "fake-test"
    assert response.confidence == 0.9
    assert response.evidence
    assert response.evidence[0].document_id == "demo-traditional-knowledge-01"


def test_query_with_no_evidence_returns_safe_response() -> None:
    service = QueryService(KnowledgeBaseService(), FakeLLM())

    response = service.answer_query(QueryRequest(question="quantum spaceship patent"))

    assert response.answer == NO_EVIDENCE_ANSWER
    assert response.grounded is False
    assert response.evidence_status == "insufficient"
    assert response.confidence == 0
    assert response.evidence == []
    assert response.provider == "none"


def test_llm_failure_falls_back_without_crashing() -> None:
    service = QueryService(KnowledgeBaseService(), FailingLLM())

    response = service.answer_query(QueryRequest(question="branding"))

    assert response.grounded is True
    assert response.evidence_status == "sufficient"
    assert response.provider == "fallback-demo"
    assert response.confidence > 0
    assert response.evidence


def test_insufficient_generated_response_cannot_claim_grounded() -> None:
    service = QueryService(KnowledgeBaseService(), InsufficientLLM())

    response = service.answer_query(QueryRequest(question="branding"))

    assert response.grounded is False
    assert response.evidence_status == "insufficient"
    assert response.confidence == 0
    assert response.evidence


def test_ollama_provider_response_is_supported(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return b'{"response":"Grounded answer [chunk-1]"}'

    monkeypatch.setattr("app.services.llm_service.urlopen", lambda *args, **kwargs: FakeResponse())
    service = OllamaLLMService(Settings())
    evidence = KnowledgeBaseService().search("branding")

    generated = service.generate_answer("branding", evidence)

    assert generated.provider == "ollama"
    assert generated.grounded is True
    assert generated.confidence > 0

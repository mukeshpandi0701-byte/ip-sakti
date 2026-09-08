import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.classification_models import ClassificationResult, QueryCategory, QueryIntent  # noqa: E402
from app.models import QueryRequest  # noqa: E402
from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402
from app.services.llm_service import FallbackLLMService  # noqa: E402
from app.services.query_classifier import RuleBasedQueryClassifier  # noqa: E402
from app.services.query_service import QueryService  # noqa: E402
from app.services.retrieval_router import RetrievalRouter  # noqa: E402


@pytest.mark.parametrize(
    ("query", "category", "domain", "source_types"),
    [
        ("How can I patent a formulation?", QueryCategory.PATENT, "ip", ("patent", "ip_guideline")),
        ("How do I register a trademark?", QueryCategory.TRADEMARK, "ip", ("trademark", "ip_guideline")),
        (
            "How can traditional knowledge be protected?",
            QueryCategory.TRADITIONAL_KNOWLEDGE,
            "traditional_knowledge",
            ("traditional_knowledge", "guideline"),
        ),
        (
            "What regulatory requirements apply?",
            QueryCategory.REGULATORY,
            "regulation",
            ("regulation", "guideline"),
        ),
    ],
)
def test_router_returns_expected_hints(
    query: str, category: QueryCategory, domain: str, source_types: tuple[str, ...]
) -> None:
    classification = RuleBasedQueryClassifier().classify(query)
    hints = RetrievalRouter().route(classification)

    assert classification.category is category
    assert hints.retrieval_domain == domain
    assert hints.source_types == source_types


def test_unknown_query_has_unrestricted_general_routing() -> None:
    classification = RuleBasedQueryClassifier().classify("Hello, how are you?")
    hints = RetrievalRouter().route(classification)

    assert classification.category is QueryCategory.UNKNOWN
    assert hints.retrieval_domain == "general"
    assert hints.source_types == ()


def test_synthetic_demo_evidence_remains_available_when_no_hint_type_matches() -> None:
    service = QueryService(KnowledgeBaseService(), FallbackLLMService())

    response = service.answer_query(QueryRequest(question="traditional knowledge"))

    assert response.grounded is True
    assert response.evidence
    assert response.evidence[0].document_id == "demo-traditional-knowledge-01"
    assert response.classification.retrieval_domain == "traditional_knowledge"
    assert response.classification.source_types == ["traditional_knowledge", "guideline"]


def test_unsupported_query_remains_insufficient_with_routing() -> None:
    service = QueryService(KnowledgeBaseService(), FallbackLLMService())

    response = service.answer_query(QueryRequest(question="quantum spaceship patent"))

    assert response.grounded is False
    assert response.evidence_status == "insufficient"
    assert response.confidence == 0
    assert response.evidence == []


def test_preferred_source_types_are_used_only_when_matching_evidence_exists() -> None:
    service = KnowledgeBaseService()

    evidence = service.search("branding", source_types=("trademark",))

    assert evidence
    assert evidence[0].document_id == "demo-branding-02"

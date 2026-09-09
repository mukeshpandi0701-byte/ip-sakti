import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.classification_models import ClassificationCategory, ClassificationIntent  # noqa: E402
from app.services.query_classifier import QueryClassifier  # noqa: E402


classifier = QueryClassifier()


def test_patent_classification() -> None:
    result = classifier.classify("Can I patent my herbal formulation?")

    assert result.category == ClassificationCategory.PATENT
    assert result.intent == ClassificationIntent.IP_PROTECTION
    assert result.confidence >= 0.8


def test_trademark_classification() -> None:
    result = classifier.classify("How do I register my brand name?")

    assert result.category == ClassificationCategory.TRADEMARK
    assert result.intent == ClassificationIntent.IP_PROTECTION


def test_copyright_classification() -> None:
    result = classifier.classify("What are the copyright rules?")

    assert result.category == ClassificationCategory.COPYRIGHT
    assert result.intent == ClassificationIntent.GENERAL_INFORMATION


def test_traditional_knowledge_classification() -> None:
    result = classifier.classify("How can traditional knowledge be protected?")

    assert result.category == ClassificationCategory.TRADITIONAL_KNOWLEDGE
    assert result.intent == ClassificationIntent.TRADITIONAL_KNOWLEDGE


def test_regulatory_classification() -> None:
    result = classifier.classify("What are the rules for selling this Ayurvedic product?")

    assert result.category == ClassificationCategory.REGULATORY
    assert result.intent == ClassificationIntent.REGULATORY_REQUIREMENT


def test_general_ip_classification() -> None:
    result = classifier.classify("What is intellectual property?")

    assert result.category == ClassificationCategory.GENERAL_IP
    assert result.intent == ClassificationIntent.GENERAL_INFORMATION


def test_unknown_empty_and_whitespace_queries() -> None:
    for query in ("quantum spaceship", "", "   "):
        result = classifier.classify(query)
        assert result.category == ClassificationCategory.UNKNOWN
        assert result.intent == ClassificationIntent.UNKNOWN
        assert result.confidence == 0


def test_ambiguous_query_uses_deterministic_specific_category() -> None:
    result = classifier.classify("Can I patent and brand my herbal formulation?")

    assert result.category == ClassificationCategory.PATENT
    assert result.intent == ClassificationIntent.IP_PROTECTION

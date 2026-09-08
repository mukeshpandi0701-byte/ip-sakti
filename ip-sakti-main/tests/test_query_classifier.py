import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.classification_models import QueryCategory, QueryIntent  # noqa: E402
from app.services.query_classifier import RuleBasedQueryClassifier  # noqa: E402


@pytest.mark.parametrize(
    ("query", "category", "intent", "confidence"),
    [
        ("How can I patent my herbal formulation?", QueryCategory.PATENT, QueryIntent.IP_PROTECTION, 0.95),
        ("How do I register a trademark for my brand?", QueryCategory.TRADEMARK, QueryIntent.IP_PROTECTION, 0.95),
        ("Can I copyright my product artwork?", QueryCategory.COPYRIGHT, QueryIntent.IP_PROTECTION, 0.95),
        ("How can traditional knowledge be protected?", QueryCategory.TRADITIONAL_KNOWLEDGE, QueryIntent.TRADITIONAL_KNOWLEDGE, 0.95),
        ("What are the regulatory requirements for selling this product?", QueryCategory.REGULATORY, QueryIntent.REGULATORY_REQUIREMENT, 0.95),
        ("What is intellectual property?", QueryCategory.GENERAL_IP, QueryIntent.GENERAL_INFORMATION, 0.80),
        ("Hello, how are you?", QueryCategory.UNKNOWN, QueryIntent.UNKNOWN, 0),
        ("", QueryCategory.UNKNOWN, QueryIntent.UNKNOWN, 0),
        ("   ", QueryCategory.UNKNOWN, QueryIntent.UNKNOWN, 0),
        ("???", QueryCategory.UNKNOWN, QueryIntent.UNKNOWN, 0),
        ("HOW CAN I PATENT MY PRODUCT?", QueryCategory.PATENT, QueryIntent.IP_PROTECTION, 0.95),
    ],
)
def test_rule_based_classifier_returns_documented_results(
    query: str, category: QueryCategory, intent: QueryIntent, confidence: float
) -> None:
    result = RuleBasedQueryClassifier().classify(query)

    assert result.category is category
    assert result.intent is intent
    assert result.confidence == confidence


def test_category_precedence_is_deterministic() -> None:
    result = RuleBasedQueryClassifier().classify("What patent regulations apply?")

    assert result.category is QueryCategory.REGULATORY
    assert result.intent is QueryIntent.REGULATORY_REQUIREMENT


def test_search_intent_is_detected_for_supported_ip_categories() -> None:
    result = RuleBasedQueryClassifier().classify("How do I search for an existing patent?")

    assert result.category is QueryCategory.PATENT
    assert result.intent is QueryIntent.IP_SEARCH

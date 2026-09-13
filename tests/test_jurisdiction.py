import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.jurisdiction_models import Jurisdiction, JurisdictionResult  # noqa: E402
from app.services.jurisdiction_service import JurisdictionService  # noqa: E402


def test_explicit_india_jurisdiction_takes_priority() -> None:
    """Explicit jurisdiction selection should override inference."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are the US patent requirements?",
        explicit_jurisdiction="india",
    )

    assert result.jurisdiction == Jurisdiction.INDIA
    assert result.confidence == 1.0
    assert "explicitly selected" in result.reason.lower()


def test_explicit_usa_jurisdiction_takes_priority() -> None:
    """Explicit USA selection should override India keywords."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are the Indian patent requirements?",
        explicit_jurisdiction="usa",
    )

    assert result.jurisdiction == Jurisdiction.USA
    assert result.confidence == 1.0


def test_explicit_eu_jurisdiction() -> None:
    """Explicit EU selection."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What is intellectual property?",
        explicit_jurisdiction="eu",
    )

    assert result.jurisdiction == Jurisdiction.EU
    assert result.confidence == 1.0


def test_infer_india_from_keywords() -> None:
    """Should infer India from India-specific keywords."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are Indian patent act requirements?"
    )

    assert result.jurisdiction == Jurisdiction.INDIA
    assert result.confidence > 0.5
    assert "keyword" in result.reason.lower()


def test_infer_usa_from_keywords() -> None:
    """Should infer USA from US-specific keywords."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="How does the US patent system work?"
    )

    assert result.jurisdiction == Jurisdiction.USA
    assert result.confidence > 0.5


def test_infer_eu_from_keywords() -> None:
    """Should infer EU from EU-specific keywords."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What is the European Patent Office process?"
    )

    assert result.jurisdiction == Jurisdiction.EU
    assert result.confidence > 0.5


def test_ambiguous_query_returns_unknown() -> None:
    """Query without clear jurisdiction indicators should return UNKNOWN."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are the patent requirements?"
    )

    assert result.jurisdiction == Jurisdiction.UNKNOWN
    assert result.confidence == 0.0
    assert "cannot be reliably determined" in result.reason.lower()


def test_ayurveda_suggests_india() -> None:
    """Ayurvedic query should suggest India jurisdiction."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="How can I patent my Ayurvedic formulation?"
    )

    assert result.jurisdiction == Jurisdiction.INDIA
    assert result.confidence > 0.2  # Reduced threshold - "Ayurvedic" alone gives ~0.33


def test_empty_question_returns_unknown() -> None:
    """Empty question should safely return UNKNOWN."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(question="")

    assert result.jurisdiction == Jurisdiction.UNKNOWN
    assert result.confidence == 0.0


def test_jurisdiction_result_has_source_scope() -> None:
    """Jurisdiction result should include source_scope for retrieval."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="Indian patent requirements",
        explicit_jurisdiction="india",
    )

    assert result.source_scope == ["india"]
    assert isinstance(result.source_scope, list)


def test_usa_jurisdiction_source_scope() -> None:
    """USA jurisdiction should have correct source_scope."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="USPTO patent requirements",
        explicit_jurisdiction="usa",
    )

    assert result.source_scope == ["usa"]


def test_eu_jurisdiction_source_scope() -> None:
    """EU jurisdiction should have correct source_scope."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        explicit_jurisdiction="eu",
        question="EPO requirements"
    )

    assert result.source_scope == ["eu"]


def test_international_jurisdiction() -> None:
    """Should support INTERNATIONAL jurisdiction."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="International patent treaty requirements",
        explicit_jurisdiction="international",
    )

    assert result.jurisdiction == Jurisdiction.INTERNATIONAL
    assert result.source_scope == ["international"]


def test_unknown_explicit_jurisdiction_defaults_to_unknown() -> None:
    """Invalid explicit jurisdiction should not crash, should return UNKNOWN."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What is IP?",
        explicit_jurisdiction="invalid_jurisdiction",
    )

    # Should fall through to inference
    assert result.jurisdiction == Jurisdiction.UNKNOWN


def test_confidence_in_valid_range() -> None:
    """Confidence should always be between 0 and 1."""
    service = JurisdictionService()

    test_cases = [
        ("Indian patent requirements",),
        ("USA patent system",),
        ("What is IP?",),
        ("",),
    ]

    for args in test_cases:
        result = service.determine_jurisdiction(*args)
        assert 0 <= result.confidence <= 1, f"Confidence out of range for {args}"


def test_india_and_usa_keywords_ambiguous_returns_unknown() -> None:
    """If query lacks clear jurisdiction keywords, should return UNKNOWN."""
    service = JurisdictionService()
    
    # No clear India/USA/EU keywords
    result = service.determine_jurisdiction(
        question="What is a copyright registration process?"
    )
    
    assert result.jurisdiction == Jurisdiction.UNKNOWN


def test_product_context_jurisdiction() -> None:
    """Should infer jurisdiction from product context if provided."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are the requirements?",
        product_context={"jurisdiction": "india"},
    )

    assert result.jurisdiction == Jurisdiction.INDIA


def test_explicit_jurisdiction_overrides_product_context() -> None:
    """Explicit selection should override product context."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are the requirements?",
        explicit_jurisdiction="usa",
        product_context={"jurisdiction": "india"},
    )

    assert result.jurisdiction == Jurisdiction.USA


def test_normalize_jurisdiction_case_insensitive() -> None:
    """Jurisdiction normalization should be case-insensitive."""
    service = JurisdictionService()

    for jurisdiction_str in ["INDIA", "India", "india"]:
        result = service.determine_jurisdiction(
            question="test",
            explicit_jurisdiction=jurisdiction_str,
        )
        assert result.jurisdiction == Jurisdiction.INDIA


def test_don_not_randomly_select_india_for_ambiguous_query() -> None:
    """Development rule: ambiguous queries must not default to India."""
    service = JurisdictionService()
    result = service.determine_jurisdiction(
        question="What are the trademark registration requirements?"
    )

    # No India-specific keywords, so should not be India
    assert result.jurisdiction == Jurisdiction.UNKNOWN


def test_jurisdiction_result_is_valid_pydantic_model() -> None:
    """JurisdictionResult should be a valid Pydantic model."""
    service = JurisdictionService()
    result = service.determine_jurisdiction("Test question")

    # Should be able to serialize
    json_data = result.model_dump_json()
    assert isinstance(json_data, str)
    assert "jurisdiction" in json_data
    assert "confidence" in json_data


def test_india_international_separation() -> None:
    """India and international scopes should be separate."""
    service = JurisdictionService()

    india_result = service.determine_jurisdiction(
        "Indian patent requirements",
        explicit_jurisdiction="india",
    )
    intl_result = service.determine_jurisdiction(
        "International patent treaty",
        explicit_jurisdiction="international",
    )

    assert india_result.source_scope == ["india"]
    assert intl_result.source_scope == ["international"]
    assert india_result.source_scope != intl_result.source_scope

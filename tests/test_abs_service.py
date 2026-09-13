import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.abs_models import ABSRelevance  # noqa: E402
from app.services.abs_service import ABSConsiderationService  # noqa: E402
from app.tk_models import TKDetection, TKResult  # noqa: E402


def test_biological_resource_query_detects_abs() -> None:
    """Query about biological resources with more context should detect ABS relevance."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="What are the regulations for using and commercializing biological materials from plants?"
    )

    assert result.relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT)
    assert result.confidence > 0.3


def test_plant_herbal_context_detects_abs() -> None:
    """Plant/herbal context should detect ABS relevance."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="How do I commercialize my herbal product?"
    )

    assert result.relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT)


def test_medicinal_plant_commercialization() -> None:
    """Medicinal plant commercialization should flag ABS relevance."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="What are the rules for selling medicinal plant extracts?"
    )

    assert result.relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT)


def test_traditional_knowledge_plus_biological_resource() -> None:
    """TK + biological resource should be strong ABS signal."""
    service = ABSConsiderationService()
    tk_result = TKResult(
        detected=TKDetection.DETECTED,
        confidence=0.9,
        reasons=["Traditional Ayurvedic formulation"],
        considerations=[],
        source_status="demo_unavailable",
    )

    result = service.assess_abs_relevance(
        question="How do I commercialize my traditional herbal formulation?",
        tk_result=tk_result,
    )

    assert result.relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT)
    assert result.confidence >= 0.5


def test_non_biological_query_no_abs() -> None:
    """Non-biological query should not detect ABS relevance."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="What is a trademark?"
    )

    assert result.relevance == ABSRelevance.NOT_DETECTED
    assert result.confidence == 0.0


def test_confidence_in_valid_range() -> None:
    """ABS confidence should always be between 0 and 1."""
    service = ABSConsiderationService()

    test_cases = [
        "biological resource",
        "herbal product",
        "trademark",
        "",
    ]

    for question in test_cases:
        result = service.assess_abs_relevance(question)
        assert 0 <= result.confidence <= 1


def test_abs_result_includes_reasons() -> None:
    """ABS result should include reasons for relevance assessment."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="How do I export medicinal plant products?"
    )

    assert isinstance(result.reasons, list)
    if result.relevance != ABSRelevance.NOT_DETECTED:
        assert len(result.reasons) > 0


def test_abs_considerations_provided() -> None:
    """ABS result should include considerations."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="What are the requirements for selling plant extracts commercially?"
    )

    assert isinstance(result.considerations, list)
    if result.relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT):
        assert len(result.considerations) > 0


def test_abs_not_legal_requirement() -> None:
    """ABS considerations should NOT fabricate specific legal requirements."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="Can I sell my herbal product?"
    )

    # Should flag considerations, not make up legal requirements
    for consideration in result.considerations:
        assert "must obtain approval" not in consideration.lower()
        assert "must pay" not in consideration.lower()
        assert "requires permission" not in consideration.lower()
        # Should be cautious language ("may", "consider", "review")
        if len(result.considerations) > 0:
            assert any(word in consideration.lower() for word in [
                "may", "consider", "review", "flag", "potential", "relevant"
            ])


def test_abs_result_is_valid_pydantic_model() -> None:
    """ABSResult should be a valid Pydantic model."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance("Test question")

    # Should be able to serialize
    json_data = result.model_dump_json()
    assert isinstance(json_data, str)
    assert "relevance" in json_data
    assert "confidence" in json_data


def test_plant_commercial_higher_confidence() -> None:
    """Plant + commercialization should have higher ABS confidence."""
    service = ABSConsiderationService()

    plant_only = service.assess_abs_relevance("plant extraction methods")
    plant_commercial = service.assess_abs_relevance("commercialize herbal plant extracts")

    assert plant_commercial.confidence >= plant_only.confidence


def test_product_context_abs_detection() -> None:
    """ABS should be detected from product context."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="What are the requirements?",
        product_context={
            "type": "herbal product",
            "commercialization": True,
        },
    )

    assert result.relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT)


def test_empty_question_no_abs() -> None:
    """Empty question should not falsely detect ABS relevance."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(question="")

    assert result.relevance == ABSRelevance.NOT_DETECTED


def test_medicinal_plant_commercialization_consideration() -> None:
    """Result should mention Prior Informed Consent for plant commercialization."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="How do I sell medicinal plant products internationally?"
    )

    if result.relevance == ABSRelevance.RELEVANT:
        considerations_text = " ".join(result.considerations).lower()
        # Should mention IC/consent/ABS framework
        assert any(word in considerations_text for word in [
            "informed consent", "abs", "benefit", "nagoya", "prior consent"
        ])


def test_tk_biological_benefit_sharing_consideration() -> None:
    """TK + biological should mention benefit-sharing."""
    service = ABSConsiderationService()
    tk_result = TKResult(
        detected=TKDetection.DETECTED,
        confidence=0.9,
        reasons=["Traditional knowledge"],
        considerations=[],
        source_status="demo_unavailable",
    )

    result = service.assess_abs_relevance(
        question="commercialize my traditional herbal plant formula",
        tk_result=tk_result,
    )

    if result.relevance == ABSRelevance.RELEVANT:
        considerations_text = " ".join(result.considerations).lower()
        assert "benefit" in considerations_text


def test_abs_flag_not_clearance() -> None:
    """ABS result should be a flag, not a legal clearance."""
    service = ABSConsiderationService()
    result = service.assess_abs_relevance(
        question="Is my herbal plant product compliant with ABS requirements for commercialization?"
    )

    # Should flag, not claim compliance
    for consideration in result.considerations:
        assert "definitely compliant" not in consideration.lower()
        assert "is compliant" not in consideration.lower()
        # Should use cautious language
        assert any(word in consideration.lower() for word in [
            "flag", "may be", "consider", "review", "potential", "relevant", "flag"
        ])


def test_multiple_biological_indicators_higher_confidence() -> None:
    """Multiple biological indicators should increase confidence."""
    service = ABSConsiderationService()

    weak_result = service.assess_abs_relevance("plant")

    strong_result = service.assess_abs_relevance(
        "commercial medicinal plant extract biodiversity resource"
    )

    assert strong_result.confidence >= weak_result.confidence

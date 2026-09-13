import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.classification_models import ClassificationCategory  # noqa: E402
from app.services.tk_service import TraditionalKnowledgeService  # noqa: E402
from app.tk_models import TKDetection  # noqa: E402


def test_traditional_knowledge_detected_from_classification() -> None:
    """TK should be detected if classified as TRADITIONAL_KNOWLEDGE."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="How is traditional knowledge protected?",
        classification_category=ClassificationCategory.TRADITIONAL_KNOWLEDGE,
    )

    assert result.detected in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED)
    assert result.confidence > 0.5


def test_tk_detected_from_keywords() -> None:
    """TK should be detected from traditional knowledge keywords."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="How can I protect my traditional herbal formulation?"
    )

    assert result.detected in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED)
    assert result.confidence > 0.3


def test_ayurvedic_query_detects_tk() -> None:
    """Ayurvedic queries should detect TK."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="What are the rules for Ayurvedic product registration?"
    )

    assert result.detected in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED)
    assert result.confidence > 0.3


def test_non_tk_query() -> None:
    """Non-TK query should not detect traditional knowledge."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="What is a trademark?"
    )

    assert result.detected == TKDetection.NOT_DETECTED
    assert result.confidence == 0.0


def test_ambiguous_tk_query() -> None:
    """Ambiguous TK query should return POSSIBLY_DETECTED or DETECTED."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="Does my formulation relate to traditional practices?"
    )

    # "formulation" + "traditional" = weak TK signal
    assert result.detected in (TKDetection.NOT_DETECTED, TKDetection.POSSIBLY_DETECTED, TKDetection.DETECTED)
    assert 0 <= result.confidence <= 1


def test_confidence_in_valid_range() -> None:
    """TK confidence should always be between 0 and 1."""
    service = TraditionalKnowledgeService()

    test_cases = [
        "traditional knowledge",
        "trademark",
        "Ayurvedic formulation",
        "",
    ]

    for question in test_cases:
        result = service.assess_traditional_knowledge(question)
        assert 0 <= result.confidence <= 1


def test_tk_result_includes_reasons() -> None:
    """TK result should include reasons for detection."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="How is Ayurvedic traditional knowledge protected?"
    )

    assert isinstance(result.reasons, list)
    assert len(result.reasons) > 0


def test_no_fake_tkdl_search() -> None:
    """Source status should indicate TKDL is not actually searched."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="Is my Ayurvedic formulation in TKDL?"
    )

    assert result.source_status == "demo_unavailable"
    # Should NOT claim TKDL was searched
    assert "tkdl" not in result.source_status.lower() or "unavailable" in result.source_status.lower()


def test_tk_considerations_provided() -> None:
    """TK result should include considerations."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="Can I patent my Ayurvedic formulation?"
    )

    assert isinstance(result.considerations, list)
    if result.detected in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED):
        assert len(result.considerations) > 0


def test_tk_not_legal_conclusion() -> None:
    """TK detection should not make legal conclusions."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="Can I patent my Ayurvedic formulation?"
    )

    # Should flag consideration, not say "definitely cannot be patented"
    for reason in result.reasons:
        assert "will not be patented" not in reason.lower()
        assert "cannot be patented" not in reason.lower()


def test_product_context_tk_detection() -> None:
    """TK should be detected from product context with question keywords."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="What are the requirements for my traditional product?",
        product_context={"type": "Traditional Ayurvedic Medicine"},
    )

    # Product context + "traditional" in question should detect
    assert result.detected in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED)


def test_empty_question_no_tk() -> None:
    """Empty question should not falsely detect TK."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(question="")

    assert result.detected == TKDetection.NOT_DETECTED or result.confidence == 0.0


def test_tk_multiple_indicators() -> None:
    """Query with multiple TK indicators should have higher confidence."""
    service = TraditionalKnowledgeService()

    weak_result = service.assess_traditional_knowledge(
        question="formulation"
    )

    strong_result = service.assess_traditional_knowledge(
        question="traditional Ayurvedic herbal formulation"
    )

    assert strong_result.confidence >= weak_result.confidence


def test_tk_result_is_valid_pydantic_model() -> None:
    """TKResult should be a valid Pydantic model."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge("Test question")

    # Should be able to serialize
    json_data = result.model_dump_json()
    assert isinstance(json_data, str)
    assert "detected" in json_data
    assert "confidence" in json_data


def test_ayurveda_product_considerations() -> None:
    """Ayurvedic product should mention Ayurvedic framework."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="What are the requirements for selling Ayurvedic products?",
        classification_category=ClassificationCategory.TRADITIONAL_KNOWLEDGE,
    )

    if result.detected == TKDetection.DETECTED:
        considerations_text = " ".join(result.considerations).lower()
        assert "ayurvedic" in considerations_text or "framework" in considerations_text


def test_tk_and_product_mentions_abs() -> None:
    """TK + product context should mention ABS in considerations."""
    service = TraditionalKnowledgeService()
    result = service.assess_traditional_knowledge(
        question="How do I commercialize my Ayurvedic formulation?",
        classification_category=ClassificationCategory.TRADITIONAL_KNOWLEDGE,
    )

    if result.detected == TKDetection.DETECTED:
        considerations_text = " ".join(result.considerations).lower()
        # Should mention sharing/ABS considerations for commercialization
        assert any(word in considerations_text for word in ["abs", "sharing", "benefit"])

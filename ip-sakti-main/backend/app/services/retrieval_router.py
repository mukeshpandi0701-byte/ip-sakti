"""Deterministic routing hints derived from Phase 4A classifications."""

from dataclasses import dataclass

from app.classification_models import ClassificationResult, QueryCategory


@dataclass(frozen=True)
class RetrievalHints:
    """Optional retrieval preferences; an empty source-type list is unrestricted."""

    retrieval_domain: str
    source_types: tuple[str, ...] = ()


class RetrievalRouter:
    """Maps one classification result to stable, conservative retrieval hints."""

    _HINTS_BY_CATEGORY: dict[QueryCategory, RetrievalHints] = {
        QueryCategory.PATENT: RetrievalHints("ip", ("patent", "ip_guideline")),
        QueryCategory.TRADEMARK: RetrievalHints("ip", ("trademark", "ip_guideline")),
        QueryCategory.COPYRIGHT: RetrievalHints("ip", ("copyright", "ip_guideline")),
        QueryCategory.TRADITIONAL_KNOWLEDGE: RetrievalHints(
            "traditional_knowledge", ("traditional_knowledge", "guideline")
        ),
        QueryCategory.REGULATORY: RetrievalHints("regulation", ("regulation", "guideline")),
        QueryCategory.GENERAL_IP: RetrievalHints("ip", ("ip_guideline",)),
        QueryCategory.UNKNOWN: RetrievalHints("general"),
    }

    def route(self, classification: ClassificationResult) -> RetrievalHints:
        return self._HINTS_BY_CATEGORY[classification.category]

    @staticmethod
    def add_hints(
        classification: ClassificationResult, hints: RetrievalHints
    ) -> ClassificationResult:
        """Return response-ready classification metadata without mutating the classifier output."""
        return classification.model_copy(
            update={
                "retrieval_domain": hints.retrieval_domain,
                "source_types": list(hints.source_types),
            }
        )

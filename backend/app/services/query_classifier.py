import re
from dataclasses import dataclass

from app.classification_models import (
    ClassificationCategory,
    ClassificationIntent,
    ClassificationResult,
)


@dataclass(frozen=True)
class _CategoryRule:
    category: ClassificationCategory
    phrases: tuple[str, ...]
    terms: tuple[str, ...]
    priority: int


RULES = (
    _CategoryRule(
        ClassificationCategory.TRADITIONAL_KNOWLEDGE,
        ("traditional knowledge", "community knowledge"),
        ("traditional", "community", "tkdl"),
        0,
    ),
    _CategoryRule(
        ClassificationCategory.PATENT,
        ("prior art", "herbal formulation"),
        ("patent", "invention", "inventive", "formulation"),
        1,
    ),
    _CategoryRule(
        ClassificationCategory.TRADEMARK,
        ("brand name",),
        ("trademark", "brand", "branding", "logo"),
        2,
    ),
    _CategoryRule(
        ClassificationCategory.COPYRIGHT,
        (),
        ("copyright", "creative work", "author", "original work"),
        3,
    ),
    _CategoryRule(
        ClassificationCategory.REGULATORY,
        (),
        ("regulatory", "regulation", "requirement", "requirements", "rules", "selling", "compliance", "license", "licence", "approval"),
        4,
    ),
    _CategoryRule(
        ClassificationCategory.GENERAL_IP,
        ("intellectual property",),
        ("ip",),
        5,
    ),
)


class QueryClassifier:
    """Small deterministic classifier used as an informational query signal."""

    def classify(self, query: str, language: str | None = None) -> ClassificationResult:
        del language  # Reserved for a future multilingual classifier.
        if not isinstance(query, str) or not query.strip():
            return self._unknown()

        normalized = query.casefold()
        terms = set(re.findall(r"[\w'-]+", normalized))
        scores: list[tuple[int, int, ClassificationCategory]] = []
        for rule in RULES:
            phrase_score = sum(3 for phrase in rule.phrases if phrase in normalized)
            term_score = sum(1 for term in rule.terms if term in terms)
            score = phrase_score + term_score
            if score:
                scores.append((score, rule.priority, rule.category))

        if not scores:
            return self._unknown()

        best_score, _, category = max(scores, key=lambda item: (item[0], -item[1]))
        if best_score < 1:
            return self._unknown()

        return ClassificationResult(
            intent=self._intent_for(category, terms),
            category=category,
            confidence=self._confidence(best_score),
        )

    @staticmethod
    def _intent_for(category: ClassificationCategory, terms: set[str]) -> ClassificationIntent:
        if category == ClassificationCategory.REGULATORY:
            return ClassificationIntent.REGULATORY_REQUIREMENT
        if category == ClassificationCategory.TRADITIONAL_KNOWLEDGE:
            return ClassificationIntent.TRADITIONAL_KNOWLEDGE
        if category == ClassificationCategory.GENERAL_IP:
            return ClassificationIntent.GENERAL_INFORMATION
        if {"search", "find", "lookup", "prior"} & terms:
            return ClassificationIntent.IP_SEARCH
        if {"protect", "register", "patent", "trademark"} & terms:
            return ClassificationIntent.IP_PROTECTION
        return ClassificationIntent.GENERAL_INFORMATION

    @staticmethod
    def _confidence(score: int) -> float:
        if score >= 3:
            return 0.9
        if score == 2:
            return 0.8
        return 0.65

    @staticmethod
    def _unknown() -> ClassificationResult:
        return ClassificationResult(
            intent=ClassificationIntent.UNKNOWN,
            category=ClassificationCategory.UNKNOWN,
            confidence=0,
        )

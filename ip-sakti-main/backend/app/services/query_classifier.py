"""Deterministic, knowledge-base-independent query classifiers."""

import re
from typing import Protocol

from app.classification_models import ClassificationResult, QueryCategory, QueryIntent


class QueryClassifier(Protocol):
    """Interface for classifiers; an LLM-backed implementation can be added later."""

    def classify(self, query: str, language: str | None = None) -> ClassificationResult:
        """Classify a user query without retrieval or answer generation."""


class RuleBasedQueryClassifier:
    """Fast keyword classifier with deterministic category precedence.

    Category precedence is traditional knowledge, regulatory, copyright, trademark,
    patent, then general IP. This makes combined questions predictable and gives
    specialized regulatory and traditional-knowledge wording priority. Intent is
    selected independently after the category: regulatory and traditional knowledge
    have fixed specialized intents; otherwise protection wording outranks search
    wording, which outranks general-information wording.
    """

    _CATEGORY_RULES: tuple[tuple[QueryCategory, tuple[str, ...]], ...] = (
        (QueryCategory.TRADITIONAL_KNOWLEDGE, ("traditional knowledge", "traditional medicinal knowledge", "indigenous knowledge")),
        (QueryCategory.REGULATORY, ("regulatory", "regulation", "compliance", "approval", "requirements", "requirement", "licence", "license", "authority")),
        (QueryCategory.COPYRIGHT, ("copyright", "copyrighted")),
        (QueryCategory.TRADEMARK, ("trademark", "trade mark", "brand name")),
        (QueryCategory.PATENT, ("patent", "patentable", "patenting")),
        (QueryCategory.GENERAL_IP, ("intellectual property", " ip ", "ip rights", "ip law")),
    )
    _PROTECTION_TERMS = ("protect", "protection", "register", "registration", "obtain", "enforce", "enforcement", "file", "filing")
    _SEARCH_TERMS = ("search", "find", "check", "discover", "lookup", "look up", "existing", "prior art")
    _GENERAL_TERMS = ("what is", "what are", "tell me about", "explain", "information", "about")

    def classify(self, query: str, language: str | None = None) -> ClassificationResult:
        """Return a stable heuristic result; ``language`` is reserved for future use."""
        normalized = self._normalize(query)
        if not normalized:
            return self._unknown()

        category = self._category_for(normalized)
        if category is QueryCategory.UNKNOWN:
            return self._unknown()

        intent = self._intent_for(normalized, category)
        confidence = 0.95 if intent is not QueryIntent.GENERAL_INFORMATION else 0.80
        return ClassificationResult(intent=intent, category=category, confidence=confidence)

    @staticmethod
    def _normalize(query: str) -> str:
        if not isinstance(query, str):
            return ""
        words = re.findall(r"[\w'-]+", query.casefold())
        return f" {' '.join(words)} "

    def _category_for(self, normalized: str) -> QueryCategory:
        for category, terms in self._CATEGORY_RULES:
            if any(term in normalized for term in terms):
                return category
        return QueryCategory.UNKNOWN

    def _intent_for(self, normalized: str, category: QueryCategory) -> QueryIntent:
        if category is QueryCategory.TRADITIONAL_KNOWLEDGE:
            return QueryIntent.TRADITIONAL_KNOWLEDGE
        if category is QueryCategory.REGULATORY:
            return QueryIntent.REGULATORY_REQUIREMENT
        if any(term in normalized for term in self._PROTECTION_TERMS):
            return QueryIntent.IP_PROTECTION
        if any(term in normalized for term in self._SEARCH_TERMS):
            return QueryIntent.IP_SEARCH
        return QueryIntent.GENERAL_INFORMATION

    @staticmethod
    def _unknown() -> ClassificationResult:
        return ClassificationResult(
            intent=QueryIntent.UNKNOWN,
            category=QueryCategory.UNKNOWN,
            confidence=0,
        )

"""Jurisdiction routing service for IP-SAKTI.

Determines the jurisdiction context (INDIA, USA, EU, INTERNATIONAL, UNKNOWN)
for a query based on available structured information. Never guesses - returns
UNKNOWN if jurisdiction cannot be reliably determined.

Explicit user-selected jurisdiction takes priority over inference.
India and international frameworks are kept separate.
"""

from app.jurisdiction_models import Jurisdiction, JurisdictionResult


class JurisdictionService:
    """Deterministic jurisdiction routing service."""

    # Source scope mappings - which document sources/filters correspond to each jurisdiction
    JURISDICTION_SCOPES = {
        Jurisdiction.INDIA: ["india"],
        Jurisdiction.USA: ["usa"],
        Jurisdiction.EU: ["eu"],
        Jurisdiction.INTERNATIONAL: ["international"],
        Jurisdiction.UNKNOWN: [],
    }

    # Keywords that strongly suggest India jurisdiction
    INDIA_KEYWORDS = {
        "india", "indian", "patent act", "copyrights act", "dpiit",
        "intellectual property appellate board", "ipab", "controller",
        "ayurveda", "ayurvedic", "ayurvedic medicine", "ayurvedic product",
        "traditional knowledge digital library", "tkdl",
    }

    # Keywords that strongly suggest USA jurisdiction
    USA_KEYWORDS = {
        "usa", "united states", "us", "america", "american",
        "us patent", "uspto", "us copyright", "us trademark",
        "us law", "us regulation", "federal",
    }

    # Keywords that strongly suggest EU jurisdiction
    EU_KEYWORDS = {
        "eu", "european", "europe", "euro",
        "epo", "european patent office", "eu regulation",
        "gdpr", "eu directive",
    }

    def determine_jurisdiction(
        self,
        question: str,
        explicit_jurisdiction: str | None = None,
        product_context: dict | None = None,
    ) -> JurisdictionResult:
        """Determine jurisdiction for a query.

        Args:
            question: The user's query/question
            explicit_jurisdiction: User-selected jurisdiction override (e.g., from UI dropdown)
            product_context: Optional product/commercialization context

        Returns:
            JurisdictionResult with determined jurisdiction, confidence, reason, and source_scope
        """
        # Priority 1: Explicit user selection always wins
        if explicit_jurisdiction:
            normalized = self._normalize_jurisdiction(explicit_jurisdiction)
            if normalized and normalized != Jurisdiction.UNKNOWN:
                return JurisdictionResult(
                    jurisdiction=normalized,
                    confidence=1.0,
                    reason=f"Jurisdiction explicitly selected by user: {explicit_jurisdiction}",
                    source_scope=self.JURISDICTION_SCOPES[normalized],
                )

        # Priority 2: Infer from question content
        inferred = self._infer_from_question(question)
        if inferred.jurisdiction != Jurisdiction.UNKNOWN:
            return inferred

        # Priority 3: Infer from product context (if provided)
        if product_context:
            inferred = self._infer_from_product_context(product_context)
            if inferred.jurisdiction != Jurisdiction.UNKNOWN:
                return inferred

        # Default: Cannot determine jurisdiction reliably
        return JurisdictionResult(
            jurisdiction=Jurisdiction.UNKNOWN,
            confidence=0.0,
            reason="Jurisdiction cannot be reliably determined from available information",
            source_scope=self.JURISDICTION_SCOPES[Jurisdiction.UNKNOWN],
        )

    def _normalize_jurisdiction(self, jurisdiction_str: str) -> Jurisdiction | None:
        """Normalize a jurisdiction string to Jurisdiction enum."""
        if not jurisdiction_str:
            return None

        normalized = jurisdiction_str.strip().lower()
        try:
            return Jurisdiction(normalized)
        except ValueError:
            # Try matching by name
            for j in Jurisdiction:
                if j.name.lower() == normalized:
                    return j
            return None

    def _infer_from_question(self, question: str) -> JurisdictionResult:
        """Infer jurisdiction from question text using keyword matching."""
        if not question or not isinstance(question, str):
            return JurisdictionResult(
                jurisdiction=Jurisdiction.UNKNOWN,
                confidence=0.0,
                reason="Question is empty or invalid",
                source_scope=[],
            )

        question_lower = question.lower()
        terms = set(question_lower.split())

        # Count keyword matches for each jurisdiction
        india_matches = sum(1 for kw in self.INDIA_KEYWORDS if kw in question_lower)
        usa_matches = sum(1 for kw in self.USA_KEYWORDS if kw in question_lower)
        eu_matches = sum(1 for kw in self.EU_KEYWORDS if kw in question_lower)

        # Determine highest scoring jurisdiction
        scores = [
            (india_matches, Jurisdiction.INDIA),
            (usa_matches, Jurisdiction.USA),
            (eu_matches, Jurisdiction.EU),
        ]
        max_score = max(score[0] for score in scores)

        # If no matches, cannot infer
        if max_score == 0:
            return JurisdictionResult(
                jurisdiction=Jurisdiction.UNKNOWN,
                confidence=0.0,
                reason="No jurisdiction-specific keywords detected in question",
                source_scope=[],
            )

        # Get all jurisdictions with top score (ambiguity check)
        top_jurisdictions = [j for score, j in scores if score == max_score]

        # If multiple jurisdictions tie, it's ambiguous - return UNKNOWN
        if len(top_jurisdictions) > 1:
            return JurisdictionResult(
                jurisdiction=Jurisdiction.UNKNOWN,
                confidence=0.0,
                reason=f"Question is ambiguous between {len(top_jurisdictions)} jurisdictions; cannot determine uniquely",
                source_scope=[],
            )

        # Single clear winner
        winner = top_jurisdictions[0]
        confidence = min(1.0, max_score / 3.0)  # Rough confidence based on keyword density
        return JurisdictionResult(
            jurisdiction=winner,
            confidence=confidence,
            reason=f"Inferred from {max_score} jurisdiction-specific keyword(s) in question",
            source_scope=self.JURISDICTION_SCOPES[winner],
        )

    def _infer_from_product_context(self, context: dict) -> JurisdictionResult:
        """Infer jurisdiction from product/commercialization context."""
        if not isinstance(context, dict):
            return JurisdictionResult(
                jurisdiction=Jurisdiction.UNKNOWN,
                confidence=0.0,
                reason="Product context is invalid",
                source_scope=[],
            )

        # Look for explicit jurisdiction in context
        for key in ["jurisdiction", "country", "market", "region"]:
            if key in context:
                value = context[key]
                normalized = self._normalize_jurisdiction(str(value))
                if normalized and normalized != Jurisdiction.UNKNOWN:
                    return JurisdictionResult(
                        jurisdiction=normalized,
                        confidence=0.8,
                        reason=f"Inferred from product context field '{key}'",
                        source_scope=self.JURISDICTION_SCOPES[normalized],
                    )

        return JurisdictionResult(
            jurisdiction=Jurisdiction.UNKNOWN,
            confidence=0.0,
            reason="Product context does not contain jurisdiction information",
            source_scope=[],
        )


# Singleton instance
jurisdiction_service = JurisdictionService()

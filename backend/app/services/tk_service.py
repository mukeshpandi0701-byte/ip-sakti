"""Traditional Knowledge detection service for IP-SAKTI.

Identifies when a query/product may involve traditional knowledge considerations.
Never claims to have searched a real TKDL (Traditional Knowledge Digital Library)
unless actually integrated. Explicitly marks sources as unavailable when appropriate.

The purpose is to FLAG potential TK considerations, not to provide legal conclusions.
"""

from app.classification_models import ClassificationCategory, ClassificationIntent
from app.tk_models import TKDetection, TKResult


class TraditionalKnowledgeService:
    """Traditional Knowledge detection and consideration service."""

    # Keywords indicating traditional knowledge/formulations
    TK_KEYWORDS = {
        "traditional", "traditional knowledge", "tk", "traditional medicine",
        "ancient", "vedic", "ayurveda", "ayurvedic", "formulation",
        "herbal formula", "traditional recipe", "time-tested", "classical",
        "traditional use", "folk medicine", "indigenous knowledge",
    }

    # Keywords indicating specific traditional products/knowledge
    AYURVEDIC_KEYWORDS = {
        "ayurveda", "ayurvedic", "dosha", "vata", "pitta", "kapha",
        "chakra", "prana", "ashwagandha", "turmeric", "neem", "brahmi",
        "triphala", "brahmi oil", "balm", "concoction",
    }

    # Product-related keywords that might involve TK
    PRODUCT_KEYWORDS = {
        "product", "formulation", "remedy", "medicine", "cure",
        "supplement", "cosmetic", "food", "ingredient",
    }

    def assess_traditional_knowledge(
        self,
        question: str,
        classification_category: ClassificationCategory | None = None,
        product_context: dict | None = None,
    ) -> TKResult:
        """Assess whether a query/product involves traditional knowledge.

        Args:
            question: The user's query/question
            classification_category: Optional pre-classified category
            product_context: Optional product/commercialization context

        Returns:
            TKResult with detection status, confidence, reasons, and considerations
        """
        # Collect evidence for TK detection
        evidence_points = []
        confidence_sum = 0.0

        # Check 1: Classification category
        if classification_category == ClassificationCategory.TRADITIONAL_KNOWLEDGE:
            evidence_points.append("Query was classified as TRADITIONAL_KNOWLEDGE")
            confidence_sum += 0.7

        # Check 2: Keywords in question
        tk_keyword_matches = self._count_keyword_matches(question, self.TK_KEYWORDS)
        if tk_keyword_matches > 0:
            evidence_points.append(f"Found {tk_keyword_matches} traditional knowledge keyword(s) in question")
            confidence_sum += min(0.6, tk_keyword_matches * 0.2)

        # Check 3: Ayurvedic-specific keywords
        ayurveda_matches = self._count_keyword_matches(question, self.AYURVEDIC_KEYWORDS)
        if ayurveda_matches > 0:
            evidence_points.append(f"Found {ayurveda_matches} Ayurveda-specific keyword(s)")
            confidence_sum += min(0.5, ayurveda_matches * 0.15)

        # Check 4: Product + TK indicators
        product_matches = self._count_keyword_matches(question, self.PRODUCT_KEYWORDS)
        if product_matches > 0 and (tk_keyword_matches > 0 or ayurveda_matches > 0):
            evidence_points.append("Query involves product and traditional knowledge indicators")
            confidence_sum += 0.3

        # Check 5: Product context
        tk_from_context = self._check_product_context_for_tk(product_context)
        if tk_from_context:
            evidence_points.extend(tk_from_context)
            confidence_sum += 0.3

        # Normalize confidence to 0-1 range
        final_confidence = min(1.0, confidence_sum)

        # Determine detection level based on evidence and confidence
        if len(evidence_points) == 0:
            return TKResult(
                detected=TKDetection.NOT_DETECTED,
                confidence=0.0,
                reasons=["No traditional knowledge indicators found in query"],
                considerations=[],
                source_status="not_applicable",
            )

        if final_confidence >= 0.7:
            detection = TKDetection.DETECTED
        elif final_confidence >= 0.4:
            detection = TKDetection.POSSIBLY_DETECTED
        else:
            detection = TKDetection.NOT_DETECTED if len(evidence_points) < 2 else TKDetection.POSSIBLY_DETECTED

        # Build considerations
        considerations = self._build_considerations(
            detection, ayurveda_matches > 0, tk_keyword_matches > 0, product_matches > 0
        )

        return TKResult(
            detected=detection,
            confidence=final_confidence,
            reasons=evidence_points,
            considerations=considerations,
            source_status="demo_unavailable",  # TKDL is not actually integrated
        )

    def _count_keyword_matches(self, text: str, keywords: set[str]) -> int:
        """Count how many keywords appear in text."""
        if not text or not isinstance(text, str):
            return 0
        text_lower = text.lower()
        return sum(1 for kw in keywords if kw in text_lower)

    def _check_product_context_for_tk(self, context: dict | None) -> list[str]:
        """Check product context for TK indicators."""
        if not context or not isinstance(context, dict):
            return []

        indicators = []

        # Check for traditional/formulation indicators in context
        for key in ["type", "product_type", "category", "description"]:
            if key in context:
                value_str = str(context[key]).lower()
                if any(kw in value_str for kw in ["traditional", "ayurvedic", "formulation"]):
                    indicators.append(f"Product context indicates traditional knowledge ({key})")

        return indicators

    def _build_considerations(
        self,
        detection: TKDetection,
        is_ayurvedic: bool,
        is_tk_query: bool,
        is_product: bool,
    ) -> list[str]:
        """Build a list of relevant TK considerations."""
        considerations = []

        if detection in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED):
            considerations.append(
                "Traditional knowledge considerations may be relevant to this query/product"
            )

            if is_ayurvedic:
                considerations.append(
                    "Query involves Ayurvedic knowledge; consider framework for "
                    "Ayurvedic product protection and commercialization"
                )

            if is_product:
                considerations.append(
                    "For commercialization of traditional products, review "
                    "Traditional Knowledge Digital Library (TKDL) status if applicable"
                )

            if is_tk_query and is_product:
                considerations.append(
                    "Traditional knowledge and product commercialization together may involve "
                    "Access and Benefit Sharing (ABS) considerations"
                )

        return considerations


# Singleton instance
tk_service = TraditionalKnowledgeService()

"""Access and Benefit Sharing (ABS) consideration service for IP-SAKTI.

Flags situations where biodiversity, biological resources, or traditional knowledge
considerations may require review under ABS frameworks (e.g., Nagoya Protocol).

This is a SUPPORT/FLAGGING mechanism only - NOT a legal compliance checker.
It does NOT invent legal requirements; it only flags potential considerations.
"""

from app.abs_models import ABSRelevance, ABSResult
from app.tk_models import TKDetection, TKResult


class ABSConsiderationService:
    """Access and Benefit Sharing (ABS) consideration detection service."""

    # Keywords indicating biological resources
    BIOLOGICAL_RESOURCE_KEYWORDS = {
        "biological", "biology", "biological material", "biological resource",
        "organism", "organisms", "species", "plant", "plants", "animal", "animals",
        "microorganism", "microbe", "microbes", "genetic material", "genetic resource",
        "biodiversity", "biodiversity resource",
    }

    # Keywords indicating plant/herbal context
    PLANT_HERBAL_KEYWORDS = {
        "plant", "plants", "herbal", "herb", "herbs", "medicinal plant", "medicinal herb",
        "botanical", "flora", "flower", "leaf", "leaves", "root", "seeds", "spice",
        "bark", "extract", "extract", "oil", "infusion",
    }

    # Keywords indicating medicinal/pharmaceutical context
    MEDICINAL_KEYWORDS = {
        "medicinal", "medicine", "pharmaceutical", "remedy", "cure", "treatment",
        "drug", "medication", "health", "wellness", "therapeutic",
    }

    # Keywords indicating commercialization
    COMMERCIALIZATION_KEYWORDS = {
        "sell", "selling", "sale", "product", "market", "commercializ",
        "business", "profit", "commercial", "export", "import",
    }

    def assess_abs_relevance(
        self,
        question: str,
        tk_result: TKResult | None = None,
        product_context: dict | None = None,
    ) -> ABSResult:
        """Assess whether ABS (Access and Benefit Sharing) considerations are relevant.

        Args:
            question: The user's query/question
            tk_result: Optional result from TK detection service
            product_context: Optional product/commercialization context

        Returns:
            ABSResult with relevance status, confidence, reasons, and considerations
        """
        # Collect evidence for ABS relevance
        evidence_points = []
        confidence_sum = 0.0

        # Check 1: Biological resource keywords
        bio_matches = self._count_keyword_matches(question, self.BIOLOGICAL_RESOURCE_KEYWORDS)
        if bio_matches > 0:
            evidence_points.append(f"Found {bio_matches} biological resource keyword(s)")
            confidence_sum += min(0.6, bio_matches * 0.15)

        # Check 2: Plant/herbal keywords
        plant_matches = self._count_keyword_matches(question, self.PLANT_HERBAL_KEYWORDS)
        if plant_matches > 0:
            evidence_points.append(f"Found {plant_matches} plant/herbal keyword(s)")
            confidence_sum += min(0.5, plant_matches * 0.12)

        # Check 3: Medicinal/pharmaceutical keywords
        medicinal_matches = self._count_keyword_matches(question, self.MEDICINAL_KEYWORDS)
        if medicinal_matches > 0:
            evidence_points.append(f"Found {medicinal_matches} medicinal/pharmaceutical keyword(s)")
            confidence_sum += min(0.5, medicinal_matches * 0.12)

        # Check 4: Commercialization context (ABS applies to commercial use of biological resources)
        commercial_matches = self._count_keyword_matches(question, self.COMMERCIALIZATION_KEYWORDS)
        if commercial_matches > 0:
            evidence_points.append(f"Found {commercial_matches} commercialization indicator(s)")
            confidence_sum += min(0.4, commercial_matches * 0.1)
            # Commercialization + biological resource is stronger signal
            if (bio_matches > 0 or plant_matches > 0) and commercial_matches > 0:
                confidence_sum += 0.2

        # Check 5: TK + biological resource (strong ABS signal)
        if tk_result and tk_result.detected in (TKDetection.DETECTED, TKDetection.POSSIBLY_DETECTED):
            if bio_matches > 0 or plant_matches > 0:
                evidence_points.append(
                    "Query involves both traditional knowledge and biological/plant resources"
                )
                confidence_sum += 0.4

        # Check 6: Product context
        abs_from_context = self._check_product_context_for_abs(product_context)
        if abs_from_context:
            evidence_points.extend(abs_from_context)
            confidence_sum += 0.3

        # Normalize confidence to 0-1 range
        final_confidence = min(1.0, confidence_sum)

        # Determine relevance based on evidence and confidence
        if len(evidence_points) == 0:
            return ABSResult(
                relevance=ABSRelevance.NOT_DETECTED,
                confidence=0.0,
                reasons=["No ABS-relevant indicators found in query"],
                considerations=[],
            )

        if final_confidence >= 0.7:
            relevance = ABSRelevance.RELEVANT
        elif final_confidence >= 0.4:
            relevance = ABSRelevance.POSSIBLY_RELEVANT
        else:
            relevance = ABSRelevance.NOT_DETECTED if len(evidence_points) < 2 else ABSRelevance.POSSIBLY_RELEVANT

        # Build considerations
        considerations = self._build_considerations(
            relevance,
            bio_matches > 0,
            plant_matches > 0,
            medicinal_matches > 0,
            commercial_matches > 0,
            tk_result is not None and tk_result.detected == TKDetection.DETECTED,
        )

        return ABSResult(
            relevance=relevance,
            confidence=final_confidence,
            reasons=evidence_points,
            considerations=considerations,
        )

    def _count_keyword_matches(self, text: str, keywords: set[str]) -> int:
        """Count how many keywords appear in text."""
        if not text or not isinstance(text, str):
            return 0
        text_lower = text.lower()
        return sum(1 for kw in keywords if kw in text_lower)

    def _check_product_context_for_abs(self, context: dict | None) -> list[str]:
        """Check product context for ABS indicators."""
        if not context or not isinstance(context, dict):
            return []

        indicators = []

        # Check for biological/plant/medicinal indicators
        for key in ["type", "product_type", "category", "description", "source"]:
            if key in context:
                value_str = str(context[key]).lower()
                if any(kw in value_str for kw in ["plant", "herbal", "biological", "medicinal"]):
                    indicators.append(f"Product context indicates biological/plant resource ({key})")

        # Check for commercialization intent
        for key in ["commercial", "commercialization", "market", "sell", "export"]:
            if key in context and context[key]:
                indicators.append(f"Product context indicates commercialization intent ({key})")

        return indicators

    def _build_considerations(
        self,
        relevance: ABSRelevance,
        has_biological: bool,
        has_plant: bool,
        has_medicinal: bool,
        has_commercial: bool,
        has_tk: bool,
    ) -> list[str]:
        """Build a list of relevant ABS considerations."""
        considerations = []

        if relevance in (ABSRelevance.RELEVANT, ABSRelevance.POSSIBLY_RELEVANT):
            considerations.append(
                "Access and Benefit Sharing (ABS) considerations may be relevant to this query/product"
            )

            if has_plant and has_commercial:
                considerations.append(
                    "For commercialization of plant-based resources, review ABS requirements "
                    "(e.g., Nagoya Protocol compliance, Prior Informed Consent)"
                )

            if has_biological and has_tk:
                considerations.append(
                    "Traditional knowledge associated with biological resources may require "
                    "benefit-sharing arrangements"
                )

            if has_tk:
                considerations.append(
                    "Ensure benefit-sharing framework compliance for traditional knowledge use"
                )

            # Note: We do NOT fabricate specific legal requirements
            considerations.append(
                "This is a flag for potential ABS consideration only, not a legal determination"
            )

        return considerations


# Singleton instance
abs_service = ABSConsiderationService()

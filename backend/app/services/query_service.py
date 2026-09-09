from app.config import settings
from app.models import QueryRequest, QueryResponse
from app.services.knowledge_base_service import KnowledgeBaseService, knowledge_base
from app.services.query_classifier import QueryClassifier
from app.services.llm_service import FallbackLLMService, LLMService, create_llm_service


NO_EVIDENCE_ANSWER = (
    "I could not find sufficient evidence in the IP-SAKTI knowledge base to answer "
    "this question reliably. Please provide more specific context or consult an "
    "appropriate qualified professional."
)


class QueryService:
    def __init__(
        self,
        knowledge_base_service: KnowledgeBaseService,
        llm_service: LLMService,
        classifier: QueryClassifier | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base_service
        self.llm = llm_service
        self.classifier = classifier or QueryClassifier()

    def answer_query(self, request: QueryRequest) -> QueryResponse:
        classification = self.classifier.classify(request.question)
        evidence = self.knowledge_base.search(request.question, limit=settings.retrieval_limit)
        if not evidence:
            return QueryResponse(
                answer=NO_EVIDENCE_ANSWER,
                evidence=[],
                classification=classification,
                grounded=False,
                evidence_status="insufficient",
                provider="none",
                confidence=0,
                disclaimer="No matching demo evidence was found; this is not legal or regulatory advice.",
            )

        try:
            generated = self.llm.generate_answer(request.question, evidence)
        except Exception:
            generated = FallbackLLMService().generate_answer(request.question, evidence)

        grounded = bool(generated.grounded and evidence)
        evidence_status = "sufficient" if grounded else "insufficient"
        confidence = generated.confidence if grounded else 0
        return QueryResponse(
            answer=generated.answer,
            evidence=evidence,
            classification=classification,
            grounded=grounded,
            evidence_status=evidence_status,
            provider=generated.provider,
            confidence=confidence,
            disclaimer="Evidence is synthetic demo content and is not legal or regulatory advice.",
        )


query_service = QueryService(knowledge_base, create_llm_service(settings))


def answer_query(request: QueryRequest) -> QueryResponse:
    """Compatibility wrapper for callers using the Phase 1 function API."""
    return query_service.answer_query(request)

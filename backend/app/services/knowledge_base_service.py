from app.knowledge_models import DocumentChunk, Evidence, KnowledgeDocument
from app.repositories.knowledge_repository import KnowledgeRepository
from app.services.retriever import KeywordRetriever


class KnowledgeBaseService:
    """Compatibility facade combining repository access and retrieval."""

    def __init__(
        self,
        documents: list[KnowledgeDocument] | None = None,
        chunks: list[DocumentChunk] | None = None,
        repository: KnowledgeRepository | None = None,
        retriever: KeywordRetriever | None = None,
    ) -> None:
        self.repository = repository or KnowledgeRepository(documents=documents, chunks=chunks)
        self.retriever = retriever or KeywordRetriever(self.repository)

    def load_demo_documents(self) -> list[KnowledgeDocument]:
        return self.repository.list_documents()

    def list_documents(self) -> list[KnowledgeDocument]:
        return self.repository.list_documents()

    def get_chunks(self, document_id: str) -> list[DocumentChunk]:
        return self.repository.get_chunks(document_id)

    def search(self, query: str, limit: int = 10) -> list[Evidence]:
        return self.retriever.search(query, limit=limit)


knowledge_base = KnowledgeBaseService()

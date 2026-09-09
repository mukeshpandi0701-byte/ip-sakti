from app.data.demo_documents import DEMO_CHUNKS, DEMO_DOCUMENTS
from app.knowledge_models import DocumentChunk, KnowledgeDocument


class KnowledgeRepository:
    """In-memory document and chunk store for the current MVP."""

    def __init__(
        self,
        documents: list[KnowledgeDocument] | None = None,
        chunks: list[DocumentChunk] | None = None,
    ) -> None:
        self._documents = list(documents if documents is not None else DEMO_DOCUMENTS)
        if chunks is not None:
            self._chunks = list(chunks)
        elif documents is None:
            self._chunks = list(DEMO_CHUNKS)
        else:
            self._chunks = [chunk for document in self._documents for chunk in document.chunks]

    def list_documents(self) -> list[KnowledgeDocument]:
        return list(self._documents)

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        return next((document for document in self._documents if document.id == document_id), None)

    def get_chunks(self, document_id: str) -> list[DocumentChunk]:
        return [chunk for chunk in self._chunks if chunk.document_id == document_id]

    def list_chunks(self) -> list[DocumentChunk]:
        return list(self._chunks)

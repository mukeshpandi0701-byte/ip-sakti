import re

from app.data.demo_documents import DEMO_CHUNKS, DEMO_DOCUMENTS
from app.knowledge_models import DocumentChunk, Evidence, KnowledgeDocument


class KnowledgeBaseService:
    """Deterministic in-memory knowledge base for the Phase 2 foundation."""

    def __init__(
        self,
        documents: list[KnowledgeDocument] | None = None,
        chunks: list[DocumentChunk] | None = None,
    ) -> None:
        self._documents = list(documents if documents is not None else DEMO_DOCUMENTS)
        self._chunks = list(chunks if chunks is not None else DEMO_CHUNKS)

    def load_demo_documents(self) -> list[KnowledgeDocument]:
        return list(self._documents)

    def list_documents(self) -> list[KnowledgeDocument]:
        return self.load_demo_documents()

    def get_chunks(self, document_id: str) -> list[DocumentChunk]:
        return [chunk for chunk in self._chunks if chunk.document_id == document_id]

    def search(
        self,
        query: str,
        limit: int = 10,
        source_types: tuple[str, ...] | list[str] | None = None,
    ) -> list[Evidence]:
        """Search deterministically, optionally preferring matching source types.

        Routing hints only narrow results when at least one keyword match has a preferred
        type. Otherwise all matches remain available, which preserves synthetic demo
        retrieval while the knowledge base has no category-specific source types.
        """
        terms = self._terms(query)
        if not terms:
            return []

        documents_by_id = {document.id: document for document in self._documents}
        matches: list[tuple[float, DocumentChunk, KnowledgeDocument]] = []
        for chunk in self._chunks:
            document = documents_by_id.get(chunk.document_id)
            if document is None:
                continue
            haystack = f"{document.title} {document.content}".casefold()
            haystack_terms = set(self._terms(haystack))
            matched_terms = sum(term in haystack_terms for term in terms)
            if matched_terms == 0:
                continue
            score = matched_terms / len(terms)
            matches.append((score, chunk, document))

        preferred_source_types = set(source_types or ())
        preferred_matches = [
            match for match in matches if match[2].source_type in preferred_source_types
        ]
        if preferred_matches:
            matches = preferred_matches

        matches.sort(key=lambda item: (-item[0], item[1].document_id, item[1].chunk_index))
        return [
            Evidence(
                document_id=document.id,
                chunk_id=chunk.id,
                title=document.title,
                excerpt=chunk.content,
                source=document.source,
                authority=document.authority,
                relevance_score=score,
                metadata={**document.metadata, **chunk.metadata},
            )
            for score, chunk, document in matches[:limit]
        ]

    @staticmethod
    def _terms(query: str) -> list[str]:
        return sorted(set(re.findall(r"[\w'-]+", query.casefold())))


knowledge_base = KnowledgeBaseService()

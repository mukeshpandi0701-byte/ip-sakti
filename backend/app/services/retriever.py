import re

from app.knowledge_models import DocumentChunk, Evidence, KnowledgeDocument
from app.repositories.knowledge_repository import KnowledgeRepository


class KeywordRetriever:
    """Deterministic whole-word retriever over repository documents and chunks."""

    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def search(self, query: str, limit: int = 10) -> list[Evidence]:
        terms = self._terms(query)
        if not terms:
            return []

        matches: list[tuple[float, DocumentChunk, KnowledgeDocument]] = []
        for chunk in self.repository.list_chunks():
            document = self.repository.get_document(chunk.document_id)
            if document is None:
                continue
            haystack = f"{document.title} {document.content}".casefold()
            haystack_terms = set(self._terms(haystack))
            matched_terms = sum(term in haystack_terms for term in terms)
            if matched_terms == 0:
                continue
            score = matched_terms / len(terms)
            matches.append((score, chunk, document))

        matches.sort(key=lambda item: (-item[0], item[1].document_id, item[1].chunk_index))
        return [
            Evidence(
                document_id=document.id,
                chunk_id=chunk.id,
                title=document.title,
                excerpt=chunk.content,
                source=document.source,
                authority=document.authority,
                source_type=document.source_type,
                relevance_score=score,
                metadata={**document.metadata, **chunk.metadata},
            )
            for score, chunk, document in matches[:limit]
        ]

    @staticmethod
    def _terms(query: str) -> list[str]:
        return sorted(set(re.findall(r"[\w'-]+", query.casefold())))

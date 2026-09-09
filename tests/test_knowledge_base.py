import sys
from pathlib import Path

import pytest
from pydantic import ValidationError


sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))

from app.knowledge_models import DocumentChunk, Evidence, KnowledgeDocument  # noqa: E402
from app.repositories.knowledge_repository import KnowledgeRepository  # noqa: E402
from app.services.knowledge_base_service import KnowledgeBaseService  # noqa: E402


def test_document_and_chunk_models_validate_required_fields() -> None:
    document = KnowledgeDocument(
        id="doc-1",
        title="Demo document",
        content="Synthetic content.",
        source="Synthetic source",
        source_type="synthetic_demo",
        authority="Not authoritative",
        jurisdiction="Demo",
        language="en",
    )
    chunk = DocumentChunk(
        id="chunk-1",
        document_id=document.id,
        content=document.content,
        chunk_index=0,
    )

    assert document.metadata == {}
    assert document.document_id == "doc-1"
    assert document.id == "doc-1"
    assert document.publication_date is None
    assert document.last_updated is None
    assert chunk.document_id == "doc-1"
    assert chunk.id == "chunk-1"
    with pytest.raises(ValidationError):
        DocumentChunk(id="chunk-2", document_id="doc-1", content="", chunk_index=0)


def test_evidence_model_is_typed() -> None:
    evidence = Evidence(
        document_id="doc-1",
        chunk_id="chunk-1",
        title="Demo",
        excerpt="Synthetic excerpt.",
        source="Synthetic source",
        authority="Not authoritative",
        relevance_score=0.5,
    )

    assert evidence.relevance_score == 0.5
    assert evidence.source_type == "unknown"
    assert evidence.metadata == {}


def test_demo_documents_load_and_chunks_are_retrievable() -> None:
    service = KnowledgeBaseService()

    documents = service.load_demo_documents()

    assert len(documents) >= 2
    assert all(document.metadata["demo"] is True for document in documents)
    assert service.get_chunks(documents[0].id)[0].document_id == documents[0].id


def test_repository_retrieves_documents_without_search_logic() -> None:
    repository = KnowledgeRepository()

    documents = repository.list_documents()
    document = repository.get_document("demo-branding-02")

    assert len(documents) == 2
    assert document is not None
    assert document.document_id == "demo-branding-02"
    assert repository.get_chunks(document.document_id)[0].document_id == document.document_id


def test_search_returns_evidence_objects_in_deterministic_order() -> None:
    service = KnowledgeBaseService()

    results = service.search("traditional knowledge")

    assert results
    assert all(isinstance(result, Evidence) for result in results)
    assert results[0].document_id == "demo-traditional-knowledge-01"
    assert results[0].relevance_score > 0
    assert results[0].source_type == "synthetic_demo"
    assert results[0].source == "IP-SAKTI synthetic demo knowledge base"
    assert results[0].metadata["demo"] is True


def test_keyword_retrieval_returns_multiple_ranked_results() -> None:
    results = KnowledgeBaseService().search("traditional branding")

    assert len(results) == 2
    assert results[0].relevance_score >= results[1].relevance_score
    assert {result.document_id for result in results} == {
        "demo-traditional-knowledge-01",
        "demo-branding-02",
    }


def test_empty_and_no_match_search_return_no_results() -> None:
    service = KnowledgeBaseService()

    assert service.search("") == []
    assert service.search("quantum spaceship patent") == []

from app.knowledge_models import DocumentChunk, KnowledgeDocument


DEMO_SOURCE = "IP-SAKTI synthetic demo knowledge base"
DEMO_AUTHORITY = "Not authoritative; synthetic demo content"
DEMO_JURISDICTION = "Demo only; no legal jurisdiction"


DEMO_DOCUMENTS: list[KnowledgeDocument] = [
    KnowledgeDocument(
        id="demo-traditional-knowledge-01",
        title="Synthetic note: documenting traditional knowledge",
        content=(
            "A knowledge-base record can describe a traditional practice, its local context, "
            "and the people who contributed the description. Good records distinguish "
            "community knowledge from newly created branding or packaging."
        ),
        source=DEMO_SOURCE,
        source_type="synthetic_demo",
        authority=DEMO_AUTHORITY,
        jurisdiction=DEMO_JURISDICTION,
        language="en",
        metadata={"topic": "traditional knowledge", "demo": True},
    ),
    KnowledgeDocument(
        id="demo-branding-02",
        title="Synthetic note: names and branding for an Ayurveda product",
        content=(
            "A product team may separately consider its brand name, logo, packaging, and "
            "technical formulation. This synthetic note is a planning prompt only and does "
            "not state what any real trademark or regulatory authority requires."
        ),
        source=DEMO_SOURCE,
        source_type="synthetic_demo",
        authority=DEMO_AUTHORITY,
        jurisdiction=DEMO_JURISDICTION,
        language="en",
        metadata={"topic": "branding", "demo": True},
    ),
]


DEMO_CHUNKS: list[DocumentChunk] = [
    DocumentChunk(
        id="demo-traditional-knowledge-01-chunk-0",
        document_id="demo-traditional-knowledge-01",
        content=DEMO_DOCUMENTS[0].content,
        chunk_index=0,
        metadata={"demo": True},
    ),
    DocumentChunk(
        id="demo-branding-02-chunk-0",
        document_id="demo-branding-02",
        content=DEMO_DOCUMENTS[1].content,
        chunk_index=0,
        metadata={"demo": True},
    ),
]

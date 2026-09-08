from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.knowledge_models import Evidence, KnowledgeDocument
from app.models import QueryRequest, QueryResponse
from app.services.knowledge_base_service import knowledge_base
from app.services.query_service import answer_query


app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@app.post("/api/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return answer_query(request)


@app.get("/api/knowledge/documents", response_model=list[KnowledgeDocument])
def list_knowledge_documents() -> list[KnowledgeDocument]:
    return knowledge_base.list_documents()


@app.get("/api/knowledge/search", response_model=list[Evidence])
def search_knowledge(
    q: str = Query(default="", max_length=2000),
) -> list[Evidence]:
    return knowledge_base.search(q)

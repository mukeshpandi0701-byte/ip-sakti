import json

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import settings
from app.knowledge_models import Evidence, KnowledgeDocument
from app.models import QueryRequest, QueryResponse, UserEvidenceIntakeResponse
from app.services.knowledge_base_service import knowledge_base
from app.services.query_service import answer_query
from app.services.user_evidence_service import UserEvidenceService, UserEvidenceValidationError


app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
user_evidence_service = UserEvidenceService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


async def _read_uploads(request: Request) -> tuple[list[tuple[str, str, bytes]], dict[str, str]]:
    form = await request.form()
    uploads = [item for item in form.getlist("files") if isinstance(item, StarletteUploadFile)]
    files = [
        (upload.filename or "unnamed", upload.content_type or "application/octet-stream", await upload.read())
        for upload in uploads
    ]
    fields = {
        field: value
        for field in ("question", "response_language", "jurisdiction")
        if isinstance((value := form.get(field)), str)
    }
    return files, fields


@app.post("/api/evidence/intake", response_model=UserEvidenceIntakeResponse)
async def intake_user_evidence(request: Request) -> UserEvidenceIntakeResponse:
    if not request.headers.get("content-type", "").casefold().startswith("multipart/form-data"):
        raise HTTPException(status_code=415, detail="Use multipart/form-data with one or more files.")
    try:
        uploads, _ = await _read_uploads(request)
        if not uploads:
            raise UserEvidenceValidationError("At least one file is required.")
        processed, _ = user_evidence_service.process_files(uploads)
    except UserEvidenceValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return UserEvidenceIntakeResponse(user_evidence=processed)


@app.post("/api/query", response_model=QueryResponse)
async def query(request: Request) -> QueryResponse:
    content_type = request.headers.get("content-type", "").casefold()
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        question_value = form.get("question")
        if not isinstance(question_value, str):
            raise HTTPException(status_code=422, detail="A question field is required.")
        try:
            processed, user_context = user_evidence_service.process_files(
                (await _read_uploads(request))[0]
            )
            query_request = QueryRequest(
                question=question_value,
                response_language=form.get("response_language", "en"),
                jurisdiction=form.get("jurisdiction", "india"),
            )
        except UserEvidenceValidationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=json.loads(exc.json())) from exc
        return answer_query(query_request, user_context=user_context, user_evidence=processed)

    try:
        query_request = QueryRequest.model_validate(await request.json())
    except (json.JSONDecodeError, ValidationError) as exc:
        detail = json.loads(exc.json()) if isinstance(exc, ValidationError) else "Invalid JSON request body."
        raise HTTPException(status_code=422, detail=detail) from exc
    return answer_query(query_request)


@app.get("/api/knowledge/documents", response_model=list[KnowledgeDocument])
def list_knowledge_documents() -> list[KnowledgeDocument]:
    return knowledge_base.list_documents()


@app.get("/api/knowledge/search", response_model=list[Evidence])
def search_knowledge(
    q: str = Query(default="", max_length=2000),
) -> list[Evidence]:
    return knowledge_base.search(q)

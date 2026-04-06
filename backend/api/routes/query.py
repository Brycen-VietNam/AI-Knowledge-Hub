# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S005
# Task: T002 — POST /v1/query schema + auth wire-up (stub)
# Task: T003 — RBAC group resolution + retrieve() + audit log (full impl)
# Decision: D01 — user_group_id IS NULL = public document
# Decision: D04 — 0-group users → empty/public results, not 403
# Rule: R001 — RBAC at WHERE clause (retriever layer, not here)
# Rule: R003 — verify_token on every endpoint
# Rule: R004 — /v1/ prefix required
# Rule: R006 — audit log before return (background task)
# Rule: R007 — asyncio.wait_for timeout=1.8s
import asyncio
import hashlib
from uuid import uuid4

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.db.session import async_session_factory
from backend.rag.retriever import QueryTimeoutError, RetrievedDocument, retrieve


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str = Field(..., max_length=512)
    top_k: int = Field(default=10, ge=1, le=100)


class QueryResult(BaseModel):
    doc_id: str
    chunk_index: int
    score: float
    is_public: bool
    content: str | None = None


class QueryResponse(BaseModel):
    request_id: str
    results: list[QueryResult]


# ---------------------------------------------------------------------------
# Embedder stub — replaced when embedder service is wired
# ---------------------------------------------------------------------------

async def embed(_text: str) -> list[float]:
    """Stub: returns zero vector until real embedder is integrated."""
    return [0.0] * 1024


# ---------------------------------------------------------------------------
# Audit log helper (module-private, runs in background)
# ---------------------------------------------------------------------------

async def _write_audit(
    user_id,
    docs: list[RetrievedDocument],
    query_hash: str,
) -> None:
    """Write one audit_log row per retrieved document. Non-blocking background task.

    Opens its own session from the factory — safe to run after the request session closes.
    """
    from backend.db.models.audit_log import AuditLog

    async with async_session_factory() as session:
        async with session.begin():
            for doc in docs:
                session.add(AuditLog(
                    user_id=user_id,
                    doc_id=doc.doc_id,
                    query_hash=query_hash,
                ))


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()


@router.post("/v1/query", response_model=QueryResponse)
async def query_documents(
    body: QueryRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QueryResponse:
    """POST /v1/query — hybrid RAG retrieval with RBAC hard-filter.

    Group IDs are pre-populated on AuthenticatedUser by verify_token:
      - API-key path: api_keys.user_group_ids (list[int])
      - OIDC path:    group names resolved to IDs in verify_oidc_token
    0-group users (user_group_ids=[]) receive public-only results — not 403 (D04).
    """
    request_id = str(uuid4())
    query_hash = hashlib.sha256(body.query.encode()).hexdigest()

    try:
        query_embedding = await embed(body.query)
        docs: list[RetrievedDocument] = await asyncio.wait_for(
            retrieve(
                query_embedding=query_embedding,
                user_group_ids=user.user_group_ids,
                top_k=body.top_k,
                session=db,
            ),
            timeout=1.8,
        )
    except (TimeoutError, QueryTimeoutError):  # TimeoutError is the builtin; asyncio.TimeoutError is an alias
        return JSONResponse(
            status_code=504,
            content={"error": {
                "code": "QUERY_TIMEOUT",
                "message": "Retrieval exceeded 1800ms SLA",
                "request_id": request_id,
            }},
        )

    background_tasks.add_task(_write_audit, user.user_id, docs, query_hash)

    results = [
        QueryResult(
            doc_id=str(d.doc_id),
            chunk_index=d.chunk_index,
            score=d.score,
            is_public=d.user_group_id is None,
            content=d.content,
        )
        for d in docs
    ]
    return QueryResponse(request_id=request_id, results=results)

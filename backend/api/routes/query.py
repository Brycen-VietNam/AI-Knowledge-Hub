# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S005
# Spec: docs/llm-provider/spec/llm-provider.spec.md#S005
# Task: T002 — POST /v1/query schema + auth wire-up (stub)
# Task: T003 — RBAC group resolution + retrieve() + audit log (full impl)
# Task: T014 — LLM generation wire-up + D10 QueryResponse breaking change
# Decision: D01 — user_group_id IS NULL = public document
# Decision: D04 — 0-group users → empty/public results, not 403
# Decision: D08 — api-agent calls generate_answer(), not LLMProviderFactory (ARCH A002)
# Decision: D09 — NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}
# Decision: D10 — QueryResponse breaking change: results[] → answer + sources + low_confidence
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
from backend.rag.generator import generate_answer
from backend.rag.llm import NoRelevantChunksError
from backend.rag.retriever import QueryTimeoutError, RetrievedDocument, retrieve


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str = Field(..., max_length=512)
    top_k: int = Field(default=10, ge=1, le=100)


class QueryResponse(BaseModel):
    # D10: breaking change — results[] replaced with answer + sources + low_confidence
    request_id: str          # retained — R005 traceability (D12)
    answer: str | None
    sources: list[str]
    low_confidence: bool
    reason: str | None = None  # populated only when answer is None (D09)


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

    chunks = [d.content for d in docs if d.content is not None]
    try:
        llm_result = await asyncio.wait_for(
            generate_answer(body.query, chunks),
            timeout=1.8,
        )
    except (TimeoutError, asyncio.TimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {
                "code": "LLM_TIMEOUT",
                "message": "LLM generation exceeded 1800ms SLA",
                "request_id": request_id,
            }},
        )
    except NoRelevantChunksError:
        # D09: bot-friendly — no 4xx, return null answer with reason
        return QueryResponse(
            request_id=request_id,
            answer=None,
            sources=[],
            low_confidence=False,
            reason="no_relevant_chunks",
        )
    return QueryResponse(
        request_id=request_id,
        answer=llm_result.answer,
        sources=llm_result.sources,
        low_confidence=llm_result.low_confidence,
    )

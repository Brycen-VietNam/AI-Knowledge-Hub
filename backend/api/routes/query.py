# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S005
# Spec: docs/llm-provider/spec/llm-provider.spec.md#S005
# Spec: docs/query-endpoint/spec/query-endpoint.spec.md#S003
# Task: T002 — POST /v1/query schema + auth wire-up (stub)
# Task: T003 — RBAC group resolution + retrieve() + audit log (full impl)
# Task: T014 — LLM generation wire-up + D10 QueryResponse breaking change
# Task: S003-T003 — Rate limiting: inject RateLimiter, add headers, 429 on exceed
# Decision: D01 — user_group_id IS NULL = public document
# Decision: D04 — 0-group users → empty/public results, not 403
# Decision: D08 — api-agent calls generate_answer(), not LLMProviderFactory (ARCH A002)
# Decision: D09 — NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}
# Decision: D10 — QueryResponse breaking change: results[] → answer + sources + low_confidence
# Rule: R001 — RBAC at WHERE clause (retriever layer, not here)
# Rule: R003 — verify_token on every endpoint
# Rule: R004 — /v1/ prefix required
# Rule: R006 — audit log before return (background task)
# Rule: R007 — asyncio.wait_for total SLA=1.8s; split: retrieval=1.0s (A2), LLM=0.8s (S002)
# Task: S004-T001 — Strip control chars from query (SECURITY S003)
# Task: S004-T003 — request_id stored in request.state for exception handlers
# Rule: S004 — 60 req/min per user_id via Valkey sliding window
import asyncio
import hashlib
import re
from uuid import uuid4

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.middleware.rate_limiter import RateLimiter
from backend.api.models.citation import CitationObject
from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.db.session import async_session_factory
from backend.rag.generator import generate_answer
from backend.rag.llm import LLMError, NoRelevantChunksError
from backend.rag.retriever import QueryTimeoutError, RetrievedDocument
from backend.rag.search import search

# S003: module-level singleton — replaced at startup via app.state in production;
# also patchable in tests via: patch("backend.api.routes.query._rate_limiter")
_rate_limiter = RateLimiter(resource="query", limit=60, window=60)

# R007/A2: 1.8s total SLA split — retrieval 1.0s + LLM 0.8s (confirmed lb_mui 2026-04-08)
# Dev override: *_TIMEOUT_OVERRIDE env vars allow increasing for local Ollama testing
import os as _os
_RETRIEVAL_TIMEOUT = float(_os.getenv("RETRIEVAL_TIMEOUT_OVERRIDE", "1.0"))
_LLM_TIMEOUT = float(_os.getenv("LLM_TIMEOUT_OVERRIDE", "0.8"))
# C014: confidence threshold below which low_confidence=True is set
_LOW_CONFIDENCE_THRESHOLD = 0.4


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str = Field(..., max_length=512)
    top_k: int = Field(default=10, ge=1, le=100)
    lang: str | None = None  # A1/D4: None=auto-detect; e.g. "ja" skips detection

    @field_validator("query")
    @classmethod
    def strip_control_chars(cls, v: str) -> str:
        # S004-T001 / SECURITY S003: strip ASCII control characters before embedding
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)


class QueryResponse(BaseModel):
    # D10: breaking change — results[] replaced with answer + sources + low_confidence
    # S002: citations added alongside sources (D-CIT-01 — additive, no breaking change)
    request_id: str          # retained — R005 traceability (D12)
    answer: str | None
    sources: list[str]
    low_confidence: bool
    reason: str | None = None  # populated only when answer is None (D09)
    citations: list[CitationObject] = Field(default_factory=list)  # AC10: never null


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
    request: Request,
    response: Response,
    body: QueryRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QueryResponse | JSONResponse:
    """POST /v1/query — hybrid RAG retrieval with RBAC hard-filter.

    Group IDs are pre-populated on AuthenticatedUser by verify_token:
      - API-key path: api_keys.user_group_ids (list[int])
      - OIDC path:    group names resolved to IDs in verify_oidc_token
    0-group users (user_group_ids=[]) receive public-only results — not 403 (D04).
    """
    request_id = str(uuid4())
    # S004-T003: store in request.state so exception handlers can reuse the same id
    request.state.request_id = request_id
    query_hash = hashlib.sha256(body.query.encode()).hexdigest()

    # S003: rate limiting — 60 req/min per user_id sliding window
    valkey_client = getattr(getattr(request, "app", None), "state", None)
    valkey_client = getattr(valkey_client, "valkey_client", None)
    allowed, rl_remaining, rl_reset = await _rate_limiter.check(
        str(user.user_id), valkey_client
    )
    # AC7: set rate-limit headers on every response (success and 429)
    response.headers["X-RateLimit-Remaining"] = str(rl_remaining)
    response.headers["X-RateLimit-Reset"] = str(rl_reset)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit of 60 requests per minute exceeded",
                "request_id": request_id,
            }},
            headers={
                "X-RateLimit-Remaining": str(rl_remaining),
                "X-RateLimit-Reset": str(rl_reset),
            },
        )

    try:
        docs: list[RetrievedDocument] = await asyncio.wait_for(
            search(
                query=body.query,
                lang=body.lang,
                user_group_ids=user.user_group_ids,
                top_k=body.top_k,
                session=db,
            ),
            timeout=_RETRIEVAL_TIMEOUT,
        )
    except (asyncio.TimeoutError, QueryTimeoutError):
        return JSONResponse(
            status_code=504,
            content={"error": {
                "code": "QUERY_TIMEOUT",
                "message": "Retrieval exceeded 1000ms SLA",
                "request_id": request_id,
            }},
        )

    background_tasks.add_task(_write_audit, user.user_id, docs, query_hash)

    if not docs:
        return QueryResponse(
            request_id=request_id,
            answer=None,
            sources=[],
            low_confidence=False,
            reason="no_relevant_chunks",
            citations=[],
        )

    # S002: T002 — LLM generation with 0.8s budget (A2)
    # S003-T006: build content_docs once so doc_titles and chunks share the same index
    content_docs = [d for d in docs if d.content]
    try:
        llm_response = await asyncio.wait_for(
            generate_answer(
                query=body.query,
                chunks=[d.content for d in content_docs],
                doc_titles=[d.title or "" for d in content_docs],
            ),
            timeout=_LLM_TIMEOUT,
        )
    except NoRelevantChunksError:
        # D09: no context chunks → 200 with null answer (not an error)
        return QueryResponse(
            request_id=request_id,
            answer=None,
            sources=[],
            low_confidence=False,
            reason="no_relevant_chunks",
            citations=[],
        )
    except (asyncio.TimeoutError, LLMError):
        return JSONResponse(
            status_code=503,
            content={"error": {
                "code": "LLM_UNAVAILABLE",
                "message": "LLM generation failed or exceeded 800ms budget",
                "request_id": request_id,
            }},
        )

    # S002: T004 — C014 low_confidence threshold
    # S002-T002 (answer-citation): build CitationObject list from same docs — D-CIT-05
    citations = [
        CitationObject(
            doc_id=str(d.doc_id),
            title=d.title or "",
            source_url=d.source_url,
            chunk_index=d.chunk_index,
            score=round(d.score, 4),
            lang=d.lang or "",
        )
        for d in docs
    ]
    return QueryResponse(
        request_id=request_id,
        answer=llm_response.answer,
        sources=[str(d.doc_id) for d in docs],
        low_confidence=llm_response.confidence < _LOW_CONFIDENCE_THRESHOLD,
        reason=None,
        citations=citations,
    )

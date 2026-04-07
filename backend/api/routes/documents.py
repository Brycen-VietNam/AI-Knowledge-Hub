# Spec: docs/document-ingestion/spec/document-ingestion.spec.md
# Task: S001-T001 — DocumentUpload schema + router scaffold
# Task: S001-T002 — auth_type write gate (D09)
# Task: S001-T003 — input validation (lang, content size)
# Task: S001-T004 — RBAC group membership check
# Task: S001-T005 — Document INSERT + BackgroundTasks dispatch + 202
# Task: S005-api-T001 — GET /v1/documents (paginated, RBAC-filtered)
# Task: S005-api-T002 — GET /v1/documents/{id} (metadata + 404)
# Task: S005-api-T003 — DELETE /v1/documents/{id} (204 + 404)
# Decision: D09 — api_key=write, OIDC=read-only
# Decision: D11 — content NOT stored in documents; passed to ingest_pipeline as arg
# Rule: R001 — RBAC at WHERE clause (read paths)
# Rule: R003 — verify_token on every endpoint
# Rule: R004 — /v1/ prefix required
import os
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_db, verify_token
from backend.auth.types import AuthenticatedUser
from backend.db.models.document import Document
from backend.db.models.embedding import Embedding

MAX_DOC_CHARS = int(os.getenv("MAX_DOC_CHARS", "100000"))
_LANG_RE = re.compile(r"^[a-z]{2}$")

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class DocumentUpload(BaseModel):
    title: str = Field(..., max_length=500)
    content: str
    lang: str
    user_group_id: int | None = None


class DocumentItem(BaseModel):
    id: str
    title: str
    lang: str
    user_group_id: int | None
    status: str
    created_at: str
    chunk_count: int


# ---------------------------------------------------------------------------
# Background pipeline stub (wired up progressively by S002–S004)
# ---------------------------------------------------------------------------

async def ingest_pipeline(doc_id: uuid.UUID, content: str) -> None:
    """Ingestion pipeline: chunk → embed → BM25 index. (S002–S004)

    S002: chunk_document splits content into overlapping Chunks.
    S003: OllamaEmbedder.batch_embed generates vectors; insert_embeddings persists them.
    S004: update_fts updates content_fts + sets status='ready'.
    On EmbedderError: doc.status='failed', no partial insert.
    """
    import logging
    from backend.db.session import async_session_factory
    from backend.rag.chunker import chunk_document, _resolve_lang
    from backend.rag.embedder import OllamaEmbedder, EmbedderError, insert_embeddings
    from backend.rag.bm25_indexer import update_fts
    from backend.db.models.document import Document

    _logger = logging.getLogger(__name__)

    async with async_session_factory() as db:
        doc = await db.get(Document, doc_id)
        if doc is None:
            _logger.error("ingest_pipeline: doc %s not found", doc_id)
            return

        lang = _resolve_lang(content, doc.lang)
        chunks = chunk_document(content, lang, doc_id)
        if not chunks:
            doc.status = "failed"
            await db.commit()
            return

        embedder = OllamaEmbedder()
        try:
            vectors = await embedder.batch_embed(chunks)
            await insert_embeddings(chunks, vectors, doc, db)
        except EmbedderError as exc:
            _logger.error("ingest_pipeline: embedding failed for doc %s: %s", doc_id, exc)
            doc.status = "failed"
            await db.commit()
            return

        await update_fts(doc_id, chunks, db)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error(request_id: str, code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def _chunk_count_subquery():
    return (
        select(func.count())
        .where(Embedding.doc_id == Document.id)
        .correlate(Document)
        .scalar_subquery()
    )


# ---------------------------------------------------------------------------
# POST /v1/documents — upload & validate
# ---------------------------------------------------------------------------

@router.post("/v1/documents")
async def upload_document(
    body: DocumentUpload,
    background_tasks: BackgroundTasks,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    request_id = str(uuid.uuid4())

    # T002: auth_type write gate (D09)
    if user.auth_type != "api_key":
        return JSONResponse(
            status_code=403,
            content=_error(request_id, "FORBIDDEN", "Write access requires API-key authentication"),
        )

    # T003: input validation
    if not body.content or not body.content.strip():
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", "content must not be empty"),
        )
    if len(body.content) > MAX_DOC_CHARS:
        return JSONResponse(
            status_code=413,
            content=_error(request_id, "DOC_TOO_LARGE", f"content exceeds {MAX_DOC_CHARS} characters"),
        )
    if not _LANG_RE.match(body.lang):
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", f"lang '{body.lang}' is not a valid ISO 639-1 code"),
        )

    # T004: RBAC group membership check
    if body.user_group_id is not None and body.user_group_id not in user.user_group_ids:
        return JSONResponse(
            status_code=403,
            content=_error(request_id, "FORBIDDEN", "Caller does not belong to the specified user_group_id"),
        )

    # T005: INSERT document + dispatch background pipeline (D11: content NOT stored)
    doc = Document(
        title=body.title,
        lang=body.lang,
        user_group_id=body.user_group_id,
        status="processing",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(ingest_pipeline, doc.id, body.content)

    return JSONResponse(
        status_code=202,
        content={"doc_id": str(doc.id), "status": "processing"},
    )


# ---------------------------------------------------------------------------
# GET /v1/documents — paginated RBAC-filtered list
# ---------------------------------------------------------------------------

@router.get("/v1/documents")
async def list_documents(
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
) -> JSONResponse:
    request_id = str(uuid.uuid4())

    if limit > 100:
        return JSONResponse(
            status_code=422,
            content=_error(request_id, "INVALID_INPUT", "limit must not exceed 100"),
        )

    offset = (page - 1) * limit

    # R001: RBAC at WHERE clause — not Python post-filter
    rbac_stmt = text(
        "SELECT d.id, d.title, d.lang, d.user_group_id, d.status, d.created_at, "
        "(SELECT COUNT(*) FROM embeddings e WHERE e.doc_id = d.id) AS chunk_count "
        "FROM documents d "
        "WHERE (d.user_group_id = ANY(:group_ids) OR d.user_group_id IS NULL) "
        "ORDER BY d.created_at DESC "
        "LIMIT :limit OFFSET :offset"
    ).bindparams(group_ids=user.user_group_ids, limit=limit, offset=offset)

    count_stmt = text(
        "SELECT COUNT(*) FROM documents d "
        "WHERE (d.user_group_id = ANY(:group_ids) OR d.user_group_id IS NULL)"
    ).bindparams(group_ids=user.user_group_ids)

    rows = (await db.execute(rbac_stmt)).mappings().all()
    total = (await db.execute(count_stmt)).scalar()

    items = [
        {
            "id": str(r["id"]),
            "title": r["title"],
            "lang": r["lang"],
            "user_group_id": r["user_group_id"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
            "chunk_count": r["chunk_count"],
        }
        for r in rows
    ]
    return JSONResponse(content={"items": items, "total": total, "page": page, "limit": limit})


# ---------------------------------------------------------------------------
# GET /v1/documents/{id} — metadata + 404 (enumeration prevention)
# ---------------------------------------------------------------------------

@router.get("/v1/documents/{doc_id}")
async def get_document(
    doc_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    request_id = str(uuid.uuid4())

    # R001: RBAC in WHERE — returns 404 for both not-found AND unauthorized (AC3: no enumeration)
    stmt = text(
        "SELECT d.id, d.title, d.lang, d.user_group_id, d.status, d.created_at, "
        "(SELECT COUNT(*) FROM embeddings e WHERE e.doc_id = d.id) AS chunk_count "
        "FROM documents d "
        "WHERE d.id = :doc_id "
        "AND (d.user_group_id = ANY(:group_ids) OR d.user_group_id IS NULL)"
    ).bindparams(doc_id=doc_id, group_ids=user.user_group_ids)

    row = (await db.execute(stmt)).mappings().first()
    if row is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "Document not found"),
        )

    return JSONResponse(content={
        "id": str(row["id"]),
        "title": row["title"],
        "lang": row["lang"],
        "user_group_id": row["user_group_id"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
        "chunk_count": row["chunk_count"],
    })


# ---------------------------------------------------------------------------
# DELETE /v1/documents/{id} — 204 + 404
# ---------------------------------------------------------------------------

@router.delete("/v1/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(verify_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    request_id = str(uuid.uuid4())

    # R001: RBAC in WHERE clause — no fetch-then-delete (P004)
    stmt = text(
        "DELETE FROM documents "
        "WHERE id = :doc_id "
        "AND (user_group_id = ANY(:group_ids) OR user_group_id IS NULL) "
        "RETURNING id"
    ).bindparams(doc_id=doc_id, group_ids=user.user_group_ids)

    result = await db.execute(stmt)
    deleted = result.fetchone()
    if deleted is None:
        return JSONResponse(
            status_code=404,
            content=_error(request_id, "NOT_FOUND", "Document not found"),
        )

    await db.commit()
    return Response(status_code=204)

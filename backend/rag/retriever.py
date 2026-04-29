# Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S002
# Task: T001 — scaffold RetrievedDocument dataclass + retrieve() stub
# Task: T002 — _dense_search() pgvector RBAC WHERE clause
# Task: T003 — _bm25_search() tsvector RBAC WHERE clause
# Task: T004 — retrieve() hybrid merge + asyncio.wait_for timeout wrapper
# Task: S003-T003 — embed-model-migration: cosine operator <-> → <=> (HNSW vector_cosine_ops match, P003)
# Decision: D01 — user_group_id IS NULL = public document
# Decision: D02 — dense filter on embeddings, BM25 filter on documents
import asyncio
import os
import uuid
from dataclasses import dataclass

from sqlalchemy import bindparam, text

RAG_DENSE_WEIGHT = float(os.getenv("RAG_DENSE_WEIGHT", "0.7"))
RAG_BM25_WEIGHT = float(os.getenv("RAG_BM25_WEIGHT", "0.3"))


class QueryTimeoutError(Exception):
    """Raised when retrieval exceeds the 1800ms SLA (R007/P001)."""


@dataclass
class RetrievedDocument:
    doc_id: uuid.UUID
    chunk_index: int
    score: float
    user_group_id: int | None   # None = public document
    content: str | None = None
    # answer-citation S001-T004: enrichment fields from documents table (migration 007)
    # d.lang or "und" fallback: defensive — lang is NOT NULL in ORM but future-proofed per T001 pre-check
    title: str | None = None
    lang: str | None = None
    source_url: str | None = None


async def _dense_search(
    session,
    query_embedding: list[float],
    user_group_ids: list[int],
    top_k: int,
) -> list["RetrievedDocument"]:
    # Task: T002 — dense RBAC filter on embeddings.user_group_id (D02)
    # R001: WHERE clause applied BEFORE ORDER BY / LIMIT — never post-query Python filter
    # S001: text().bindparams() — zero f-string SQL interpolation
    # answer-citation S001-T005: INNER JOIN documents to SELECT title/lang/source_url
    # RBAC filter remains on embeddings.user_group_id (D02 — not documents.user_group_id)
    sql = text("""
        SELECT e.doc_id, e.chunk_index, e.user_group_id, e.text,
               d.title, d.lang, d.source_url,
               e.embedding <=> cast(:query_vec AS vector) AS distance
        FROM embeddings e
        INNER JOIN documents d ON d.id = e.doc_id
        WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)
        ORDER BY distance
        LIMIT :top_k
    """).bindparams(
        bindparam("query_vec", value=str(query_embedding)),
        bindparam("group_ids", value=user_group_ids),
        bindparam("top_k", value=top_k),
    )
    rows = await session.execute(sql)
    return [
        RetrievedDocument(
            doc_id=r.doc_id,
            chunk_index=r.chunk_index,
            score=1.0 - (r.distance / 2.0),  # cosine distance ∈ [0,2] → similarity ∈ [0,1]
            user_group_id=r.user_group_id,
            content=r.text,
            title=r.title,
            lang=r.lang or "und",  # defensive fallback — lang is NOT NULL in ORM (migration 007 T001)
            source_url=r.source_url,
        )
        for r in rows
    ]


async def _bm25_search(
    session,
    bm25_query: str,
    user_group_ids: list[int],
    top_k: int,
) -> list["RetrievedDocument"]:
    # Task: T003 — BM25 RBAC filter on documents.user_group_id (D02)
    # R001: WHERE clause applied BEFORE ORDER BY / LIMIT
    # S001: text().bindparams() — zero f-string SQL interpolation
    # answer-citation S001-T005: already queries documents d — add title/lang/source_url to SELECT
    sql = text("""
        SELECT d.id AS doc_id, 0 AS chunk_index, d.user_group_id,
               d.title, d.lang, d.source_url,
               ts_rank(d.content_fts, plainto_tsquery('simple', :query)) AS rank
        FROM documents d
        WHERE (d.user_group_id = ANY(:group_ids) OR d.user_group_id IS NULL)
          AND d.content_fts @@ plainto_tsquery('simple', :query)
        ORDER BY rank DESC
        LIMIT :top_k
    """).bindparams(
        bindparam("query", value=bm25_query),
        bindparam("group_ids", value=user_group_ids),
        bindparam("top_k", value=top_k),
    )
    rows = await session.execute(sql)
    return [
        RetrievedDocument(
            doc_id=r.doc_id,
            chunk_index=r.chunk_index,  # intentionally 0 — BM25 queries documents, not embeddings
            score=float(r.rank),
            user_group_id=r.user_group_id,
            title=r.title,
            lang=r.lang or "und",  # defensive fallback — lang is NOT NULL in ORM (migration 007 T001)
            source_url=r.source_url,
        )
        for r in rows
    ]


def _merge(
    dense: list[RetrievedDocument],
    bm25: list[RetrievedDocument],
    top_k: int,
) -> list[RetrievedDocument]:
    # Task: T004 — weighted score merge + dedup by doc_id (A004)
    scores: dict[uuid.UUID, float] = {}
    for doc in dense:
        scores[doc.doc_id] = scores.get(doc.doc_id, 0.0) + RAG_DENSE_WEIGHT * doc.score
    for doc in bm25:
        scores[doc.doc_id] = scores.get(doc.doc_id, 0.0) + RAG_BM25_WEIGHT * doc.score
    ranked = sorted(scores, key=scores.__getitem__, reverse=True)[:top_k]
    all_docs = {d.doc_id: d for d in dense + bm25}
    return [
        RetrievedDocument(**{**vars(all_docs[did]), "score": scores[did]})
        for did in ranked
    ]


async def retrieve(
    query_embedding: list[float],
    user_group_ids: list[int],   # [] = public-only mode
    top_k: int = 10,
    *,
    session,                     # AsyncSession — injected by caller
    bm25_query: str | None = None,
) -> list[RetrievedDocument]:
    # Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S002
    # Task: T004 — hybrid merge, concurrent gather, timeout wrapper
    # Decision: D02 — dense filter on embeddings, BM25 filter on documents

    async def _inner() -> list[RetrievedDocument]:
        if bm25_query:
            dense = await _dense_search(session, query_embedding, user_group_ids, top_k)
            bm25 = await _bm25_search(session, bm25_query, user_group_ids, top_k)
        else:
            dense = await _dense_search(session, query_embedding, user_group_ids, top_k)
            bm25 = []
        return _merge(dense, bm25, top_k)

    try:
        return await asyncio.wait_for(_inner(), timeout=1.8)
    except asyncio.TimeoutError:
        raise QueryTimeoutError("retrieval exceeded 1800ms SLA")

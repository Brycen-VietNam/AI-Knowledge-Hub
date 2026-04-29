# Spec: docs/embed-model-migration/spec/embed-model-migration.spec.md#S002
# Task: T002 — Pipeline-body unit tests (prefix routing, dim=1024, single commit)
# Task: T003 — Multilingual smoke test (JA/EN/VI/KO)
# Rule: P002 (batch ≥32, no per-doc loop), P004 (single commit), R002 (no PII in metadata)
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

# Stub OIDC env (mirrors tests/api/conftest.py) — required because importing
# backend.api.routes.documents transitively imports backend.auth.oidc.
os.environ.setdefault("OIDC_ISSUER", "https://test.example.com")
os.environ.setdefault("OIDC_AUDIENCE", "test-audience")
os.environ.setdefault("OIDC_JWKS_URI", "https://test.example.com/.well-known/jwks.json")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-key-for-unit-tests-only-32bytes!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-secret-key-for-unit-tests-32b!")

import pytest

from backend.api.routes.documents import ingest_pipeline
from backend.rag.chunker import Chunk


def _make_doc(lang: str = "en", user_group_id: int = 1):
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.lang = lang
    doc.user_group_id = user_group_id
    doc.status = "processing"
    return doc


def _patch_pipeline_deps(doc, chunks, vectors):
    """Patch async_session_factory + chunker + update_fts. Returns (db_mock, embedder_cls_mock)."""
    db = AsyncMock()
    db.add_all = MagicMock()
    db.commit = AsyncMock()
    db.get = AsyncMock(return_value=doc)

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=db)
    session_ctx.__aexit__ = AsyncMock(return_value=False)
    session_factory = MagicMock(return_value=session_ctx)

    embedder_instance = MagicMock()
    embedder_instance.batch_embed_passage = AsyncMock(return_value=vectors)
    embedder_instance.batch_embed = AsyncMock(side_effect=AssertionError("legacy batch_embed must not be called"))
    embedder_cls = MagicMock(return_value=embedder_instance)

    return db, embedder_instance, embedder_cls, session_factory, chunks


@pytest.mark.asyncio
async def test_pipeline_calls_batch_embed_passage():
    """ingest_pipeline must call batch_embed_passage, never legacy batch_embed (AC1)."""
    doc = _make_doc()
    chunks = [Chunk(doc_id=doc.id, chunk_index=i, text=f"hello {i}", lang="en") for i in range(3)]
    vectors = [[0.0] * 1024 for _ in chunks]
    _, embedder, embedder_cls, session_factory, _ = _patch_pipeline_deps(doc, chunks, vectors)

    with patch("backend.db.session.async_session_factory", session_factory), \
         patch("backend.rag.chunker.chunk_document", return_value=chunks), \
         patch("backend.rag.bm25_indexer.update_fts", new_callable=AsyncMock), \
         patch("backend.rag.embedder.OllamaEmbedder", embedder_cls):
        await ingest_pipeline(doc.id, "raw content")

    embedder.batch_embed_passage.assert_awaited_once()
    embedder.batch_embed.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_passes_raw_chunk_text():
    """Chunks forwarded to batch_embed_passage must NOT carry the 'passage: ' prefix (AC4 — prefix contract)."""
    doc = _make_doc()
    chunks = [Chunk(doc_id=doc.id, chunk_index=i, text=f"raw chunk {i}", lang="en") for i in range(3)]
    vectors = [[0.0] * 1024 for _ in chunks]
    _, embedder, embedder_cls, session_factory, _ = _patch_pipeline_deps(doc, chunks, vectors)

    with patch("backend.db.session.async_session_factory", session_factory), \
         patch("backend.rag.chunker.chunk_document", return_value=chunks), \
         patch("backend.rag.bm25_indexer.update_fts", new_callable=AsyncMock), \
         patch("backend.rag.embedder.OllamaEmbedder", embedder_cls):
        await ingest_pipeline(doc.id, "raw content")

    forwarded = embedder.batch_embed_passage.await_args.args[0]
    for c in forwarded:
        assert not c.text.startswith("passage: "), f"caller pre-prefixed: {c.text!r}"


@pytest.mark.asyncio
async def test_pipeline_stores_dim_1024_vectors():
    """Vectors persisted via insert_embeddings must have dim == 1024 (AC5)."""
    doc = _make_doc()
    chunks = [Chunk(doc_id=doc.id, chunk_index=i, text=f"chunk {i}", lang="en") for i in range(3)]
    vectors = [[0.0] * 1024 for _ in chunks]
    db, _, embedder_cls, session_factory, _ = _patch_pipeline_deps(doc, chunks, vectors)

    with patch("backend.db.session.async_session_factory", session_factory), \
         patch("backend.rag.chunker.chunk_document", return_value=chunks), \
         patch("backend.rag.bm25_indexer.update_fts", new_callable=AsyncMock), \
         patch("backend.rag.embedder.OllamaEmbedder", embedder_cls):
        await ingest_pipeline(doc.id, "raw content")

    db.add_all.assert_called_once()
    rows = db.add_all.call_args.args[0]
    assert len(rows) == 3
    for row in rows:
        assert len(row.embedding) == 1024


@pytest.mark.asyncio
async def test_pipeline_single_commit_no_per_doc_loop():
    """Exactly one db.add_all + one db.commit — no per-chunk DB call (P004, AC4)."""
    doc = _make_doc()
    chunks = [Chunk(doc_id=doc.id, chunk_index=i, text=f"chunk {i}", lang="en") for i in range(5)]
    vectors = [[0.0] * 1024 for _ in chunks]
    db, _, embedder_cls, session_factory, _ = _patch_pipeline_deps(doc, chunks, vectors)

    with patch("backend.db.session.async_session_factory", session_factory), \
         patch("backend.rag.chunker.chunk_document", return_value=chunks), \
         patch("backend.rag.bm25_indexer.update_fts", new_callable=AsyncMock), \
         patch("backend.rag.embedder.OllamaEmbedder", embedder_cls):
        await ingest_pipeline(doc.id, "raw content")

    assert db.add_all.call_count == 1
    assert db.commit.await_count == 1


# ---------------------------------------------------------------------------
# T003: Multilingual ingest smoke (JA/EN/VI/KO) — real chunker, mocked embedder
# ---------------------------------------------------------------------------

def _mecab_available() -> bool:
    try:
        import MeCab
        MeCab.Tagger()
        return True
    except Exception:
        return False


_MECAB_AVAILABLE = _mecab_available()


@pytest.mark.parametrize(
    "lang, content",
    [
        ("en", "The knowledge hub indexes internal documents for hybrid retrieval."),
        ("ja", "ナレッジハブは社内文書をハイブリッド検索のために索引化します。"),
        ("vi", "Knowledge Hub lập chỉ mục tài liệu nội bộ phục vụ tìm kiếm hỗn hợp."),
        ("ko", "지식 허브는 하이브리드 검색을 위해 내부 문서를 색인화합니다."),
    ],
)
@pytest.mark.asyncio
async def test_pipeline_multilingual_lang_populated(lang: str, content: str):
    """Real chunker → Embedding.lang matches source doc lang for ja/en/vi/ko (AC3, R002)."""
    if lang == "ja" and not _MECAB_AVAILABLE:
        pytest.skip("MeCab system binary not installed (see Dockerfile)")
    doc = _make_doc(lang=lang, user_group_id=7)
    # Use real chunker — only embedder + session + bm25 are mocked.
    fake_vector = [0.0] * 1024

    db = AsyncMock()
    db.add_all = MagicMock()
    db.commit = AsyncMock()
    db.get = AsyncMock(return_value=doc)
    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=db)
    session_ctx.__aexit__ = AsyncMock(return_value=False)
    session_factory = MagicMock(return_value=session_ctx)

    embedder_instance = MagicMock()

    async def fake_batch(chunks):  # noqa: S7503 — async required: side_effect for AsyncMock
        return [fake_vector for _ in chunks]

    embedder_instance.batch_embed_passage = AsyncMock(side_effect=fake_batch)
    embedder_cls = MagicMock(return_value=embedder_instance)

    with patch("backend.db.session.async_session_factory", session_factory), \
         patch("backend.rag.bm25_indexer.update_fts", new_callable=AsyncMock), \
         patch("backend.rag.embedder.OllamaEmbedder", embedder_cls):
        await ingest_pipeline(doc.id, content)

    db.add_all.assert_called_once()
    rows = db.add_all.call_args.args[0]
    assert len(rows) >= 1, f"chunker yielded no chunks for lang={lang}"
    for row in rows:
        assert row.lang == lang, f"row.lang={row.lang!r} != source doc lang={lang!r}"
        assert row.user_group_id == 7   # R002: flows from doc, never from chunk
        assert row.lang is not None     # AC3 explicit

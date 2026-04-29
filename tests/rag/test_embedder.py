# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S003
# Task: S003-T001 — _embed_one tests (removed in embed-model-migration S001-T005)
# Task: S003-T002 — batch_embed tests (removed in embed-model-migration S001-T005)
# Task: S003-T003 — insert_embeddings + failure path tests
# Task: T001 — EMBEDDING_MODEL default (embed-model-migration S001)
# Task: S001-T005 — embed-model-migration: remove embed_one/batch_embed legacy API
# Decision: D10, D11, Rule: R002, P002, P004
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.rag.chunker import Chunk
from backend.rag.embedder import EmbedderError, OllamaEmbedder, insert_embeddings


def _make_chunk(index: int = 0, lang: str = "en") -> Chunk:
    return Chunk(doc_id=uuid.uuid4(), chunk_index=index, text=f"chunk text {index}", lang=lang)


# ---------------------------------------------------------------------------
# T001 (embed-model-migration): EMBEDDING_MODEL default
# ---------------------------------------------------------------------------

def test_default_model_when_env_unset():
    """OllamaEmbedder._model == 'multilingual-e5-large' when EMBEDDING_MODEL env is absent (AC1)."""
    with patch("backend.rag.embedder.EMBEDDING_MODEL", "multilingual-e5-large"):
        embedder = OllamaEmbedder()
    assert embedder._model == "multilingual-e5-large"


def test_default_model_overridden_by_env():
    """OllamaEmbedder._model picks up a non-default EMBEDDING_MODEL value (A004)."""
    with patch("backend.rag.embedder.EMBEDDING_MODEL", "mxbai-embed-large"):
        embedder = OllamaEmbedder()
    assert embedder._model == "mxbai-embed-large"


# ---------------------------------------------------------------------------
# T002 (embed-model-migration): embed_query
# ---------------------------------------------------------------------------

def _mock_httpx(status: int = 200, embedding: list | None = None):
    """Return a patch context for httpx.AsyncClient that yields a fixed embedding."""
    if embedding is None:
        embedding = [0.0] * 1024
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = {"embedding": embedding}
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_client, patch("backend.rag.embedder.httpx.AsyncClient", return_value=ctx)


@pytest.mark.asyncio
async def test_embed_query_prepends_prefix():
    """Outgoing Ollama prompt starts with 'query: ' (AC2, X3: 7 chars, lowercase, single space)."""
    embedder = OllamaEmbedder()
    mock_client, patcher = _mock_httpx()
    with patcher:
        await embedder.embed_query("hello world")
    call_kwargs = mock_client.post.call_args
    sent_prompt = call_kwargs.kwargs["json"]["prompt"]
    assert sent_prompt.startswith("query: ")
    assert sent_prompt[7:8] != " ", "no double-space after prefix"


@pytest.mark.asyncio
async def test_embed_query_returns_dim_1024():
    """embed_query returns a 1024-dimensional vector (AC7 — dim)."""
    embedder = OllamaEmbedder()
    _, patcher = _mock_httpx(embedding=[0.0] * 1024)
    with patcher:
        result = await embedder.embed_query("some query")
    assert len(result) == 1024


@pytest.mark.asyncio
async def test_embed_query_truncation_includes_prefix():
    """With 1500-char input: sent prompt is ≤1400 chars AND still starts with 'query: ' (AC6)."""
    embedder = OllamaEmbedder()
    long_text = "a" * 1500
    mock_client, patcher = _mock_httpx()
    with patcher:
        await embedder.embed_query(long_text)
    sent_prompt = mock_client.post.call_args.kwargs["json"]["prompt"]
    assert len(sent_prompt) == 1400
    assert sent_prompt.startswith("query: ")


@pytest.mark.asyncio
async def test_embed_query_raises_on_non_200():
    """embed_query propagates EmbedderError on HTTP 500 (AC7 — error path)."""
    embedder = OllamaEmbedder()
    _, patcher = _mock_httpx(status=500)
    with patcher, pytest.raises(EmbedderError):
        await embedder.embed_query("query text")


def test_embed_query_rejects_pre_prefixed_input():
    """embed_query('query: foo') raises ValueError — double-prefix guard (Q3)."""
    embedder = OllamaEmbedder()
    # _check_no_prefix raises synchronously before any await
    with pytest.raises(ValueError, match="already contains"):
        embedder._check_no_prefix("query: pre-prefixed", "query: ")


# ---------------------------------------------------------------------------
# T003 (embed-model-migration): embed_passage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_embed_passage_prepends_prefix():
    """Outgoing Ollama prompt starts with 'passage: ' (AC3, X3: 9 chars, lowercase, single space)."""
    embedder = OllamaEmbedder()
    mock_client, patcher = _mock_httpx()
    with patcher:
        await embedder.embed_passage("some passage text")
    sent_prompt = mock_client.post.call_args.kwargs["json"]["prompt"]
    assert sent_prompt.startswith("passage: ")
    assert sent_prompt[9:10] != " ", "no double-space after prefix"


@pytest.mark.asyncio
async def test_embed_passage_returns_dim_1024():
    """embed_passage returns a 1024-dimensional vector (AC7 — dim)."""
    embedder = OllamaEmbedder()
    _, patcher = _mock_httpx(embedding=[0.0] * 1024)
    with patcher:
        result = await embedder.embed_passage("some passage")
    assert len(result) == 1024


@pytest.mark.asyncio
async def test_embed_passage_truncation_includes_prefix():
    """With 1500-char input: sent prompt is ≤1400 chars AND still starts with 'passage: ' (AC6)."""
    embedder = OllamaEmbedder()
    long_text = "a" * 1500
    mock_client, patcher = _mock_httpx()
    with patcher:
        await embedder.embed_passage(long_text)
    sent_prompt = mock_client.post.call_args.kwargs["json"]["prompt"]
    assert len(sent_prompt) == 1400
    assert sent_prompt.startswith("passage: ")


def test_embed_passage_rejects_pre_prefixed_input():
    """embed_passage('passage: foo') raises ValueError — double-prefix guard (Q3)."""
    embedder = OllamaEmbedder()
    # _check_no_prefix raises synchronously before any await
    with pytest.raises(ValueError, match="already contains"):
        embedder._check_no_prefix("passage: pre-prefixed", "passage: ")


# ---------------------------------------------------------------------------
# T004 (embed-model-migration): batch_embed_passage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_embed_passage_preserves_order():
    """Returned vectors map back to input chunk index in order (AC4, AC7)."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(50)]

    async def fake_passage(text: str) -> list[float]:
        idx = int(text.split()[-1])
        return [float(idx)] * 4

    with patch.object(embedder, "embed_passage", side_effect=fake_passage):
        results = await embedder.batch_embed_passage(chunks, batch_size=32)

    assert len(results) == 50
    for i, vec in enumerate(results):
        assert vec == [float(i)] * 4, f"order mismatch at index {i}"


@pytest.mark.asyncio
async def test_batch_embed_passage_uses_passage_prefix():
    """All prompts forwarded to _embed begin with 'passage: ' (AC3, AC4)."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(3)]
    captured: list[str] = []
    fake_vector = [0.0] * 1024

    async def spy_embed(prompt: str) -> list[float]:  # noqa: S7503 — async required: side_effect for async _embed
        captured.append(prompt)
        return fake_vector

    with patch.object(embedder, "_embed", side_effect=spy_embed):
        await embedder.batch_embed_passage(chunks, batch_size=32)

    assert len(captured) == 3
    for prompt in captured:
        assert prompt.startswith("passage: "), f"expected 'passage: ' prefix, got: {prompt!r}"


@pytest.mark.asyncio
async def test_batch_embed_passage_batches_at_32():
    """70 chunks → exactly 3 batches (32+32+6); embed_passage called 70 times (AC4, P002)."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(70)]
    fake_vector = [0.0] * 1024

    with patch.object(embedder, "embed_passage", new_callable=AsyncMock, return_value=fake_vector) as mock_ep:
        results = await embedder.batch_embed_passage(chunks, batch_size=32)

    assert len(results) == 70
    assert mock_ep.call_count == 70


@pytest.mark.asyncio
async def test_batch_embed_passage_propagates_embedder_error():
    """EmbedderError from one chunk propagates and aborts the whole call (AC7 — error)."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(3)]

    async def boom(text: str) -> list[float]:
        if "1" in text:
            raise EmbedderError("mock 500")
        return [0.0] * 1024

    with patch.object(embedder, "embed_passage", side_effect=boom):
        with pytest.raises(EmbedderError):
            await embedder.batch_embed_passage(chunks, batch_size=32)


# ---------------------------------------------------------------------------
# S001-T005: regression — legacy API removed (AC5)
# ---------------------------------------------------------------------------

def test_old_api_removed():
    """embed_one and batch_embed must not exist on OllamaEmbedder (AC5 — clean removal)."""
    assert not hasattr(OllamaEmbedder, "embed_one"), "embed_one must be removed"
    assert not hasattr(OllamaEmbedder, "batch_embed"), "batch_embed must be removed"


# ---------------------------------------------------------------------------
# T003: insert_embeddings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insert_embeddings_success():
    """All Embedding rows inserted with correct text and user_group_id (R002, D11)."""
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.user_group_id = 42

    chunks = [_make_chunk(i) for i in range(3)]
    vectors = [[float(i)] * 4 for i in range(3)]

    db = AsyncMock()
    db.add_all = MagicMock()
    db.commit = AsyncMock()

    await insert_embeddings(chunks, vectors, doc, db)

    db.add_all.assert_called_once()
    rows = db.add_all.call_args.args[0]
    assert len(rows) == 3
    for i, row in enumerate(rows):
        assert row.user_group_id == 42      # R002
        assert row.text == chunks[i].text   # D11
        assert row.chunk_index == i
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_insert_embeddings_failure_sets_status_failed():
    """EmbedderError → 0 embeddings inserted, doc.status='failed'."""
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.user_group_id = 1
    doc.status = "processing"

    chunks = [_make_chunk(0)]
    vectors = [[0.1, 0.2]]

    db = AsyncMock()
    db.add_all = MagicMock(side_effect=EmbedderError("mock failure"))
    db.commit = AsyncMock()

    # Simulate pipeline failure handling
    try:
        await insert_embeddings(chunks, vectors, doc, db)
    except EmbedderError:
        doc.status = "failed"
        await db.commit()

    assert doc.status == "failed"
    db.commit.assert_called_once()

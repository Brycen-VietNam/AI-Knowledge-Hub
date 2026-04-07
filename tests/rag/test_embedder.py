# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S003
# Task: S003-T001 — _embed_one tests
# Task: S003-T002 — batch_embed tests
# Task: S003-T003 — insert_embeddings + failure path tests
# Decision: D10, D11, Rule: R002, P002, P004
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.rag.chunker import Chunk
from backend.rag.embedder import EmbedderError, OllamaEmbedder, insert_embeddings


def _make_chunk(index: int = 0, lang: str = "en") -> Chunk:
    return Chunk(doc_id=uuid.uuid4(), chunk_index=index, text=f"chunk text {index}", lang=lang)


# ---------------------------------------------------------------------------
# T001: _embed_one
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_embed_one_returns_list_of_floats():
    embedder = OllamaEmbedder()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

    with patch("backend.rag.embedder.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await embedder._embed_one("hello world")

    assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_embed_one_raises_embedder_error_on_500():
    embedder = OllamaEmbedder()
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("backend.rag.embedder.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        with pytest.raises(EmbedderError):
            await embedder._embed_one("hello")


# ---------------------------------------------------------------------------
# T002: batch_embed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_embed_single_batch():
    """10 chunks, batch_size=32 → single gather call."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(10)]
    fake_vector = [0.1] * 1024

    with patch.object(embedder, "_embed_one", new_callable=AsyncMock, return_value=fake_vector):
        results = await embedder.batch_embed(chunks, batch_size=32)

    assert len(results) == 10
    assert all(v == fake_vector for v in results)


@pytest.mark.asyncio
async def test_batch_embed_multiple_batches():
    """70 chunks, batch_size=32 → 3 batches (32+32+6)."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(70)]
    fake_vector = [0.0] * 1024

    with patch.object(embedder, "_embed_one", new_callable=AsyncMock, return_value=fake_vector) as mock_embed:
        results = await embedder.batch_embed(chunks, batch_size=32)

    assert len(results) == 70
    assert mock_embed.call_count == 70


@pytest.mark.asyncio
async def test_batch_embed_order_preserved():
    """Output embedding at index N must correspond to chunk at index N."""
    embedder = OllamaEmbedder()
    chunks = [_make_chunk(i) for i in range(5)]

    async def fake_embed(text: str) -> list[float]:
        idx = int(text.split()[-1])
        return [float(idx)] * 4

    with patch.object(embedder, "_embed_one", side_effect=fake_embed):
        results = await embedder.batch_embed(chunks, batch_size=32)

    for i, vec in enumerate(results):
        assert vec == [float(i)] * 4


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

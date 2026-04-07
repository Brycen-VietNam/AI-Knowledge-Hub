# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S004
# Task: S004-T001 — tokenize_for_fts tests
# Task: S004-T002 — update_fts SQL tests
# Task: S004-T003 — status=ready + pipeline ordering tests
# Rule: R005, S001, P004
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.rag.bm25_indexer import tokenize_for_fts, update_fts
from backend.rag.chunker import Chunk


DOC_ID = uuid.uuid4()


def _make_chunk(text: str, lang: str = "en", index: int = 0) -> Chunk:
    return Chunk(doc_id=DOC_ID, chunk_index=index, text=text, lang=lang)


# ---------------------------------------------------------------------------
# T001: tokenize_for_fts
# ---------------------------------------------------------------------------

def test_tokenize_for_fts_japanese_uses_factory():
    """R005: Japanese must use TokenizerFactory."""
    mock_tokenizer = MagicMock()
    mock_tokenizer.tokenize.return_value = ["日本", "語"]
    with patch("backend.rag.bm25_indexer.TokenizerFactory.get", return_value=mock_tokenizer) as mock_get:
        result = tokenize_for_fts("日本語テスト", "ja")
    mock_get.assert_called_with("ja")
    assert result == "日本 語"


def test_tokenize_for_fts_english_uses_whitespace():
    result = tokenize_for_fts("hello world test", "en")
    assert result == "hello world test"


def test_tokenize_for_fts_unsupported_lang_no_exception(caplog):
    """AC3: UnsupportedLanguageError from factory → warning logged, raw text returned.
    Uses lang="ja" (CJK path) but factory raises UnsupportedLanguageError to simulate gap.
    """
    from backend.rag.tokenizers.exceptions import UnsupportedLanguageError
    with patch("backend.rag.bm25_indexer.TokenizerFactory.get", side_effect=UnsupportedLanguageError("ja")):
        with caplog.at_level("WARNING"):
            result = tokenize_for_fts("some text", "ja")
    assert result == "some text"
    assert any("Unsupported" in r.message for r in caplog.records)


def test_tokenize_for_fts_unknown_non_cjk_lang_uses_whitespace():
    """Non-CJK unknown lang (e.g. 'xx') → whitespace split, no exception, no warning."""
    result = tokenize_for_fts("hello world foo", "xx")
    assert result == "hello world foo"


def test_tokenize_for_fts_korean_uses_factory():
    mock_tokenizer = MagicMock()
    mock_tokenizer.tokenize.return_value = ["한국", "어"]
    with patch("backend.rag.bm25_indexer.TokenizerFactory.get", return_value=mock_tokenizer):
        result = tokenize_for_fts("한국어 텍스트", "ko")
    assert result == "한국 어"


# ---------------------------------------------------------------------------
# T002: update_fts SQL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_fts_executes_single_update():
    """P004: single UPDATE — not per-chunk; S001: parameterized query."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()

    chunks = [_make_chunk("hello world", "en", 0), _make_chunk("more text", "en", 1)]
    await update_fts(DOC_ID, chunks, db)

    db.execute.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_fts_joins_all_chunks():
    """All chunk tokens must be joined into single UPDATE statement."""
    db = AsyncMock()
    capture_calls = []
    db.execute = AsyncMock(side_effect=lambda stmt: capture_calls.append(stmt))
    db.commit = AsyncMock()

    chunks = [_make_chunk("hello world", "en", 0), _make_chunk("foo bar", "en", 1)]
    await update_fts(DOC_ID, chunks, db)

    assert len(capture_calls) == 1
    params = capture_calls[0]._bindparams
    assert "hello world" in params["tokens"].value
    assert "foo bar" in params["tokens"].value


@pytest.mark.asyncio
async def test_update_fts_sets_status_ready():
    """S004-T003: status='ready' set in same UPDATE as FTS."""
    db = AsyncMock()
    capture_calls = []
    db.execute = AsyncMock(side_effect=lambda stmt: capture_calls.append(stmt))
    db.commit = AsyncMock()

    await update_fts(DOC_ID, [_make_chunk("text", "en")], db)

    assert len(capture_calls) == 1
    executed_sql = str(capture_calls[0])
    assert "status" in executed_sql
    assert "ready" in executed_sql


@pytest.mark.asyncio
async def test_update_fts_uses_bindparams_not_fstring():
    """S001: must use .bindparams(), never f-string interpolation."""
    db = AsyncMock()
    capture_calls = []
    db.execute = AsyncMock(side_effect=lambda stmt: capture_calls.append(stmt))
    db.commit = AsyncMock()

    await update_fts(DOC_ID, [_make_chunk("content", "en")], db)

    assert len(capture_calls) == 1
    stmt = capture_calls[0]
    assert hasattr(stmt, "_bindparams")
    assert "tokens" in stmt._bindparams
    assert "doc_id" in stmt._bindparams

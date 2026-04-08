# Spec: docs/multilingual-rag-pipeline/spec/multilingual-rag-pipeline.spec.md#S002,S003
# Task: S002-T001 — Write test suite for tokenize_query()
# Task: S002-T002 — Implement tokenize_query() in query_processor.py
# Task: S003-T001 — Write test suite for embed_query()
# Task: S003-T002 — Implement embed_query() in query_processor.py

import pytest
from unittest.mock import patch, AsyncMock
from backend.rag.query_processor import tokenize_query, embed_query
from backend.rag.tokenizers.exceptions import UnsupportedLanguageError
from backend.rag.embedder import EmbedderError


# MeCab requires system binary (apt-get install mecab mecab-ipadic-utf8).
# Skip Japanese tests when MeCab dict is not installed (local dev on Windows / CI without Docker).
def _mecab_available() -> bool:
    try:
        import MeCab
        MeCab.Tagger()
        return True
    except Exception:
        return False


_MECAB_AVAILABLE = _mecab_available()
skip_no_mecab = pytest.mark.skipif(not _MECAB_AVAILABLE, reason="MeCab system binary not installed (see Dockerfile)")


@skip_no_mecab
def test_tokenize_query_japanese():
    """Verify tokenize_query() returns space-separated tokens for Japanese text."""
    text = "こんにちは世界"
    result = tokenize_query(text, "ja")

    assert isinstance(result, str), "Result must be string"
    assert len(result) > 0, "Result must not be empty"
    tokens = result.split(" ")
    assert len(tokens) > 0, "Must produce at least one token"
    # Verify tokens are non-empty strings
    assert all(token for token in tokens), "All tokens must be non-empty"


def test_tokenize_query_vietnamese():
    """Verify tokenize_query() returns space-separated tokens for Vietnamese text."""
    text = "Xin chào thế giới"
    result = tokenize_query(text, "vi")

    assert isinstance(result, str), "Result must be string"
    assert len(result) > 0, "Result must not be empty"
    tokens = result.split(" ")
    assert len(tokens) > 0, "Must produce at least one token"
    assert all(token for token in tokens), "All tokens must be non-empty"


def test_tokenize_query_english():
    """Verify tokenize_query() returns space-separated tokens for English text."""
    text = "Hello world"
    result = tokenize_query(text, "en")

    assert isinstance(result, str), "Result must be string"
    assert len(result) > 0, "Result must not be empty"
    tokens = result.split(" ")
    assert len(tokens) > 0, "Must produce at least one token"
    assert all(token for token in tokens), "All tokens must be non-empty"


def test_tokenize_query_korean():
    """Verify tokenize_query() returns space-separated tokens for Korean text."""
    text = "안녕하세요"
    result = tokenize_query(text, "ko")

    assert isinstance(result, str), "Result must be string"
    assert len(result) > 0, "Result must not be empty"
    tokens = result.split(" ")
    assert len(tokens) > 0, "Must produce at least one token"
    assert all(token for token in tokens), "All tokens must be non-empty"


def test_tokenize_query_unsupported_lang():
    """Verify tokenize_query() raises UnsupportedLanguageError for unknown language codes."""
    with pytest.raises(UnsupportedLanguageError):
        tokenize_query("hello", "fr")


def test_tokenize_query_unsupported_lang_german():
    """Verify tokenize_query() raises UnsupportedLanguageError for German (unsupported)."""
    with pytest.raises(UnsupportedLanguageError):
        tokenize_query("guten tag", "de")


def test_tokenize_query_error_propagates():
    """Verify UnsupportedLanguageError message propagates correctly."""
    with pytest.raises(UnsupportedLanguageError, match="Unsupported language"):
        tokenize_query("hello", "es")


# ============================================================================
# S003: Query Embedding Tests
# ============================================================================


@patch('backend.rag.query_processor._embedder')
async def test_embed_query_returns_vector(mock_embedder):
    """Verify embed_query() returns list[float] of expected shape."""
    # Setup mock to return a 768-dim vector
    mock_embedder._embed_one = AsyncMock(return_value=[0.1, 0.2, 0.3] * 256)

    result = await embed_query("hello world")

    assert isinstance(result, list), "Result must be list"
    assert len(result) == 768, f"Expected 768-dim vector, got {len(result)}"
    assert all(isinstance(x, float) for x in result), "All elements must be floats"
    mock_embedder._embed_one.assert_called_once_with("hello world")


@patch('backend.rag.query_processor._embedder')
async def test_embed_query_embedder_error_propagates(mock_embedder):
    """Verify EmbedderError from embedder is NOT caught — propagates to caller."""
    # Setup mock to raise error
    mock_embedder._embed_one = AsyncMock(side_effect=EmbedderError("Ollama API down"))

    with pytest.raises(EmbedderError, match="Ollama API down"):
        await embed_query("hello world")

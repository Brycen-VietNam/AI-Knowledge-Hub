# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S002
# Task: S002-T001 — lang resolution tests
# Task: S002-T002 — chunking tests
# Task: S002-T003 — empty chunk discard tests
import uuid
from unittest.mock import MagicMock, patch

import pytest

from backend.rag.chunker import Chunk, _resolve_lang, chunk_document


DOC_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# T001: lang resolution
# ---------------------------------------------------------------------------

def test_provided_lang_returned_as_is():
    """If lang is provided, detect_language must NOT be called."""
    with patch("backend.rag.chunker.detect_language") as mock_detect:
        result = _resolve_lang("Some content", "ja")
    assert result == "ja"
    mock_detect.assert_not_called()


def test_none_lang_triggers_detection():
    """If lang is None, detect_language must be called."""
    with patch("backend.rag.chunker.detect_language", return_value="en") as mock_detect:
        result = _resolve_lang("Hello world this is English text", None)
    assert result == "en"
    mock_detect.assert_called_once()


def test_empty_lang_triggers_detection():
    """Empty string lang triggers detection."""
    with patch("backend.rag.chunker.detect_language", return_value="ja") as mock_detect:
        result = _resolve_lang("日本語テキスト", "")
    assert result == "ja"
    mock_detect.assert_called_once()


def test_detection_error_falls_back_to_en():
    """LanguageDetectionError → fallback to 'en', no exception propagated."""
    from backend.rag.tokenizers.exceptions import LanguageDetectionError
    with patch("backend.rag.chunker.detect_language", side_effect=LanguageDetectionError("short")):
        result = _resolve_lang("hi", None)
    assert result == "en"


# ---------------------------------------------------------------------------
# T002: chunk_document
# ---------------------------------------------------------------------------

def test_english_text_chunks_under_chunk_size():
    words = ["word"] * 600
    content = " ".join(words)
    with patch("backend.rag.chunker.CHUNK_SIZE", 512), patch("backend.rag.chunker.CHUNK_OVERLAP", 50):
        chunks = chunk_document(content, "en", DOC_ID)
    assert all(len(c.text.split()) <= 512 for c in chunks)
    assert len(chunks) > 1


def test_chunk_index_is_sequential():
    content = " ".join(["word"] * 600)
    chunks = chunk_document(content, "en", DOC_ID)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i


def test_cjk_uses_tokenizer_factory():
    """For Japanese text, TokenizerFactory.get must be called (R005)."""
    mock_tokenizer = MagicMock()
    mock_tokenizer.tokenize.return_value = ["日本", "語", "テスト"] * 200
    with patch("backend.rag.chunker.TokenizerFactory.get", return_value=mock_tokenizer) as mock_get:
        chunks = chunk_document("日本語テスト" * 100, "ja", DOC_ID)
    mock_get.assert_called_with("ja")


def test_chunk_overlap_between_consecutive_chunks():
    """Consecutive chunks should share approximately CHUNK_OVERLAP tokens."""
    words = [f"w{i}" for i in range(600)]
    content = " ".join(words)
    with patch("backend.rag.chunker.CHUNK_SIZE", 100), patch("backend.rag.chunker.CHUNK_OVERLAP", 20):
        chunks = chunk_document(content, "en", DOC_ID)
    assert len(chunks) >= 2
    # Last words of chunk 0 should appear at start of chunk 1
    end_of_first = set(chunks[0].text.split()[-20:])
    start_of_second = set(chunks[1].text.split()[:20])
    assert len(end_of_first & start_of_second) > 0


def test_doc_id_preserved_in_chunks():
    chunks = chunk_document("Hello world test content", "en", DOC_ID)
    assert all(c.doc_id == DOC_ID for c in chunks)


def test_lang_preserved_in_chunks():
    chunks = chunk_document("Hello world test content repeated many times " * 20, "en", DOC_ID)
    assert all(c.lang == "en" for c in chunks)


# ---------------------------------------------------------------------------
# T003: empty chunk discard
# ---------------------------------------------------------------------------

def test_empty_chunks_discarded():
    """Chunks with only whitespace must be silently discarded."""
    content = "real content here " + "   " * 10 + " more real content"
    chunks = chunk_document(content, "en", DOC_ID)
    assert all(c.text.strip() != "" for c in chunks)


def test_all_whitespace_content_returns_empty_list():
    """Content that is entirely whitespace returns empty list, no exception."""
    chunks = chunk_document("   \n\t  ", "en", DOC_ID)
    assert chunks == []


def test_empty_content_returns_empty_list():
    chunks = chunk_document("", "en", DOC_ID)
    assert chunks == []

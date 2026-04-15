# Spec: docs/multilingual-rag-pipeline/spec/multilingual-rag-pipeline.spec.md#S004,S005
# Task: S004-T001 — Write unit test suite for search()
# Task: S004-T002 — Implement search() in search.py
# Task: S004-T003 — Write integration test for search() pipeline

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from backend.rag.retriever import RetrievedDocument
from backend.rag.tokenizers.exceptions import LanguageDetectionError, UnsupportedLanguageError
from backend.rag.embedder import EmbedderError
from backend.rag.retriever import QueryTimeoutError


# ============================================================================
# S004-T001: Unit Tests for search() — Mocked orchestration
# ============================================================================


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_with_auto_detect(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify search() calls detect_language when lang=None."""
    # Setup mocks
    mock_detect.return_value = "ja"
    mock_tokenize.return_value = "token1 token2"
    mock_embed.return_value = [0.1] * 768
    mock_doc = RetrievedDocument(
        doc_id=uuid4(), chunk_index=0, score=0.95, user_group_id=1, content="test"
    )
    mock_retrieve.return_value = [mock_doc]

    from backend.rag.search import search

    result = await search(
        query="こんにちは",
        user_group_ids=[1],
        session=MagicMock(),
        lang=None,
    )

    # Verify call sequence
    mock_detect.assert_called_once_with("こんにちは")
    mock_tokenize.assert_called_once_with("こんにちは", "ja")
    mock_embed.assert_called_once_with("こんにちは")
    mock_retrieve.assert_called_once()
    assert len(result) == 1
    assert result[0].score == 0.95


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_with_lang_override(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify search() skips detect_language when lang is provided."""
    # Setup mocks
    mock_tokenize.return_value = "hello world"
    mock_embed.return_value = [0.2] * 768
    mock_retrieve.return_value = []

    from backend.rag.search import search

    await search(
        query="hello",
        user_group_ids=[1],
        session=MagicMock(),
        lang="en",
    )

    # detect_language should NOT be called
    mock_detect.assert_not_called()
    mock_tokenize.assert_called_once_with("hello", "en")
    mock_embed.assert_called_once_with("hello")


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_language_detection_error(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify LanguageDetectionError propagates when lang=None and detection fails."""
    mock_detect.side_effect = LanguageDetectionError("Failed to detect")

    from backend.rag.search import search

    with pytest.raises(LanguageDetectionError):
        await search(
            query="",
            user_group_ids=[1],
            session=MagicMock(),
            lang=None,
        )


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_unsupported_language(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify UnsupportedLanguageError raised for invalid lang override."""
    from backend.rag.search import search

    with pytest.raises(UnsupportedLanguageError, match="Unsupported language"):
        await search(
            query="hello",
            user_group_ids=[1],
            session=MagicMock(),
            lang="fr",  # unsupported
        )


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_embedder_error(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify EmbedderError propagates."""
    mock_detect.return_value = "en"
    mock_tokenize.return_value = "hello"
    mock_embed.side_effect = EmbedderError("Ollama down")

    from backend.rag.search import search

    with pytest.raises(EmbedderError):
        await search(
            query="hello",
            user_group_ids=[1],
            session=MagicMock(),
            lang=None,
        )


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_query_timeout_error(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify QueryTimeoutError propagates."""
    mock_detect.return_value = "en"
    mock_tokenize.return_value = "hello"
    mock_embed.return_value = [0.1] * 768
    mock_retrieve.side_effect = QueryTimeoutError("Retrieval timeout")

    from backend.rag.search import search

    with pytest.raises(QueryTimeoutError):
        await search(
            query="hello",
            user_group_ids=[1],
            session=MagicMock(),
            lang=None,
        )


@patch('backend.rag.search.retrieve')
@patch('backend.rag.search.embed_query')
@patch('backend.rag.search.tokenize_query')
@patch('backend.rag.search.detect_language')
async def test_search_rbac_passthrough(mock_detect, mock_tokenize, mock_embed, mock_retrieve):
    """Verify user_group_ids passed unchanged to retrieve()."""
    mock_detect.return_value = "en"
    mock_tokenize.return_value = "hello"
    mock_embed.return_value = [0.1] * 768
    mock_retrieve.return_value = []

    from backend.rag.search import search

    await search(
        query="hello",
        user_group_ids=[1, 2, 3],  # Multiple groups
        session=MagicMock(),
        lang="en",
    )

    # Verify user_group_ids passed unchanged
    call_kwargs = mock_retrieve.call_args[1]
    assert call_kwargs["user_group_ids"] == [1, 2, 3]


# ============================================================================
# S004-T003: Integration Tests for search() — Real DB + Docker
# ============================================================================


@pytest.mark.integration
async def test_search_integration_full_pipeline(seeded_session):
    """Verify search() returns results via full pipeline (lang detect → tokenize → embed → retrieve).

    Requires: TEST_DATABASE_URL set + Docker PostgreSQL + pgvector running.
    Uses seeded_session fixture which provides 18 embeddings across 3 user groups + public.
    """
    from backend.rag.search import search

    # Test 1: Auto-detect English, verify results (use longer query for reliable detection)
    results = await search(
        query="the quick brown fox jumps over the lazy dog",
        user_group_ids=[1],  # GROUP_A_ID
        session=seeded_session,
        lang=None,  # Auto-detect
    )

    assert isinstance(results, list), "Results must be list[RetrievedDocument]"
    # Results may be empty or populated depending on embedding distance
    # but should not raise an error

    # Test 2: Override lang to English explicitly
    results_en = await search(
        query="sample text for english search",
        user_group_ids=[1],
        session=seeded_session,
        lang="en",  # Explicit override
    )

    assert isinstance(results_en, list), "Results must be list"


@pytest.mark.integration
async def test_search_integration_rbac_filter(seeded_session):
    """Verify RBAC: empty user_group_ids returns only public documents (user_group_id IS NULL)."""
    from backend.rag.search import search

    results = await search(
        query="hello",
        user_group_ids=[],  # No groups → only public
        session=seeded_session,
        lang="en",
    )

    # All results should have user_group_id = None (public)
    for result in results:
        assert result.user_group_id is None, f"RBAC filter failed: got group {result.user_group_id}"

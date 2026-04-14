# Spec: docs/multilingual-rag-pipeline/spec/multilingual-rag-pipeline.spec.md#S004
# Task: S004-T002 — Implement search() in search.py
# Decision: D4 (2026-04-08) — lang: str | None = None (None=auto-detect, override=validate)

from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.query_processor import tokenize_query, embed_query
from backend.rag.retriever import retrieve, RetrievedDocument
from backend.rag.tokenizers.detection import detect_language
from backend.rag.tokenizers.exceptions import LanguageDetectionError, UnsupportedLanguageError
from backend.rag.embedder import EmbedderError
from backend.rag.retriever import QueryTimeoutError

# Supported languages (must match TokenizerFactory registry)
_SUPPORTED = {"ja", "en", "vi", "ko", "zh"}


async def search(
    query: str,
    user_group_ids: list[int],
    session: AsyncSession,
    top_k: int = 10,
    lang: str | None = None,
) -> list[RetrievedDocument]:
    """Unified RAG search orchestration.

    Detects language (if not provided) → tokenizes → embeds → retrieves.
    Propagates all errors: LanguageDetectionError, UnsupportedLanguageError,
    EmbedderError, QueryTimeoutError.

    Args:
        query: Raw user query text
        user_group_ids: RBAC user groups (from token) — passed unchanged to retrieve()
        session: AsyncSession for database access
        top_k: Max results to return (default 10)
        lang: Override language code. None = auto-detect. If provided, must be in _SUPPORTED.

    Returns:
        list[RetrievedDocument] ranked by hybrid score (0.7*dense + 0.3*BM25)

    Raises:
        LanguageDetectionError: If lang=None and detection fails
        UnsupportedLanguageError: If lang not in _SUPPORTED
        EmbedderError: If embedding API fails
        QueryTimeoutError: If retrieval exceeds SLA (1800ms)
    """
    # Step 1: Detect or validate language
    if lang is None:
        lang = detect_language(query)  # Raises LanguageDetectionError on failure
    else:
        if lang not in _SUPPORTED:
            raise UnsupportedLanguageError(f"Unsupported language: {lang!r}")

    # Step 2: Tokenize for BM25
    bm25_query = tokenize_query(query, lang)  # Raises UnsupportedLanguageError if invalid

    # Step 3: Embed for dense search
    query_embedding = await embed_query(query)  # Raises EmbedderError on failure

    # Step 4: Hybrid retrieval with RBAC
    results = await retrieve(
        query_embedding=query_embedding,
        bm25_query=bm25_query,
        user_group_ids=user_group_ids,
        session=session,
        top_k=top_k,
    )  # Raises QueryTimeoutError on timeout

    return results

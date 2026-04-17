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
) -> tuple[list[RetrievedDocument], str]:
    """Unified RAG search orchestration.

    Always detects query language (best effort) → tokenizes → embeds → retrieves.
    Propagates all errors: LanguageDetectionError, UnsupportedLanguageError,
    EmbedderError, QueryTimeoutError.

    Args:
        query: Raw user query text
        user_group_ids: RBAC user groups (from token) — passed unchanged to retrieve()
        session: AsyncSession for database access
        top_k: Max results to return (default 10)
        lang: UI language preference fallback. Priority: detected query lang > UI lang preference.

    Returns:
        tuple of (list[RetrievedDocument] ranked by hybrid score, detected_lang: str)
        detected_lang is the query language (detected if possible, else UI lang, else 'en')

    Raises:
        UnsupportedLanguageError: If detected/provided lang not in _SUPPORTED
        EmbedderError: If embedding API fails
        QueryTimeoutError: If retrieval exceeds SLA (1800ms)
    """
    # Step 1: Detect query language first (priority), fallback to UI lang pref
    detected_lang = None
    try:
        detected_lang = detect_language(query)
    except Exception:
        # Detection failed — use UI language preference as fallback
        detected_lang = lang or "en"

    # Determine effective language: detected > UI preference > default "en"
    effective_lang = detected_lang or lang or "en"

    # Validate the effective language is supported
    if effective_lang not in _SUPPORTED:
        raise UnsupportedLanguageError(f"Unsupported language: {effective_lang!r}")

    # Step 2: Tokenize for BM25 using effective language
    bm25_query = tokenize_query(query, effective_lang)

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

    return results, effective_lang

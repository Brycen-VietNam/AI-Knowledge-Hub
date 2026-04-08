# Spec: docs/multilingual-rag-pipeline/spec/multilingual-rag-pipeline.spec.md#S002,S003
# Task: S002-T002 — Implement tokenize_query() in query_processor.py
# Task: S003-T002 — Implement embed_query() in query_processor.py
# Decision: D2 (2026-04-08) — Use TokenizerFactory.get(lang) for ALL langs

from backend.rag.tokenizers.factory import TokenizerFactory
from backend.rag.tokenizers.exceptions import UnsupportedLanguageError
from backend.rag.embedder import OllamaEmbedder, EmbedderError

# Module-level singleton embedder (initialized once per module import)
_embedder = OllamaEmbedder()


def tokenize_query(text: str, lang: str) -> str:
    """Tokenize query text for BM25 search using language-aware tokenizer.

    Delegates to TokenizerFactory to obtain the correct tokenizer for the given
    language, then returns space-separated tokens. Supports: ja, ko, zh, vi, en.

    Args:
        text: Raw query text to tokenize
        lang: Language code (ja, ko, zh, vi, en)

    Returns:
        Space-separated token string (matches tokenize_for_fts() format)

    Raises:
        UnsupportedLanguageError: If lang is not in the supported set
    """
    tokenizer = TokenizerFactory.get(lang)  # Raises UnsupportedLanguageError if unsupported
    tokens = tokenizer.tokenize(text)
    return " ".join(tokens)


async def embed_query(text: str) -> list[float]:
    """Embed query text using OllamaEmbedder.

    Uses module-level singleton embedder to generate a dense vector for the query.

    Args:
        text: Query text to embed

    Returns:
        Dense vector (list of floats, typically 768-dim for multilingual-e5-large)

    Raises:
        EmbedderError: If Ollama API request fails or returns non-200 status
    """
    return await _embedder._embed_one(text)

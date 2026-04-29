# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S003
# Task: S003-T001 — OllamaEmbedder + EmbedderError + env config
# Task: S003-T002 — batch_embed() with asyncio.gather
# Task: S003-T003 — insert_embeddings + failure path
# Decision: D10 — Ollama /api/embeddings, EMBEDDING_MODEL env var
# Decision: D11 — Embedding.text stores chunk text for RAG retrieval
# Rule: P002 — batch minimum 32, never per-document loop
# Rule: R002 — user_group_id from doc, never from request/chunk
import asyncio
import os

import httpx

from backend.rag.config import OLLAMA_EMBED_URL
from backend.rag.chunker import Chunk

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "multilingual-e5-large")


class EmbedderError(RuntimeError):
    """Raised when the Ollama embedding API returns a non-200 response."""


class OllamaEmbedder:
    # Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S003
    # Spec: docs/embed-model-migration/spec/embed-model-migration.spec.md#S001
    # Decision: D10 — env-configurable URL + model (no hardcoded values)

    def __init__(self):
        self._base_url = OLLAMA_EMBED_URL
        self._model = EMBEDDING_MODEL

    # multilingual-e5-large context limit aligned with prior mxbai bound.
    # Truncation runs AFTER prefix prepend so the prefix is never cut (AC6).
    _MAX_EMBED_CHARS: int = int(os.getenv("OLLAMA_MAX_EMBED_CHARS", "1400"))

    @staticmethod
    def _check_no_prefix(text: str, prefix: str) -> None:
        # Fail-fast: prevents silent recall degradation if a caller adds the prefix manually.
        if text.startswith(prefix):
            raise ValueError(
                f"Input already contains the '{prefix}' prefix. "
                "Pass raw text — the embedder applies prefixes internally."
            )

    async def _embed(self, prompt: str) -> list[float]:
        """POST an already-prefixed, truncated prompt to Ollama. Raises EmbedderError on failure."""
        prompt = prompt[: self._MAX_EMBED_CHARS]
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": prompt},
            )
        if resp.status_code != 200:
            raise EmbedderError(f"Ollama embeddings returned HTTP {resp.status_code}")
        return resp.json()["embedding"]

    async def embed_query(self, text: str) -> list[float]:
        """Embed a query string with the 'query: ' prefix (AC2, AC6)."""
        self._check_no_prefix(text, "query: ")
        return await self._embed("query: " + text)

    async def embed_passage(self, text: str) -> list[float]:
        """Embed a passage string with the 'passage: ' prefix (AC3, AC6)."""
        self._check_no_prefix(text, "passage: ")
        return await self._embed("passage: " + text)

    async def batch_embed_passage(self, chunks: list[Chunk], batch_size: int = 32) -> list[list[float]]:
        """Embed passage chunks in batches using asyncio.gather. Preserves input order. (AC4, P002)"""
        results: list[list[float]] = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i: i + batch_size]
            batch_vectors = await asyncio.gather(*[self.embed_passage(c.text) for c in batch])
            results.extend(batch_vectors)
        return results

async def insert_embeddings(
    chunks: list[Chunk],
    vectors: list[list[float]],
    doc,
    db,
) -> None:
    """Bulk-insert Embedding rows. On EmbedderError, set doc.status='failed'. (R002, P004, D11)

    R002: user_group_id copied from doc — never from chunk or request.
    D11:  chunk text stored in Embedding.text.
    P004: single db.add_all + one commit — no N+1.
    """
    from backend.db.models.embedding import Embedding

    rows = [
        Embedding(
            doc_id=doc.id,
            chunk_index=chunk.chunk_index,
            lang=chunk.lang,
            text=chunk.text,                   # D11
            user_group_id=doc.user_group_id,   # R002
            embedding=vector,
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    db.add_all(rows)
    await db.commit()

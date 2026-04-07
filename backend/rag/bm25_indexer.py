# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S004
# Task: S004-T001 — bm25_indexer scaffold + tokenize_for_fts()
# Task: S004-T002 — update_fts() — single UPDATE with to_tsvector
# Task: S004-T003 — status=ready update + pipeline wire-up
# Decision: D08 — new file, owns content_fts write path; retriever owns read path
# Rule: R005 — CJK tokenization required; S001 — no SQL string interpolation
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.chunker import Chunk
from backend.rag.tokenizers.exceptions import UnsupportedLanguageError
from backend.rag.tokenizers.factory import TokenizerFactory

_logger = logging.getLogger(__name__)

_CJK_LANGS = {"ja", "ko", "zh", "vi"}


def tokenize_for_fts(text_content: str, lang: str) -> str:
    """Tokenize text for PostgreSQL FTS (to_tsvector input).

    CJK langs: use TokenizerFactory (R005).
    Latin/other: whitespace split.
    UnsupportedLanguageError: log warning, fall back to text (AC3).
    Returns space-separated token string for to_tsvector('simple', ...).
    """
    if lang in _CJK_LANGS:
        try:
            tokens = TokenizerFactory.get(lang).tokenize(text_content)
            return " ".join(tokens)
        except UnsupportedLanguageError:
            _logger.warning("Unsupported language %r for FTS tokenization — using raw text", lang)
            return text_content
    return " ".join(text_content.split())


async def update_fts(doc_id: uuid.UUID, chunks: list[Chunk], db: AsyncSession) -> None:
    """Update documents.content_fts and set status='ready' for doc_id.

    Joins all chunk tokens into a single string then runs one UPDATE.
    Uses text().bindparams() — no f-string interpolation (S001, P004).
    status='ready' set after FTS update in same call (S004-T003 ordering).
    """
    all_tokens = " ".join(
        tokenize_for_fts(chunk.text, chunk.lang)
        for chunk in chunks
    )

    await db.execute(
        text(
            "UPDATE documents SET content_fts = to_tsvector('simple', :tokens), "
            "status = 'ready' WHERE id = :doc_id"
        ).bindparams(tokens=all_tokens, doc_id=doc_id)
    )
    await db.commit()

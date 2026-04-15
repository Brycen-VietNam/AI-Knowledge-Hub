# Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S002
# Task: S002-T001 — Chunk dataclass + language detection wrapper
# Task: S002-T002 — Sliding window chunker (CJK-aware token counting)
# Task: S002-T003 — Empty chunk discard
# Decision: D02 — CHUNK_SIZE=512, CHUNK_OVERLAP=50, configurable via env
# Rule: R005 — CJK content must use language-aware tokenizer
import os
import uuid
from dataclasses import dataclass

from backend.rag.tokenizers.detection import detect_language
from backend.rag.tokenizers.exceptions import LanguageDetectionError
from backend.rag.tokenizers.factory import TokenizerFactory

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

_CJK_LANGS = {"ja", "ko", "zh", "vi"}


@dataclass
class Chunk:
    doc_id: uuid.UUID
    chunk_index: int
    text: str
    lang: str


def _resolve_lang(content: str, provided_lang: str | None) -> str:
    """Return provided_lang if given; otherwise detect from content.

    Falls back to "en" if detection raises LanguageDetectionError.
    """
    if provided_lang:
        return provided_lang
    try:
        return detect_language(content)
    except LanguageDetectionError:
        return "en"  # fallback for short/ambiguous text


def _tokenize(text: str, lang: str) -> list[str]:
    """Tokenize text using CJK tokenizer for CJK langs, whitespace split otherwise."""
    if lang in _CJK_LANGS:
        return TokenizerFactory.get(lang).tokenize(text)
    return text.split()


def chunk_document(content: str, lang: str, doc_id: uuid.UUID) -> list["Chunk"]:
    """Split content into overlapping chunks using sliding window.

    Token counting is language-aware: CJK langs use TokenizerFactory,
    latin/other uses whitespace split (R005, D02).
    Empty/whitespace-only chunks are discarded.
    """
    tokens = _tokenize(content, lang)
    if not tokens:
        return []

    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    chunks: list[Chunk] = []
    chunk_index = 0
    i = 0

    while i < len(tokens):
        window = tokens[i: i + CHUNK_SIZE]
        # Reconstruct text from tokens
        if lang in _CJK_LANGS:
            text = "".join(window)
        else:
            text = " ".join(window)

        if text.strip():
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_index=chunk_index,
                text=text,
                lang=lang,
            ))
            chunk_index += 1

        i += step

    return chunks

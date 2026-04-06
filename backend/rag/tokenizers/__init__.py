# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T004 — Public API exports
# Decision: D05 — lazy loading; backend imports deferred to avoid import-time failures
from .base import BaseTokenizer
from .exceptions import LanguageDetectionError, UnsupportedLanguageError
from .factory import TokenizerFactory
from .detection import detect_language

__all__ = [
    "BaseTokenizer",
    "JapaneseTokenizer",
    "KoreanTokenizer",
    "ChineseTokenizer",
    "VietnameseTokenizer",
    "WhitespaceTokenizer",
    "TokenizerFactory",
    "detect_language",
    "UnsupportedLanguageError",
    "LanguageDetectionError",
]


def __getattr__(name: str):
    """Lazy-load language backend classes to defer heavy imports (MeCab, kiwipiepy, etc.)."""
    if name == "JapaneseTokenizer":
        from .japanese import JapaneseTokenizer
        return JapaneseTokenizer
    if name == "KoreanTokenizer":
        from .korean import KoreanTokenizer
        return KoreanTokenizer
    if name == "ChineseTokenizer":
        from .chinese import ChineseTokenizer
        return ChineseTokenizer
    if name == "VietnameseTokenizer":
        from .vietnamese import VietnameseTokenizer
        return VietnameseTokenizer
    if name == "WhitespaceTokenizer":
        from .whitespace import WhitespaceTokenizer
        return WhitespaceTokenizer
    raise AttributeError(f"module 'backend.rag.tokenizers' has no attribute {name!r}")

# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: S002-T001 — TokenizerFactory with lazy loading
# Decision: D01 — TokenizerFactory.get(lang) pattern
# Decision: D05 — lazy loading; MeCab/kiwipiepy init is expensive
import threading

from .base import BaseTokenizer
from .exceptions import UnsupportedLanguageError


class TokenizerFactory:
    _registry: dict[str, BaseTokenizer] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, lang: str) -> BaseTokenizer:
        if lang in cls._registry:
            return cls._registry[lang]
        with cls._lock:
            if lang in cls._registry:  # double-checked locking
                return cls._registry[lang]
            instance = cls._create(lang)
            cls._registry[lang] = instance
            return instance

    @classmethod
    def _create(cls, lang: str) -> BaseTokenizer:
        if lang == "ja":
            from .japanese import JapaneseTokenizer
            return JapaneseTokenizer()
        if lang == "ko":
            from .korean import KoreanTokenizer
            return KoreanTokenizer()
        if lang == "zh":
            from .chinese import ChineseTokenizer
            return ChineseTokenizer()
        if lang == "vi":
            from .vietnamese import VietnameseTokenizer
            return VietnameseTokenizer()
        if lang == "en":
            from .whitespace import WhitespaceTokenizer
            return WhitespaceTokenizer()
        raise UnsupportedLanguageError(f"Unsupported language: {lang!r}")

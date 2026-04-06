# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T003 — VietnameseTokenizer (underthesea)
# Decision: Q5 — word_tokenize confirmed (not tokenize which is char-level)
from underthesea import word_tokenize

from .base import BaseTokenizer


class VietnameseTokenizer(BaseTokenizer):
    def tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        return word_tokenize(text)

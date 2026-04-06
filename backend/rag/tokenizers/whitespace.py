# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T003 — WhitespaceTokenizer (en)
from .base import BaseTokenizer


class WhitespaceTokenizer(BaseTokenizer):
    def tokenize(self, text: str) -> list[str]:
        return text.split()

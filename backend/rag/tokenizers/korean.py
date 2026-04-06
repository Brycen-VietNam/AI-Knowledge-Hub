# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T003 — KoreanTokenizer (kiwipiepy)
# Decision: D04 — kiwipiepy (MIT), replaces KoNLPy (Java)
# Decision: D09 — all morphemes, form only
from kiwipiepy import Kiwi

from .base import BaseTokenizer


class KoreanTokenizer(BaseTokenizer):
    def __init__(self):
        self._kiwi = Kiwi()

    def tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        return [token.form for token in self._kiwi.tokenize(text)]

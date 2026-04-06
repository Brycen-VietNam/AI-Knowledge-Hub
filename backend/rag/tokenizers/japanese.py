# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T002 — JapaneseTokenizer (MeCab)
# Decision: D09 — surface forms (MeCab default ipadic)
import MeCab

from .base import BaseTokenizer


class JapaneseTokenizer(BaseTokenizer):
    def __init__(self):
        self._tagger = MeCab.Tagger()

    def tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        node = self._tagger.parseToNode(text)
        tokens = []
        while node:
            if node.surface:
                tokens.append(node.surface)
            node = node.next
        return tokens

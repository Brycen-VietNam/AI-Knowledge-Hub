# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T003 — ChineseTokenizer (jieba)
# Decision: D10 — zh-cn / zh-tw both handled by jieba
import logging

import jieba

from .base import BaseTokenizer

jieba.setLogLevel(logging.WARNING)


class ChineseTokenizer(BaseTokenizer):
    def tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        return [tok for tok in jieba.cut(text) if tok.strip()]

# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T001 — BaseTokenizer ABC
from abc import ABC, abstractmethod


class BaseTokenizer(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into a list of string tokens."""
        ...

# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: T001 — Exception classes


class UnsupportedLanguageError(ValueError):
    """Raised when TokenizerFactory.get() receives an unsupported language code."""


class LanguageDetectionError(RuntimeError):
    """Raised when language detection fails (short text, low confidence, or detect error)."""

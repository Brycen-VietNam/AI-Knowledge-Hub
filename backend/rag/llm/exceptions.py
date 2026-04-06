class LLMError(Exception):
    """Raised when an LLM provider call fails."""


class NoRelevantChunksError(LLMError):
    """Raised when context_chunks is empty — no answer without source (C014)."""

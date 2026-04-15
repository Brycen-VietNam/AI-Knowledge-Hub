from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Result returned by any LLMProvider.complete() call."""

    # Spec: docs/answer-citation/spec/answer-citation.spec.md#S003
    # Task: T001 — delete sources (D-CIT-09), add inline_markers_present
    answer: str
    confidence: float
    provider: str
    model: str
    low_confidence: bool
    inline_markers_present: bool = False


class LLMProvider(ABC):
    """Abstract base class for all LLM provider adapters.

    Subclasses must implement complete(), which receives the user prompt,
    pre-retrieved context chunks, and document titles, and returns an LLMResponse.
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        context_chunks: list[str],
        doc_titles: list[str],
    ) -> LLMResponse:
        """Generate an answer from the prompt and retrieved context chunks.

        Args:
            prompt: The raw user query (already sanitised by the API layer).
            context_chunks: Text content of documents returned by the retriever.
            doc_titles: Ordered document titles matching context_chunks indices.

        Returns:
            LLMResponse with answer, confidence, and low_confidence flag.

        Raises:
            NoRelevantChunksError: If context_chunks is empty (C014 gate).
            LLMError: On any provider-side failure.
        """
        ...

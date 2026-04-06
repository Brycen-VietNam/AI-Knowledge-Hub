from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Result returned by any LLMProvider.complete() call."""

    answer: str
    sources: list[str]
    confidence: float
    provider: str
    model: str
    low_confidence: bool


class LLMProvider(ABC):
    """Abstract base class for all LLM provider adapters.

    Subclasses must implement complete(), which receives the user prompt and
    pre-retrieved context chunks, and returns an LLMResponse.
    """

    @abstractmethod
    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse:
        """Generate an answer from the prompt and retrieved context chunks.

        Args:
            prompt: The raw user query (already sanitised by the API layer).
            context_chunks: Text content of documents returned by the retriever.

        Returns:
            LLMResponse with answer, sources, confidence, and low_confidence flag.

        Raises:
            NoRelevantChunksError: If context_chunks is empty (C014 gate).
            LLMError: On any provider-side failure.
        """
        ...

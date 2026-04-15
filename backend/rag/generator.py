# Spec: docs/llm-provider/spec/llm-provider.spec.md#S005
# Task: T013 — generate_answer() service layer (D08)
# Decision: D08 — api-agent calls generate_answer(), never LLMProviderFactory directly (ARCH A002)
from .llm import LLMProviderFactory, LLMResponse


async def generate_answer(query: str, chunks: list[str], doc_titles: list[str]) -> LLMResponse:
    """Service layer: api-agent calls this — never imports LLMProviderFactory directly (ARCH A002)."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#S003
    # Task: T006 — pass doc_titles through to adapter (AC6: no lang hardcoded)
    provider = LLMProviderFactory.get()
    return await provider.complete(query, chunks, doc_titles)

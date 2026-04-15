import os
from pathlib import Path

from backend.rag.citation_parser import _parse_citations
from .base import LLMProvider, LLMResponse
from .exceptions import LLMError, NoRelevantChunksError

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "answer.txt").read_text()


class ClaudeAdapter(LLMProvider):
    """LLM adapter for the Anthropic Claude Messages API.

    Configuration via env vars:
        ANTHROPIC_API_KEY: Anthropic secret key.
        LLM_MODEL:         Model ID (default: claude-haiku-4-5-20251001, per D02/A02).

    Confidence is derived from cited_ratio (BACKLOG-2) — Claude has no logprobs endpoint (D06).
    """
    def __init__(self):
        self._api_key = os.getenv("ANTHROPIC_API_KEY")
        self._model = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")

    async def complete(
        self,
        prompt: str,
        context_chunks: list[str],
        doc_titles: list[str],
    ) -> LLMResponse:
        # Spec: docs/answer-citation/spec/answer-citation.spec.md#S003
        # Task: T006 — ClaudeAdapter updated complete() (D-CIT-09, AC5 fallback)
        # Decision: D06 — sentinel 0.9 (Claude has no logprobs)
        # Route A prompt caching: stable prefix ends at "Sources:" label; {sources_index}+{question} are volatile suffix
        if not context_chunks:
            raise NoRelevantChunksError("No relevant chunks (C014)")
        import anthropic  # lazy import — SDK not loaded until needed
        import re
        sources_index = "\n\n".join(
            f"[{i + 1}] {title}\n{chunk}"
            for i, (title, chunk) in enumerate(zip(doc_titles, context_chunks))
        )
        filled = _PROMPT_TEMPLATE.format(sources_index=sources_index, question=prompt)
        try:
            client = anthropic.AsyncAnthropic(api_key=self._api_key)
            msg = await client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": filled}],
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        answer = msg.content[0].text
        # BACKLOG-2: derive confidence from cited_ratio — Claude has no logprobs (D06)
        # Formula: cited_ratio * 0.8 + 0.2  (range [0.2, 1.0]; low_confidence triggers when < 0.4)
        num_docs = len(context_chunks)
        cited_ratio = len(_parse_citations(answer, num_docs)) / num_docs if num_docs else 0.0
        confidence = cited_ratio * 0.8 + 0.2
        return LLMResponse(
            answer=answer,
            confidence=confidence,
            provider="claude",
            model=self._model,
            low_confidence=confidence < 0.4,
            inline_markers_present=bool(re.search(r"\[\d+\]", answer)),
        )

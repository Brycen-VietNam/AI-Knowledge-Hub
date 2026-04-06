import os
from pathlib import Path

from .base import LLMProvider, LLMResponse
from .exceptions import LLMError, NoRelevantChunksError

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "answer.txt").read_text()


class ClaudeAdapter(LLMProvider):
    """LLM adapter for the Anthropic Claude Messages API.

    Configuration via env vars:
        ANTHROPIC_API_KEY: Anthropic secret key.
        LLM_MODEL:         Model ID (default: claude-haiku-4-5-20251001, per D02/A02).

    Confidence is always the sentinel 0.9 — Claude has no logprobs endpoint (D06).
    """
    def __init__(self):
        self._api_key = os.getenv("ANTHROPIC_API_KEY")
        self._model = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")

    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse:
        # Spec: docs/llm-provider/spec/llm-provider.spec.md#S002
        # Task: T008 — ClaudeAdapter (lazy import, D07)
        # Decision: D06 — sentinel 0.9 (Claude has no logprobs)
        # Route A prompt caching: answer.txt is stable prefix; {question}+{context} are volatile suffix
        if not context_chunks:
            raise NoRelevantChunksError("No relevant chunks (C014)")
        import anthropic  # lazy import — SDK not loaded until needed
        filled = _PROMPT_TEMPLATE.format(
            context="\n".join(context_chunks), question=prompt
        )
        try:
            client = anthropic.AsyncAnthropic(api_key=self._api_key)
            msg = await client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": filled}],
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        return LLMResponse(
            answer=msg.content[0].text,
            sources=context_chunks,
            confidence=0.9,  # sentinel — Claude API has no logprobs (D06)
            provider="claude",
            model=self._model,
            low_confidence=False,  # 0.9 is never < 0.4
        )

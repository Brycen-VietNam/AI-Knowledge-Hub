import os
from pathlib import Path

from .base import LLMProvider, LLMResponse
from .exceptions import LLMError, NoRelevantChunksError

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "answer.txt").read_text()


class OpenAIAdapter(LLMProvider):
    """LLM adapter for the OpenAI Chat Completions API.

    Configuration via env vars:
        OPENAI_API_KEY: OpenAI secret key.
        LLM_MODEL:      Model name (default: gpt-4o-mini).

    Confidence is derived from logprobs when available; falls back to sentinel 0.9 (D06).
    """
    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY")
        self._model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse:
        # Spec: docs/llm-provider/spec/llm-provider.spec.md#S002
        # Task: T007 — OpenAIAdapter (lazy import, D07)
        # Decision: D06 — logprobs → confidence; sentinel 0.9 if unavailable
        if not context_chunks:
            raise NoRelevantChunksError("No relevant chunks (C014)")
        import openai  # lazy import — SDK not loaded until needed
        filled = _PROMPT_TEMPLATE.format(
            context="\n".join(context_chunks), question=prompt
        )
        try:
            client = openai.AsyncOpenAI(api_key=self._api_key)
            resp = await client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": filled}],
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        content = resp.choices[0].message.content
        logprobs = resp.choices[0].logprobs
        confidence = float(logprobs.content[0].logprob) if logprobs else 0.9
        return LLMResponse(
            answer=content,
            sources=context_chunks,
            confidence=confidence,
            provider="openai",
            model=self._model,
            low_confidence=confidence < 0.4,
        )

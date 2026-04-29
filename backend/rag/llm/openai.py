import math
import os
from pathlib import Path

from .base import LLMProvider, LLMResponse, LANG_NAMES
from .exceptions import LLMError, NoRelevantChunksError

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "answer.txt").read_text()


class OpenAIAdapter(LLMProvider):
    """LLM adapter for the OpenAI Chat Completions API (or compatible endpoints).

    Configuration via env vars:
        OPENAI_API_KEY:  API key (OpenAI or OpenRouter).
        OPENAI_BASE_URL: Optional base URL override (e.g. https://openrouter.ai/api/v1).
                         Defaults to OpenAI's endpoint when unset.
        LLM_MODEL:       Model name (default: gpt-4o-mini).

    Confidence is derived from logprobs when available; falls back to sentinel 0.9 (D06).
    """
    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY")
        self._base_url = os.getenv("OPENAI_BASE_URL")  # None → openai SDK default
        self._model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def complete(
        self,
        prompt: str,
        context_chunks: list[str],
        doc_titles: list[str],
        lang: str | None = None,
    ) -> LLMResponse:
        # Spec: docs/answer-citation/spec/answer-citation.spec.md#S003
        # Task: T005 — OpenAIAdapter updated complete() (D-CIT-09, AC5 fallback)
        # Decision: D06 — logprobs → confidence; sentinel 0.9 if unavailable
        if not context_chunks:
            raise NoRelevantChunksError("No relevant chunks (C014)")
        import openai  # lazy import — SDK not loaded until needed
        import re
        sources_index = "\n\n".join(
            f"[{i + 1}] {title}\n{chunk}"
            for i, (title, chunk) in enumerate(zip(doc_titles, context_chunks))
        )
        lang_instruction = f"Respond in {LANG_NAMES[lang]}." if lang in LANG_NAMES else ""
        filled = _PROMPT_TEMPLATE.format(sources_index=sources_index, question=prompt, lang_instruction=lang_instruction)
        try:
            client = openai.AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,  # None → SDK default (api.openai.com)
            )
            resp = await client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": filled}],
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        content = resp.choices[0].message.content
        logprobs = resp.choices[0].logprobs
        confidence = math.exp(logprobs.content[0].logprob) if logprobs else 0.9
        return LLMResponse(
            answer=content,
            confidence=confidence,
            provider="openai",
            model=self._model,
            low_confidence=confidence < 0.4,
            inline_markers_present=bool(re.search(r"\[\d+[^\]]*\]|【\d+[^】]*】|\(\d+\)", content)),
        )

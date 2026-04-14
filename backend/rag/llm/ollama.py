import os
from pathlib import Path

import httpx

from backend.rag.config import OLLAMA_LLM_URL
from .base import LLMProvider, LLMResponse
from .exceptions import LLMError, NoRelevantChunksError

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "answer.txt").read_text()


class OllamaAdapter(LLMProvider):
    """LLM adapter for a locally-running Ollama instance.

    Configuration via env vars:
        OLLAMA_BASE_URL: Base URL of the Ollama server (default: http://localhost:11434).
        LLM_MODEL:       Model tag to use (default: llama3).
        LLM_TIMEOUT_S:   HTTP request timeout in seconds (default: 5.0).
    """
    def __init__(self):
        self._base_url = OLLAMA_LLM_URL
        self._model = os.getenv("LLM_MODEL", "llama3")
        self._timeout = float(os.getenv("LLM_TIMEOUT_S", "5.0"))

    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse:
        # Spec: docs/llm-provider/spec/llm-provider.spec.md#S002
        # Task: T006 — OllamaAdapter (async httpx, D07)
        # Decision: D03 — NoRelevantChunksError gates generation (C014)
        if not context_chunks:
            raise NoRelevantChunksError("No relevant chunks — cannot generate answer (C014)")
        filled = _PROMPT_TEMPLATE.format(
            context="\n".join(context_chunks), question=prompt
        )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url}/api/generate",
                    json={"model": self._model, "prompt": filled, "stream": False},
                    timeout=self._timeout,
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise LLMError(str(exc)) from exc
        return LLMResponse(
            answer=data["response"],
            sources=context_chunks,
            confidence=0.9,  # sentinel — Ollama has no logprobs (D06)
            provider="ollama",
            model=self._model,
            low_confidence=False,  # 0.9 is never < 0.4
        )

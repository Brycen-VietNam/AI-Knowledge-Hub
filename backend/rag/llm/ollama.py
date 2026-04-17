import os
import re
from pathlib import Path

import httpx

from backend.rag.citation_parser import _parse_citations
from backend.rag.config import OLLAMA_LLM_URL
from .base import LLMProvider, LLMResponse, LANG_NAMES
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

    async def complete(
        self,
        prompt: str,
        context_chunks: list[str],
        doc_titles: list[str],
        lang: str | None = None,
    ) -> LLMResponse:
        # Spec: docs/answer-citation/spec/answer-citation.spec.md#S003
        # Task: T004 — OllamaAdapter updated complete() (D-CIT-09, AC5 fallback)
        # Decision: D03 — NoRelevantChunksError gates generation (C014)
        if not context_chunks:
            raise NoRelevantChunksError("No relevant chunks — cannot generate answer (C014)")
        sources_index = "\n\n".join(
            f"[{i + 1}] {title}\n{chunk}"
            for i, (title, chunk) in enumerate(zip(doc_titles, context_chunks))
        )
        lang_instruction = f"Respond in {LANG_NAMES[lang]}." if lang in LANG_NAMES else ""
        filled = _PROMPT_TEMPLATE.format(sources_index=sources_index, question=prompt, lang_instruction=lang_instruction)
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
        answer = data["response"]
        # BACKLOG-2: derive confidence from cited_ratio — Ollama has no logprobs (D06)
        # Formula: cited_ratio * 0.8 + 0.2  (range [0.2, 1.0]; low_confidence triggers when < 0.4)
        num_docs = len(context_chunks)
        cited_ratio = len(_parse_citations(answer, num_docs)) / num_docs if num_docs else 0.0
        confidence = cited_ratio * 0.8 + 0.2
        return LLMResponse(
            answer=answer,
            confidence=confidence,
            provider="ollama",
            model=self._model,
            low_confidence=confidence < 0.4,
            inline_markers_present=bool(re.search(r"\[\d+\]", answer)),
        )

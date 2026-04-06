# Spec: docs/llm-provider/spec/llm-provider.spec.md
# Tasks: T001–T012 — LLMProvider base, adapters, factory, C014 gate
import inspect

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.rag.llm.base import LLMProvider, LLMResponse
from backend.rag.llm.exceptions import LLMError, NoRelevantChunksError


# ---------------------------------------------------------------------------
# T001 — Exception hierarchy
# ---------------------------------------------------------------------------

def test_exception_hierarchy():
    assert issubclass(NoRelevantChunksError, LLMError)
    assert issubclass(LLMError, Exception)


def test_no_relevant_chunks_error_is_llm_error():
    err = NoRelevantChunksError("no chunks")
    assert isinstance(err, LLMError)


# ---------------------------------------------------------------------------
# T002+T003 — Base interface + importable package
# ---------------------------------------------------------------------------

def test_llm_package_importable():
    import backend.rag.llm  # must not raise


class TestLLMBase:
    def test_llm_response_fields(self):
        r = LLMResponse(
            answer="42", sources=["doc-1"], confidence=0.9,
            provider="ollama", model="llama3", low_confidence=False
        )
        assert r.answer == "42"
        assert r.sources == ["doc-1"]
        assert r.low_confidence is False

    def test_llm_response_low_confidence_flag(self):
        r = LLMResponse(
            answer="maybe", sources=["doc-2"], confidence=0.3,
            provider="ollama", model="llama3", low_confidence=True
        )
        assert r.low_confidence is True

    def test_llm_provider_is_abstract(self):
        with pytest.raises(TypeError):
            LLMProvider()  # cannot instantiate ABC

    # T004 additions below
    def test_llm_response_all_fields_required(self):
        with pytest.raises(TypeError):
            LLMResponse(answer="x", sources=[])  # missing confidence, provider, model, low_confidence

    def test_complete_is_coroutine(self):
        class FakeProvider(LLMProvider):
            async def complete(self, prompt, context_chunks):
                return LLMResponse("a", [], 0.9, "fake", "m", False)
        p = FakeProvider()
        assert inspect.iscoroutinefunction(p.complete)


# ---------------------------------------------------------------------------
# T005 — Prompt template
# ---------------------------------------------------------------------------

def test_answer_prompt_template_exists():
    from pathlib import Path
    tmpl = Path("backend/rag/llm/prompts/answer.txt").read_text()
    assert "{context}" in tmpl
    assert "{question}" in tmpl


# ---------------------------------------------------------------------------
# T006+T007+T008 — Adapter tests
# ---------------------------------------------------------------------------

class TestAdapters:
    # --- OllamaAdapter ---

    @pytest.mark.asyncio
    async def test_ollama_happy_path(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://fake:11434")
        monkeypatch.setenv("LLM_MODEL", "llama3")
        from backend.rag.llm.ollama import OllamaAdapter
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "The answer is 42."}
        mock_resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await OllamaAdapter().complete("What is 42?", ["doc-1: context text"])
        assert result.provider == "ollama"
        assert result.model == "llama3"
        assert result.answer == "The answer is 42."
        assert result.confidence == 0.9
        assert result.low_confidence is False

    @pytest.mark.asyncio
    async def test_ollama_no_chunks_raises(self):
        from backend.rag.llm.ollama import OllamaAdapter
        with pytest.raises(NoRelevantChunksError):
            await OllamaAdapter().complete("query", [])

    @pytest.mark.asyncio
    async def test_ollama_network_error_raises_llm_error(self):
        from backend.rag.llm.ollama import OllamaAdapter
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(LLMError):
                await OllamaAdapter().complete("q", ["chunk"])

    @pytest.mark.asyncio
    async def test_ollama_http_error_raises_llm_error(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://fake")
        from backend.rag.llm.ollama import OllamaAdapter
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(LLMError):
                await OllamaAdapter().complete("q", ["chunk"])

    # --- OpenAIAdapter ---

    @pytest.mark.asyncio
    async def test_openai_happy_path(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Answer text"
        mock_completion.choices[0].logprobs = None
        openai_mock = MagicMock()
        openai_mock.OpenAI.return_value.chat.completions.create.return_value = mock_completion
        with patch.dict("sys.modules", {"openai": openai_mock}):
            from backend.rag.llm import openai as _openai_mod
            import importlib
            importlib.reload(_openai_mod)
            result = await _openai_mod.OpenAIAdapter().complete("Q?", ["chunk1"])
        assert result.provider == "openai"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_openai_no_chunks_raises(self):
        from backend.rag.llm.openai import OpenAIAdapter
        with pytest.raises(NoRelevantChunksError):
            await OpenAIAdapter().complete("q", [])

    @pytest.mark.asyncio
    async def test_openai_api_error_raises_llm_error(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "bad")
        openai_mock = MagicMock()
        openai_mock.OpenAI.return_value.chat.completions.create.side_effect = Exception("auth")
        with patch.dict("sys.modules", {"openai": openai_mock}):
            from backend.rag.llm import openai as _openai_mod
            import importlib
            importlib.reload(_openai_mod)
            with pytest.raises(LLMError):
                await _openai_mod.OpenAIAdapter().complete("q", ["chunk"])

    # --- ClaudeAdapter ---

    @pytest.mark.asyncio
    async def test_claude_happy_path(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("LLM_MODEL", "claude-haiku-4-5-20251001")
        mock_msg = MagicMock()
        mock_msg.content[0].text = "Claude answer"
        anthropic_mock = MagicMock()
        anthropic_mock.Anthropic.return_value.messages.create.return_value = mock_msg
        with patch.dict("sys.modules", {"anthropic": anthropic_mock}):
            from backend.rag.llm import claude as _claude_mod
            import importlib
            importlib.reload(_claude_mod)
            result = await _claude_mod.ClaudeAdapter().complete("Q?", ["chunk1"])
        assert result.provider == "claude"
        assert result.model == "claude-haiku-4-5-20251001"
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_claude_no_chunks_raises(self):
        from backend.rag.llm.claude import ClaudeAdapter
        with pytest.raises(NoRelevantChunksError):
            await ClaudeAdapter().complete("q", [])

    @pytest.mark.asyncio
    async def test_claude_api_error_raises_llm_error(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "bad")
        anthropic_mock = MagicMock()
        anthropic_mock.Anthropic.return_value.messages.create.side_effect = Exception("rate limit")
        with patch.dict("sys.modules", {"anthropic": anthropic_mock}):
            from backend.rag.llm import claude as _claude_mod
            import importlib
            importlib.reload(_claude_mod)
            with pytest.raises(LLMError):
                await _claude_mod.ClaudeAdapter().complete("q", ["chunk"])


# ---------------------------------------------------------------------------
# T009 — Factory tests
# ---------------------------------------------------------------------------

class TestFactory:
    def setup_method(self):
        from backend.rag.llm.factory import LLMProviderFactory
        LLMProviderFactory._instances.clear()

    def test_default_provider_is_ollama(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        from backend.rag.llm.factory import LLMProviderFactory
        from backend.rag.llm.ollama import OllamaAdapter
        provider = LLMProviderFactory.get()
        assert isinstance(provider, OllamaAdapter)

    def test_ollama_explicit(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        from backend.rag.llm.factory import LLMProviderFactory
        from backend.rag.llm.ollama import OllamaAdapter
        provider = LLMProviderFactory.get()
        assert isinstance(provider, OllamaAdapter)

    def test_openai_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        from backend.rag.llm.factory import LLMProviderFactory
        from backend.rag.llm.openai import OpenAIAdapter
        provider = LLMProviderFactory.get()
        assert isinstance(provider, OpenAIAdapter)

    def test_claude_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "claude")
        from backend.rag.llm.factory import LLMProviderFactory
        from backend.rag.llm.claude import ClaudeAdapter
        provider = LLMProviderFactory.get()
        assert isinstance(provider, ClaudeAdapter)

    def test_unknown_provider_raises(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        from backend.rag.llm.factory import LLMProviderFactory
        with pytest.raises(LLMError, match="Unsupported provider"):
            LLMProviderFactory.get()

    def test_singleton_same_instance(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        from backend.rag.llm.factory import LLMProviderFactory
        p1 = LLMProviderFactory.get()
        p2 = LLMProviderFactory.get()
        assert p1 is p2


# ---------------------------------------------------------------------------
# T010 — Public API exports
# ---------------------------------------------------------------------------

def test_public_api_exports():
    from backend.rag.llm import (  # noqa: F401
        LLMProvider, LLMResponse, LLMProviderFactory,
        LLMError, NoRelevantChunksError
    )
    # concrete adapters must NOT be importable from public API
    with pytest.raises(ImportError):
        from backend.rag.llm import OllamaAdapter  # noqa: F401


# ---------------------------------------------------------------------------
# T011 — TestAnswerGate (C014 regression — must never be skipped)
# ---------------------------------------------------------------------------

class TestAnswerGate:
    """
    C014 regression tests.
    CONSTITUTION C014: No answer generated if no relevant chunks found.
    Confidence < 0.4 triggers low-confidence warning.
    These tests must never be skipped.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("adapter_class,env_key,env_val", [
        ("OllamaAdapter", "OLLAMA_BASE_URL", "http://fake"),
        ("OpenAIAdapter", "OPENAI_API_KEY", "test"),
        ("ClaudeAdapter", "ANTHROPIC_API_KEY", "test"),
    ])
    async def test_no_relevant_chunks_raises_for_all_adapters(self, adapter_class, env_key, env_val, monkeypatch):
        """AC5 — C014 hard gate: empty chunks → NoRelevantChunksError, always."""
        monkeypatch.setenv(env_key, env_val)
        if adapter_class == "OllamaAdapter":
            from backend.rag.llm.ollama import OllamaAdapter as Adapter
        elif adapter_class == "OpenAIAdapter":
            from backend.rag.llm.openai import OpenAIAdapter as Adapter
        else:
            from backend.rag.llm.claude import ClaudeAdapter as Adapter
        with pytest.raises(NoRelevantChunksError):
            await Adapter().complete("any query", [])

    def test_low_confidence_flag_set_when_below_threshold(self):
        """AC6 — C014: confidence < 0.4 → low_confidence=True on LLMResponse."""
        r = LLMResponse(
            answer="uncertain", sources=["doc-1"],
            confidence=0.3, provider="test", model="m",
            low_confidence=True
        )
        assert r.low_confidence is True
        assert r.confidence < 0.4

    def test_low_confidence_flag_not_set_when_above_threshold(self):
        """Complement: confidence >= 0.4 → low_confidence=False."""
        r = LLMResponse(
            answer="confident", sources=["doc-1"],
            confidence=0.4, provider="test", model="m",
            low_confidence=False
        )
        assert r.low_confidence is False

    def test_low_confidence_boundary_exactly_04(self):
        """Boundary: confidence == 0.4 is NOT low confidence (< not <=)."""
        r = LLMResponse(
            answer="ok", sources=["doc-1"],
            confidence=0.4, provider="test", model="m",
            low_confidence=False  # 0.4 is NOT < 0.4
        )
        assert r.low_confidence is False

    @pytest.mark.asyncio
    async def test_ollama_no_chunks_raised_before_http_call(self):
        """NoRelevantChunksError must be raised BEFORE any network call."""
        from backend.rag.llm.ollama import OllamaAdapter
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        with patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(NoRelevantChunksError):
                await OllamaAdapter().complete("q", [])
            mock_client.post.assert_not_called()  # HTTP call never made

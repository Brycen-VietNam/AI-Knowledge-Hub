# Spec: docs/llm-provider/spec/llm-provider.spec.md#S005
# Task: T013 — generate_answer() service layer tests
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.rag.generator import generate_answer
from backend.rag.llm import LLMResponse, NoRelevantChunksError


@pytest.mark.asyncio
async def test_generate_answer_delegates_to_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    mock_response = LLMResponse("ans", ["doc-1"], 0.9, "ollama", "llama3", False)
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        result = await generate_answer("What?", ["chunk1"])
    assert result.answer == "ans"
    assert result.provider == "ollama"


@pytest.mark.asyncio
async def test_generate_answer_propagates_no_chunks_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(side_effect=NoRelevantChunksError("empty"))
        mock_factory.return_value = mock_provider
        with pytest.raises(NoRelevantChunksError):
            await generate_answer("Q?", [])

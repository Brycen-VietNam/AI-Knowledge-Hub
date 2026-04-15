# Spec: docs/llm-provider/spec/llm-provider.spec.md#S005
# Spec: docs/answer-citation/spec/answer-citation.spec.md#S003
# Task: T013 — generate_answer() service layer tests
# Task: S005-T003 — AC5a, AC5b, AC6 (doc_titles, CJK), GAP-2 (OOB marker)
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.rag.generator import generate_answer
from backend.rag.llm import LLMResponse, NoRelevantChunksError


@pytest.mark.asyncio
async def test_generate_answer_delegates_to_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    mock_response = LLMResponse("ans", 0.9, "ollama", "llama3", False)
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        result = await generate_answer("What?", ["chunk1"], ["Doc 1"])
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
            await generate_answer("Q?", [], [])


# ---------------------------------------------------------------------------
# S005-T003 — AC5a: inline_markers_present=True when [N] in answer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generator_inline_markers_present(monkeypatch):
    """AC5a: adapter returns answer with '[1]' → inline_markers_present=True propagated."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC5
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    mock_response = LLMResponse(
        answer="According to [1] the policy states...",
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
        inline_markers_present=True,
    )
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        result = await generate_answer("Policy?", ["chunk1"], ["Doc 1"])
    assert result.inline_markers_present is True
    assert "[1]" in result.answer


# ---------------------------------------------------------------------------
# S005-T003 — AC5b: graceful fallback when no [N] markers in answer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generator_inline_markers_fallback(monkeypatch):
    """AC5b: adapter returns answer without [N] → inline_markers_present=False; no exception."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC5
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    mock_response = LLMResponse(
        answer="The policy covers all employees.",
        confidence=0.8,
        provider="ollama",
        model="llama3",
        low_confidence=False,
        inline_markers_present=False,
    )
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        result = await generate_answer("Policy?", ["chunk1"], ["Doc 1"])
    assert result.inline_markers_present is False
    assert result.answer == "The policy covers all employees."


# ---------------------------------------------------------------------------
# S005-T003 — AC6: doc_titles forwarded to adapter complete()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generator_doc_titles_passed_to_adapter(monkeypatch):
    """AC6: generate_answer() forwards doc_titles list to provider.complete() unchanged."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC6
    # Decision: D-CIT-05 — API layer passes titles; adapter builds numbered index
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    expected_titles = ["HR Policy", "Safety Manual", "Code of Conduct"]
    mock_response = LLMResponse("ok", 0.9, "ollama", "llama3", False)
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        await generate_answer("What?", ["c1", "c2", "c3"], expected_titles)
    mock_provider.complete.assert_called_once()
    _, call_args, call_kwargs = mock_provider.complete.mock_calls[0]
    # doc_titles is the 3rd positional arg
    passed_titles = call_args[2] if len(call_args) > 2 else call_kwargs.get("doc_titles")
    assert passed_titles == expected_titles


# ---------------------------------------------------------------------------
# S005-T003 — AC6 CJK: generate_answer does not override answer language
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["ja", "en", "vi", "ko", "zh"])
async def test_generator_cjk_answer_language(lang, monkeypatch):
    """AC6 CJK: generate_answer() does not override adapter's answer language."""
    # Spec: docs/answer-citation/spec/answer-citation.spec.md#AC6
    # Rule: ARCH A003 — never hardcode lang="en" as fallback
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    expected_answer = f"answer in {lang}"
    mock_response = LLMResponse(expected_answer, 0.9, "ollama", "llama3", False)
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        result = await generate_answer(f"query in {lang}", ["chunk"], ["Doc"])
    # generate_answer must return the adapter's answer verbatim — no lang override
    assert result.answer == expected_answer


# ---------------------------------------------------------------------------
# S005-T003 — GAP-2: OOB marker [99] with only 3 citations → 200, answer unchanged
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_oob_marker_in_answer(monkeypatch):
    """GAP-2: LLM emits [99] but citations has 3 entries → answer returned as-is, no exception.

    The API layer does NOT validate marker indices against citations length.
    Consumer contract (S004 AC2) handles OOB gracefully by rendering plain text.
    """
    # WARM: answer-citation.mem.md GAP-2
    # Decision: D-CIT-08 — graceful fallback; no hard gate in v1
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    oob_answer = "See [99] for details."  # [99] is out of range — only 3 docs
    mock_response = LLMResponse(
        answer=oob_answer,
        confidence=0.9,
        provider="ollama",
        model="llama3",
        low_confidence=False,
        inline_markers_present=True,
    )
    with patch("backend.rag.generator.LLMProviderFactory.get") as mock_factory:
        mock_provider = MagicMock()
        mock_provider.complete = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_provider
        result = await generate_answer(
            "question",
            ["chunk1", "chunk2", "chunk3"],
            ["Doc 1", "Doc 2", "Doc 3"],
        )
    # generate_answer must not raise; answer returned unchanged
    assert result.answer == oob_answer
    assert result.inline_markers_present is True

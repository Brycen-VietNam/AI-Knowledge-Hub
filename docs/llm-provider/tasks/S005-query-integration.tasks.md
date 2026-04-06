# Tasks: S005 (Post-G3) — QueryResponse schema + generator.py service layer
Feature: llm-provider | Agent: api-agent (generator.py: rag-agent) | Generated: 2026-04-06 | Status: DONE ✅ 2026-04-06
Decisions: D08 (generator.py), D09 (NoRelevantChunks → 200), D10 (breaking QueryResponse)

---

## Task Summary

| ID | Title | Parallel | Est. lines |
|----|-------|----------|------------|
| T013 | Create `backend/rag/generator.py` — generate_answer() service layer (D08) | safe | ~25 |
| T014 | Update `backend/api/routes/query.py` — call generate_answer(), new response schema (D09+D10) | after:T013 | ~40 |

**Parallel groups:** G1[T013], G2[T014]
**Depends:** S003 complete (factory interface locked before api-agent touches query.py)
**Est. total tokens to implement:** ~2.5k

---

## T013 — Create generator.py service layer

**Agent:** rag-agent (owns `backend/rag/`)
**Parallel:** safe (after S003)
**TOUCH:**
- `backend/rag/generator.py` (CREATE)
- `tests/rag/test_generator.py` (CREATE)

**Test first:**
```python
# tests/rag/test_generator.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
```

**Then implement:**
```python
# backend/rag/generator.py
from .llm import LLMProviderFactory, LLMResponse

async def generate_answer(query: str, chunks: list[str]) -> LLMResponse:
    """Service layer: api-agent calls this — never imports LLMProviderFactory directly (ARCH A002)."""
    provider = LLMProviderFactory.get()
    return await provider.complete(query, chunks)
```

**review_criteria:**
- `generate_answer()` is `async` — no sync wrapper
- `LLMProviderFactory.get()` called each time (singleton handles caching)
- No `try/except` here — errors propagate to api-agent for HTTP translation (D09)
- ARCH A002: `backend/rag/generator.py` is rag-agent scope; api-agent imports only `generate_answer`

**test_cmd:** `pytest tests/rag/test_generator.py -v`

---

## T014 — Update query.py (D09 + D10)

**Agent:** api-agent (owns `backend/api/routes/`)
**Parallel:** after:T013
**TOUCH:**
- `backend/api/routes/query.py` (MODIFY)
- `tests/api/test_query_route.py` (MODIFY — update/add tests for new response shape)

**Test first (update existing tests + add new):**
```python
# tests/api/test_query_route.py — add/update:

@pytest.mark.asyncio
async def test_query_returns_answer_and_sources(client, mock_retriever, mock_generator):
    """D10: response shape is {answer, sources, low_confidence} not results[]."""
    mock_generator.return_value = LLMResponse(
        answer="42", sources=["doc-1"], confidence=0.9,
        provider="ollama", model="llama3", low_confidence=False
    )
    resp = await client.post("/v1/query", json={"query": "What is 42?"}, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
    assert "low_confidence" in body
    assert "results" not in body  # D10: old field removed

@pytest.mark.asyncio
async def test_query_no_chunks_returns_200_with_null_answer(client, mock_retriever):
    """D09: NoRelevantChunksError → 200 {answer: null, reason: no_relevant_chunks}."""
    mock_retriever.return_value = []  # no chunks found
    resp = await client.post("/v1/query", json={"query": "unknown"}, headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] is None
    assert body["reason"] == "no_relevant_chunks"

@pytest.mark.asyncio
async def test_query_low_confidence_flagged_in_response(client, mock_retriever, mock_generator):
    """D10: low_confidence flag surfaced in response."""
    mock_generator.return_value = LLMResponse(
        answer="maybe", sources=["doc-1"], confidence=0.3,
        provider="ollama", model="llama3", low_confidence=True
    )
    resp = await client.post("/v1/query", json={"query": "Q?"}, headers=AUTH)
    assert resp.json()["low_confidence"] is True
```

**Then implement (query.py changes):**
```python
# backend/api/routes/query.py — key changes only (signatures + logic):

from backend.rag.generator import generate_answer
from backend.rag.llm import NoRelevantChunksError

# New response model (D10 breaking change):
class QueryResponse(BaseModel):
    answer: str | None
    sources: list[str]
    low_confidence: bool
    reason: str | None = None  # populated only when answer is None (D09)

@router.post("/v1/query", dependencies=[Depends(verify_token)])
async def query(request: QueryRequest, ...) -> QueryResponse:
    chunks = await retriever.retrieve(request.query, ...)
    try:
        result = await generate_answer(request.query, [c.text for c in chunks])
    except NoRelevantChunksError:
        # D09: bot-friendly — no 4xx
        return QueryResponse(answer=None, sources=[], low_confidence=False, reason="no_relevant_chunks")
    return QueryResponse(
        answer=result.answer,
        sources=result.sources,
        low_confidence=result.low_confidence,
    )
```

**review_criteria:**
- `results[]` field removed from `QueryResponse` — D10 breaking change confirmed
- `NoRelevantChunksError` caught → 200 + `{answer: null, reason: "no_relevant_chunks"}` — D09
- `generate_answer()` imported from `backend.rag.generator` — NOT `LLMProviderFactory` directly (ARCH A002)
- `verify_token` dependency present — R003 (auth on every endpoint)
- Route prefix `/v1/` — R004
- Audit log call present (R006 — already implemented in prior auth feature)

**test_cmd:** `pytest tests/api/test_query_route.py -v`

# Plan: llm-provider
Generated: 2026-04-06 | Spec: docs/llm-provider/spec/llm-provider.spec.md | Checklist: PASS 30/30

---

## Layer 1 — Plan Summary

| Field | Value |
|-------|-------|
| Stories | 4 |
| Sessions est. | 2 |
| Critical path | S001 → S002 → S003 ∥ S004 |
| Token budget total | ~18k |

### Parallel Groups
```
G1 (sequential): S001 (rag-agent) — base interface + dataclasses
G2 (after G1):   S002 (rag-agent) — three adapters [longest story]
G3 (after G2, parallel):
  G3a: S003 (rag-agent) — factory
  G3b: S004 (rag-agent) — tests
  NOTE: S003 + S004 touch different files — parallel-safe
        S004 depends on S001+S002+S003 interfaces (read-only) — safe to run concurrently
        after S002 because factory.py is needed to test get() paths
```

### Agent Assignments
| Story | Agent | Parallel group |
|-------|-------|----------------|
| S001 | rag-agent | G1 — sequential |
| S002 | rag-agent | G2 — sequential after G1 |
| S003 | rag-agent | G3a — parallel with S004 |
| S004 | rag-agent | G3b — parallel with S003 |
| QueryResponse schema update (D10) | api-agent | after G3 (S003 must be done — interface locked) |

---

## Layer 2 — Per-Story Plans

---

### S001: LLMProvider abstract interface + dataclasses
**Agent:** rag-agent | **Group:** G1 | **Depends:** none | **Dispatch:** YES

**Files:**
```
CREATE: backend/rag/llm/__init__.py          — stub only (exports added in S003)
CREATE: backend/rag/llm/base.py              — LLMProvider ABC, LLMResponse dataclass
CREATE: backend/rag/llm/exceptions.py        — LLMError, NoRelevantChunksError
```

**Key contracts to implement:**
```python
# base.py
@dataclass
class LLMResponse:
    answer: str
    sources: list[str]
    confidence: float
    provider: str
    model: str
    low_confidence: bool  # True when confidence < 0.4

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse: ...

# exceptions.py
class LLMError(Exception): ...
class NoRelevantChunksError(LLMError): ...  # raised when context_chunks == []
```

**HARD rules:**
- S005: no secrets in source
- ARCH A001: `backend/rag/llm/` owned by rag-agent only

**Est. tokens:** ~1.5k
**Test:** `pytest tests/rag/test_llm_provider.py::TestLLMBase -v`

---

### S002: Three provider adapters (Ollama, OpenAI, Claude)
**Agent:** rag-agent | **Group:** G2 | **Depends:** S001 | **Dispatch:** YES

**Files:**
```
CREATE: backend/rag/llm/ollama.py            — OllamaAdapter (async httpx)
CREATE: backend/rag/llm/openai.py            — OpenAIAdapter (openai SDK)
CREATE: backend/rag/llm/claude.py            — ClaudeAdapter (anthropic SDK)
CREATE: backend/rag/llm/prompts/answer.txt   — {context} + {question} placeholders
MODIFY: requirements.txt                     — add: openai, anthropic
```

**Key contracts:**
```python
# ollama.py — MUST be async (clarify D07)
class OllamaAdapter(LLMProvider):
    async def complete(self, prompt: str, context_chunks: list[str]) -> LLMResponse:
        # raises NoRelevantChunksError if context_chunks == []
        # uses async httpx.AsyncClient — NEVER sync
        # reads OLLAMA_BASE_URL (default http://localhost:11434), LLM_MODEL (default llama3)
        # wraps all httpx errors → LLMError

# openai.py
class OpenAIAdapter(LLMProvider):
    # reads OPENAI_API_KEY, LLM_MODEL (default gpt-4o-mini)
    # confidence from logprobs if available, else sentinel 0.9

# claude.py
class ClaudeAdapter(LLMProvider):
    # reads ANTHROPIC_API_KEY, LLM_MODEL (default claude-haiku-4-5-20251001)
    # prompt caching: answer.txt template = stable prefix (Route A, Policy v1)
    # confidence sentinel 0.9 (no logprobs in Claude API)
    # low_confidence = confidence < 0.4
```

**Prompt template (answer.txt):**
```
Given the following context documents, answer the question accurately and concisely.
Cite the source document IDs in your answer.

Context:
{context}

Question:
{question}

Answer:
```

**HARD rules:**
- S005: all keys via `os.getenv()` — zero hardcoded
- ARCH A001: no imports from `backend/api/` or `backend/auth/`
- All adapters load `answer.txt` at startup, not per-request

**Est. tokens:** ~4k
**Test:** `pytest tests/rag/test_llm_provider.py::TestAdapters -v`

---

### S003: LLMProviderFactory
**Agent:** rag-agent | **Group:** G3a | **Depends:** S001, S002 | **Parallel with:** S004 | **Dispatch:** YES

**Files:**
```
CREATE: backend/rag/llm/factory.py           — LLMProviderFactory
MODIFY: backend/rag/llm/__init__.py          — add public exports
```

**Key contracts:**
```python
# factory.py — singleton per provider per process (threading.Lock pattern, same as TokenizerFactory)
class LLMProviderFactory:
    _instances: dict[str, LLMProvider] = {}
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def get(cls) -> LLMProvider:
        provider = os.getenv("LLM_PROVIDER", "ollama")
        # "ollama" | "openai" | "claude" → return singleton
        # unknown → raise LLMError("Unsupported provider: ...")
        # lazy import inside _create() — don't load all 3 SDKs at startup (P007)

# __init__.py exports (concrete adapters NOT exported):
from .base import LLMProvider, LLMResponse
from .exceptions import LLMError, NoRelevantChunksError
from .factory import LLMProviderFactory
```

**Est. tokens:** ~1.5k
**Test:** `pytest tests/rag/test_llm_provider.py::TestFactory -v`

---

### S004: Integration tests + answer-generation gate
**Agent:** rag-agent | **Group:** G3b | **Depends:** S001, S002, S003 (interfaces only — read) | **Parallel with:** S003 | **Dispatch:** YES

**Files:**
```
CREATE: tests/rag/test_llm_provider.py       — all mocked, offline
```

**Test structure:**
```python
class TestLLMBase:          # S001 — dataclass field presence, LLMError hierarchy
class TestAdapters:         # S002 — mock httpx/openai/anthropic per AC2/AC3/AC4
class TestFactory:          # S003 — all 3 providers + unknown + default "ollama"
class TestAnswerGate:       # S004 — NoRelevantChunks + LowConfidence regression (C014)
```

**Critical regressions (C014 — never skip):**
```python
def test_no_relevant_chunks_raises():
    # context_chunks=[] → NoRelevantChunksError (AC5)

def test_low_confidence_flag():
    # confidence=0.3 → low_confidence=True (AC6)
```

**Coverage gate:** ≥ 80% for all `backend/rag/llm/*.py`

**HARD rules:**
- All provider calls mocked — no real API keys in CI
- `monkeypatch.setenv` for all env vars

**Est. tokens:** ~3k
**Test:** `pytest tests/rag/test_llm_provider.py -v --cov=backend/rag/llm --cov-report=term-missing`

---

### Post-G3: QueryResponse schema update (D10)
**Agent:** api-agent | **Group:** after G3 | **Depends:** S003 (interface locked) | **Dispatch:** YES

**Files:**
```
MODIFY: backend/api/routes/query.py          — call generate_answer(); update response schema
MODIFY: backend/rag/generator.py             — NEW service layer (D08): wraps LLMProviderFactory
```

**Key contracts (D08 + D09 + D10):**
```python
# backend/rag/generator.py (NEW — rag-agent scope, called by api-agent)
async def generate_answer(query: str, chunks: list[str]) -> LLMResponse:
    provider = LLMProviderFactory.get()
    return await provider.complete(query, chunks)

# backend/api/routes/query.py (api-agent)
# BREAKING CHANGE: replace results[] → answer + sources + low_confidence (D10)
# NoRelevantChunksError → 200 + {"answer": null, "reason": "no_relevant_chunks"} (D09)
```

**Est. tokens:** ~2k
**Test:** `pytest tests/api/test_query_route.py -v`

---

## Dispatch Order

```
Session 1:
  → dispatch rag-agent: S001 (sequential)
  → dispatch rag-agent: S002 (after S001)

Session 2:
  → dispatch rag-agent: S003 + S004 in parallel (after S002)
  → dispatch api-agent: QueryResponse update (after S003)
```

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| OllamaAdapter sync/async mistake | Medium | D07 in WARM + clarify.md A01: must use async httpx.AsyncClient |
| ClaudeAdapter default model drift | Low | Hardcoded to `claude-haiku-4-5-20251001` via env default; CLAUDE.md model table is source of truth |
| S004 parallel with S003 — factory.py not ready | Low | S004 reads factory interface only; mocks replace real factory in tests |
| QueryResponse breaking change (D10) | Low | Consumers not in production; migration cost = 0 (confirmed in clarify Q3) |

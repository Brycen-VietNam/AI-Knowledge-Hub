# Spec: llm-provider
Created: 2026-04-06 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary

| Field | Value |
|-------|-------|
| Epic | rag-pipeline |
| Priority | P0 |
| Story count | 4 |
| Token budget est. | ~5k |
| Critical path | S001 → S002 → S003 → S004 |
| Parallel-safe stories | S003 ∥ S004 (after S002) |
| Blocking specs | None |
| Blocked by | cjk-tokenizer ✅ |
| Agents needed | rag-agent, api-agent |
| Prompt caching | Route A (stable prefix) — `answer.txt` template is stable prefix; `{question}` + `{context}` are volatile suffix. Route B (`cache_control` on system prompt block) optional for `ClaudeAdapter` direct API path — add post-implementation if cost monitoring shows benefit. |

### Problem Statement
The `/v1/query` endpoint has no LLM response generation layer — retrieval returns chunks but no synthesized answer.
C015 mandates a multi-provider adapter (ollama/openai/claude) configurable via `LLM_PROVIDER` env var.
C014 mandates that answers cite ≥1 source document and suppress generation when no relevant chunks are found.

### Solution Summary
- `LLMProvider` abstract interface with `complete(prompt, context_chunks) -> LLMResponse`
- Three concrete adapters: `OllamaAdapter` (default/free/local), `OpenAIAdapter`, `ClaudeAdapter`
- `LLMProviderFactory.get()` reads `LLM_PROVIDER` + `LLM_MODEL` env vars — no hardcoded names
- Answer generation gated by chunk relevance: no chunks → return structured error; confidence < 0.4 → low-confidence flag (C014)
- All adapters output uniform `LLMResponse(answer, sources, confidence, provider, model)` dataclass

### Out of Scope
- Fine-tuning or model hosting — provider adapters only
- Streaming responses — deferred to `streaming-query` feature
- Prompt template management UI — templates are files, not DB records
- Reranker — separate `multilingual-rag-pipeline` scope
- Conflict detection — separate scope

---

## LAYER 2 — Story Detail

### S001: LLMProvider abstract interface + dataclasses

**Role / Want / Value**
- As a: rag-agent developer
- I want: a `LLMProvider` ABC and `LLMResponse` dataclass
- So that: all adapters share a contract; callers never import concrete adapters directly

**Acceptance Criteria**
- [ ] AC1: `LLMProvider` ABC in `backend/rag/llm/base.py` with abstract method `complete(prompt: str, context_chunks: list[str]) -> LLMResponse`
- [ ] AC2: `LLMResponse` dataclass fields: `answer: str`, `sources: list[str]`, `confidence: float`, `provider: str`, `model: str`
- [ ] AC3: `LLMError` exception class in `backend/rag/llm/exceptions.py` — raised when provider call fails; distinct from `LanguageDetectionError`
- [ ] AC4: `NoRelevantChunksError(LLMError)` — raised when context_chunks is empty (C014: no answer without source)
- [ ] AC5: `LowConfidenceWarning` — not an exception; a flag field `low_confidence: bool` on `LLMResponse` (C014: confidence < 0.4)

**Auth Requirement**
- N/A — internal library, no HTTP endpoint

**Non-functional**
- No latency SLA at this story level
- Audit log: not required

**Implementation notes**
- Location: `backend/rag/llm/` — new subdirectory
- Keep `base.py` and `exceptions.py` free of provider-specific imports

---

### S002: Three provider adapters (Ollama, OpenAI, Claude)

**Role / Want / Value**
- As a: platform operator
- I want: three working LLM adapters behind a common interface
- So that: I can switch provider via `LLM_PROVIDER` env var without code changes

**Acceptance Criteria**
- [ ] AC1: `OllamaAdapter(LLMProvider)` in `backend/rag/llm/ollama.py` — calls Ollama REST API; reads `OLLAMA_BASE_URL` (default `http://localhost:11434`) and `LLM_MODEL` (default `llama3`)
- [ ] AC2: `OpenAIAdapter(LLMProvider)` in `backend/rag/llm/openai.py` — uses `openai` SDK; reads `OPENAI_API_KEY` and `LLM_MODEL` (default `gpt-4o-mini`)
- [ ] AC3: `ClaudeAdapter(LLMProvider)` in `backend/rag/llm/claude.py` — uses `anthropic` SDK; reads `ANTHROPIC_API_KEY` and `LLM_MODEL` (default `claude-haiku-4-5-20251001`)
- [ ] AC4: All adapters raise `LLMError` on provider failure (network error, auth error, rate limit) — never propagate raw SDK exceptions to callers
- [ ] AC5: No provider name, model name, or API key hardcoded in source — all via `os.getenv()` (SECURITY S005)
- [ ] AC6: Each adapter builds prompt from template: `backend/rag/llm/prompts/answer.txt` — reads file at startup, not per-request
- [ ] AC7: `confidence` in `LLMResponse` is populated from provider response where available (OpenAI/Claude logprobs or fixed 0.9 sentinel if unavailable); `low_confidence=True` when `confidence < 0.4`

**Auth Requirement**
- N/A — internal library

**Non-functional**
- Latency: OllamaAdapter < 5s p95 (local); OpenAI/Claude < 3s p95 (network — not enforced in unit tests, documented only)
- Audit log: not required at adapter level (logged at API route level)

**Implementation notes**
- `openai` and `anthropic` packages added to `requirements.txt`
- Ollama uses `httpx` (already in FastAPI stack) — no new dependency
- Prompt template path: `backend/rag/llm/prompts/answer.txt` — include `{context}` and `{question}` placeholders

---

### S003: LLMProviderFactory

**Role / Want / Value**
- As a: api-agent caller (`/v1/query` route)
- I want: `LLMProviderFactory.get() -> LLMProvider`
- So that: the query handler never imports concrete adapters; provider selection is fully config-driven

**Acceptance Criteria**
- [ ] AC1: `LLMProviderFactory.get()` reads `LLM_PROVIDER` env var; supported values: `"ollama"` (default), `"openai"`, `"claude"`
- [ ] AC2: `LLM_PROVIDER` not set → defaults to `"ollama"` (never raises; C015 default)
- [ ] AC3: `LLM_PROVIDER` set to unknown value → raises `LLMError("Unsupported provider: ...")` (C005 fail-fast)
- [ ] AC4: Factory returns a singleton per provider per process (same pattern as `TokenizerFactory`)
- [ ] AC5: `backend/rag/llm/__init__.py` exports: `LLMProvider`, `LLMResponse`, `LLMProviderFactory`, `LLMError`, `NoRelevantChunksError` — concrete adapters not in public API

**Auth Requirement**
- N/A

**Non-functional**
- Thread-safe singleton (same `threading.Lock` pattern as `TokenizerFactory`)

**Implementation notes**
- Location: `backend/rag/llm/factory.py`
- Use lazy import inside `_create()` (same pattern as tokenizer factory — defers SDK import cost)

---

### S004: LLM integration tests + answer-generation gate

**Role / Want / Value**
- As a: developer
- I want: full test coverage for all LLM provider paths including the no-chunks gate
- So that: C014 (cite source / no hallucination) regressions are caught before merge

**Acceptance Criteria**
- [ ] AC1: Unit tests for all 3 adapters using `unittest.mock` — no real API calls in CI
- [ ] AC2: `OllamaAdapter` test: mock `httpx.AsyncClient.post` — verify request body shape and response parsing
- [ ] AC3: `OpenAIAdapter` test: mock `openai.OpenAI.chat.completions.create`
- [ ] AC4: `ClaudeAdapter` test: mock `anthropic.Anthropic.messages.create`
- [ ] AC5: `NoRelevantChunksError` raised when `context_chunks=[]` — regression test for C014
- [ ] AC6: `low_confidence=True` when adapter returns `confidence < 0.4` — regression test for C014
- [ ] AC7: `LLMProviderFactory` tests: all 3 supported providers + unknown → `LLMError`; default `"ollama"` when env not set
- [ ] AC8: Test coverage ≥ 80% for all `backend/rag/llm/*.py`

**Non-functional**
- Tests run fully offline — all provider calls mocked
- No real API keys required in CI

**Implementation notes**
- Location: `tests/rag/test_llm_provider.py`
- Use `monkeypatch.setenv` for `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: LLMProvider ABC | Constitution | CONSTITUTION.md C015 | "LLM provider must be configurable via env var" | 2026-03-18 |
| AC2: LLMResponse dataclass | Business logic | Conversation lb_mui 2026-04-06 | Uniform output contract for all adapters | 2026-04-06 |
| AC3: LLMError | Constitution | CONSTITUTION.md P005 — fail fast | Distinct exception for observability | 2026-03-18 |
| AC4: NoRelevantChunksError | Constitution | CONSTITUTION.md C014 | "No answer generated if no relevant chunks found" | 2026-03-18 |
| AC5: LowConfidenceWarning flag | Constitution | CONSTITUTION.md C014 | "Confidence < 0.4 triggers low-confidence warning" | 2026-03-18 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: OllamaAdapter default | Constitution | CONSTITUTION.md C015 | "Default: ollama" — free/local first | 2026-03-18 |
| AC2: OpenAIAdapter | Constitution | CONSTITUTION.md C015 | "Supported: ollama, openai, claude" | 2026-03-18 |
| AC3: ClaudeAdapter | Constitution | CONSTITUTION.md C015 | "Supported: ollama, openai, claude" | 2026-03-18 |
| AC4: LLMError on failure | Constitution | CONSTITUTION.md P005 — fail fast | Wrap all SDK exceptions | 2026-03-18 |
| AC5: No hardcoded secrets | Security rule | SECURITY.md S005 | "Zero hardcoded secrets in source code" | 2026-03-18 |
| AC6: Prompt template file | Business logic | Conversation lb_mui 2026-04-06 | Decouple prompt text from code | 2026-04-06 |
| AC7: Confidence + low_confidence flag | Constitution | CONSTITUTION.md C014 | "confidence < 0.4 triggers low-confidence warning" | 2026-03-18 |

### S003 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: LLM_PROVIDER env var | Constitution | CONSTITUTION.md C015 | "configurable via env var (LLM_PROVIDER)" | 2026-03-18 |
| AC2: Default ollama | Constitution | CONSTITUTION.md C015 | "Default: ollama" | 2026-03-18 |
| AC3: Unknown provider → error | Constitution | CONSTITUTION.md P005 — fail fast | Unknown config must not silently fall back | 2026-03-18 |
| AC4: Singleton pattern | Business logic | Existing pattern — TokenizerFactory | Consistent with cjk-tokenizer D05 | 2026-04-06 |
| AC5: Clean public API | Business logic | Conversation lb_mui 2026-04-06 | Concrete adapters are implementation detail | 2026-04-06 |

### S004 Sources
| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1–AC4: Mock-based unit tests | Constitution | CONSTITUTION.md testing policy | "Backend unit test coverage ≥ 80%" | 2026-03-18 |
| AC5: NoRelevantChunks regression | Constitution | CONSTITUTION.md C014 | No hallucination without source — critical regression | 2026-03-18 |
| AC6: LowConfidence regression | Constitution | CONSTITUTION.md C014 | "confidence < 0.4 triggers low-confidence warning" | 2026-03-18 |
| AC7: Factory tests | Business logic | Existing pattern — TestTokenizerFactory | Same coverage pattern as cjk-tokenizer S004 | 2026-04-06 |
| AC8: ≥80% coverage | Constitution | CONSTITUTION.md testing policy | Standard coverage threshold | 2026-03-18 |

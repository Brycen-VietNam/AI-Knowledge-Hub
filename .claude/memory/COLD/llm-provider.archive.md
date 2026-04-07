---
name: llm-provider archive
description: Completed feature archive — multi-provider LLM adapter (ollama/openai/claude) for /v1/query answer generation
type: project
---

# COLD Archive: llm-provider
Created: 2026-04-06 | Status: DONE ✅ FINALIZED 2026-04-06 | Phase: /report ✅ — archived

---

## Spec Summary
Multi-provider LLM adapter for `/v1/query` answer generation.
Satisfies C014 (cite source, no hallucination) and C015 (LLM_PROVIDER env var).
Providers: Ollama (default/free/local), OpenAI, Claude.

**4 stories:** S001 (base + dataclasses) → S002 (3 adapters) → S003 (Factory) → S004 (tests)
**22 ACs | 0 open blockers**

---

## Key Decisions
- D01 (2026-04-06): Ollama as default provider — free/local, no API key needed for dev
- D02 (2026-04-06): Prompt template in file `backend/rag/llm/prompts/answer.txt` — decouple prompt from code
- D03 (2026-04-06): NoRelevantChunksError gates generation (C014) — no chunks = no answer, raise error
- D04 (2026-04-06): LowConfidence is a flag on LLMResponse (not exception) — caller decides how to surface
- D05 (2026-04-06): Singleton factory pattern — same as TokenizerFactory (D05 from cjk-tokenizer)
- D06 (2026-04-06): Confidence sentinel: OpenAI/Claude logprobs where available; fixed 0.9 if unavailable
- D07 (2026-04-06): OllamaAdapter MUST be async httpx.AsyncClient — spec A01 was wrong; retriever.py + query.py are fully async
- D08 (2026-04-06): generator.py service layer — `backend/rag/generator.py` wraps LLMProvider; api-agent calls generate_answer(), not LLMProviderFactory directly (ARCH A002)
- D09 (2026-04-06): NoRelevantChunksError → 200 + {"answer": null, "reason": "no_relevant_chunks"} — bot-friendly, no 4xx to handle
- D10 (2026-04-06): QueryResponse schema breaking change — replace results[] with answer + sources + low_confidence; consumers not in production so migration cost = 0

---

## Files to Create
```
NEW:
  backend/rag/llm/__init__.py
  backend/rag/llm/base.py             — LLMProvider ABC, LLMResponse dataclass
  backend/rag/llm/exceptions.py       — LLMError, NoRelevantChunksError
  backend/rag/llm/ollama.py           — OllamaAdapter (httpx)
  backend/rag/llm/openai.py           — OpenAIAdapter (openai SDK)
  backend/rag/llm/claude.py           — ClaudeAdapter (anthropic SDK)
  backend/rag/llm/factory.py          — LLMProviderFactory
  backend/rag/llm/prompts/answer.txt  — prompt template ({context}, {question})
  tests/rag/test_llm_provider.py      — TDD-first, all mocked

MODIFY:
  requirements.txt    — add: openai, anthropic
```

---

## Assumptions (confirm at /clarify)
> **A01**: `OllamaAdapter` uses synchronous `httpx` (not async) — consistent with current retriever.py pattern. Confirm or /clarify.
> **A02**: `ClaudeAdapter` uses `claude-haiku-4-5-20251001` as default model — matches CLAUDE.md model list. Confirm.
> **A03**: Prompt template uses `{context}` (joined chunk text) and `{question}` (raw user query). No i18n on prompt in this feature scope. Confirm.

---

## Status per Story
| Story | Status | Tasks file |
|---|---|---|
| S001 — Base interface + dataclasses | TASKED | docs/llm-provider/tasks/S001.tasks.md |
| S002 — Three adapters | TASKED | docs/llm-provider/tasks/S002.tasks.md |
| S003 — LLMProviderFactory | TASKED | docs/llm-provider/tasks/S003.tasks.md |
| S004 — Tests + coverage gate | TASKED | docs/llm-provider/tasks/S004.tasks.md |
| Post-G3 — generator.py + query.py | TASKED | docs/llm-provider/tasks/S005-query-integration.tasks.md |

## Task Board
| Task | Story | Parallel | Status |
|------|-------|----------|--------|
| T001 — exceptions.py | S001 | safe | DONE ✅ |
| T002 — base.py | S001 | after:T001 | DONE ✅ |
| T003 — __init__.py stub | S001 | after:T001 | DONE ✅ |
| T004 — TestLLMBase complete | S001 | after:T002 | DONE ✅ |
| T005 — prompts/answer.txt + requirements.txt | S002 | safe | DONE ✅ |
| T006 — ollama.py | S002 | after:T005 | DONE ✅ |
| T007 — openai.py | S002 | after:T005 | DONE ✅ |
| T008 — claude.py | S002 | after:T005 | DONE ✅ |
| T009 — factory.py | S003 | safe (∥ T011) | DONE ✅ |
| T010 — __init__.py exports | S003 | after:T009 | DONE ✅ |
| T011 — TestAnswerGate (C014) | S004 | safe (∥ T009) | DONE ✅ |
| T012 — Coverage sweep ≥80% | S004 | after:T011 | DONE ✅ 100% |
| T013 — generator.py | Post-G3 | after S003 | DONE ✅ |
| T014 — query.py update | Post-G3 | after:T013 | DONE ✅ |

---

## Phase Tracker
- [x] /specify ✅ 2026-04-06
- [x] /clarify ✅ 2026-04-06 — 3 BLOCKERs RESOLVED (D08/D09/D10), D07 correction, UNBLOCKED
- [x] /checklist ✅ 2026-04-06 — 30/30 PASS, WARN-1 resolved (caching strategy in spec)
- [x] /plan ✅ 2026-04-06 — 4 stories, 2 sessions, G3 parallel (S003∥S004), plan: docs/llm-provider/plan/llm-provider.plan.md
- [x] /tasks ✅ 2026-04-06 — 14 tasks across 5 files (S001–S004 + Post-G3)
- [x] /analyze ✅ 2026-04-06 — 3 gaps found; T014 TOUCH correction; request_id retained in QueryResponse
- [x] /implement ✅ 2026-04-06 — 14 tasks DONE, 100% coverage, 169 pass
- [x] /reviewcode ✅ 2026-04-06 — APPROVED (post-fix: B001+W001–W004 all resolved)
- [ ] /report

---

## Sync: 2026-04-06 (Session #018)
Decisions added: D11 (T014 TOUCH correction), D12 (QueryResponse retains request_id)
Tasks changed: all 14 → status confirmed TODO, analysis complete
Files touched (docs only — no src yet):
  - docs/llm-provider/reviews/checklist.md (CREATED + updated PASS)
  - docs/llm-provider/plan/llm-provider.plan.md (CREATED)
  - docs/llm-provider/tasks/S001.tasks.md (CREATED)
  - docs/llm-provider/tasks/S002.tasks.md (CREATED)
  - docs/llm-provider/tasks/S003.tasks.md (CREATED)
  - docs/llm-provider/tasks/S004.tasks.md (CREATED)
  - docs/llm-provider/tasks/S005-query-integration.tasks.md (CREATED)
  - docs/llm-provider/tasks/all-stories.analysis.md (CREATED)
  - docs/llm-provider/spec/llm-provider.spec.md (MODIFIED — prompt caching row added)
Questions resolved: WARN-1 (prompt caching strategy), T014 TOUCH gap, request_id retention
New blockers: none
Analysis corrections to carry into /implement:
  - T014: CREATE tests/api/test_query_route.py + MODIFY tests/api/test_query_rbac.py L85,103,119,133
  - QueryResponse: request_id: str + answer + sources + low_confidence + reason
  - OllamaAdapter: async httpx.AsyncClient (never sync)

## Sync: 2026-04-06 (Session #019)
Decisions added: none new (D01–D12 already recorded)
Tasks changed: T001–T014 → all DONE ✅
Files touched (src):
  - backend/rag/llm/__init__.py (CREATED — public exports)
  - backend/rag/llm/base.py (CREATED — LLMResponse dataclass + LLMProvider ABC)
  - backend/rag/llm/exceptions.py (CREATED — LLMError, NoRelevantChunksError)
  - backend/rag/llm/ollama.py (CREATED — async httpx, D07)
  - backend/rag/llm/openai.py (CREATED — lazy import openai SDK)
  - backend/rag/llm/claude.py (CREATED — lazy import anthropic SDK, default haiku)
  - backend/rag/llm/factory.py (CREATED — singleton double-checked lock, D05)
  - backend/rag/llm/prompts/answer.txt (CREATED — {context}/{question} template)
  - backend/rag/llm/prompts/__init__.py (CREATED — empty package)
  - backend/rag/generator.py (CREATED — generate_answer() service layer, D08)
  - backend/api/routes/query.py (MODIFIED — D10 QueryResponse + D09 null-answer + D08 generate_answer wiring)
  - requirements.txt (MODIFIED — openai>=1.0.0, anthropic>=0.20.0)
  - tests/rag/test_llm_provider.py (CREATED — 33 tests, 100% coverage)
  - tests/rag/test_generator.py (CREATED — 2 tests)
  - tests/api/test_query_route.py (CREATED — 3 LLM-path tests)
  - tests/api/test_query_rbac.py (MODIFIED — 4 assertions updated D10, generate_answer patches)
Questions resolved: all /analyze corrections applied
New blockers: none
Coverage: 100% on backend/rag/llm/*.py | 169 pass, 0 fail (new)

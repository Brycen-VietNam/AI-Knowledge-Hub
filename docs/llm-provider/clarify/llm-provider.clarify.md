# Clarify: llm-provider
Generated: 2026-04-06 | Spec: docs/llm-provider/spec/llm-provider.spec.md

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | Where in the query pipeline does LLM generation happen? After `retrieve()` returns chunks, does `/v1/query` call `LLMProvider.complete()` directly, or is there a separate service layer? | **Option B** — `backend/rag/generator.py` service layer; api-agent calls `generate_answer(query, chunks)` | ✅ lb_mui | 2026-04-06 |
| Q2 | Should `/v1/query` return an error (4xx) when `NoRelevantChunksError` is raised, or return 200 with `{"answer": null, "reason": "no_relevant_chunks"}`? | **Option A** — 200 + `{"answer": null, "reason": "no_relevant_chunks"}` | ✅ lb_mui | 2026-04-06 |
| Q3 | What does the query route response schema look like after adding LLM generation? Currently it returns `list[RetrievedDocument]` — does this change to `{"answer": str, "sources": [...], "confidence": float}`? | **Option A** — breaking change: replace `results[]` with `answer + sources + low_confidence`. Consumers not yet in production — migration cost = 0 | ✅ lb_mui | 2026-04-06 |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q4 | `OllamaAdapter` — sync or async httpx? | **ASSUME: async `httpx.AsyncClient`** — query.py is fully async; sync adapter would block the event loop. Auto-answered from `backend/rag/retriever.py` and `backend/api/routes/query.py` (both use `async/await` throughout). A01 in spec was WRONG. |
| Q5 | `ClaudeAdapter` default model — `claude-haiku-4-5-20251001`? | **ASSUME: YES** — matches CLAUDE.md model list "Haiku 4.5: claude-haiku-4-5-20251001"; cheapest/fastest for answer generation. |
| Q6 | Prompt template language — English only in this scope? | **ASSUME: YES** — A03 confirmed; i18n on prompts is deferred to `multilingual-rag-pipeline`. Prompt template uses `{context}` (joined chunk text, newline-separated) and `{question}` (raw user query string). |
| Q7 | `LLMResponse.confidence` when provider doesn't return logprobs (e.g. Ollama)? | **ASSUME: sentinel 0.9** — D06 in WARM. Fixed value meaning "model responded, no confidence data available". |
| Q8 | Should `openai` and `anthropic` packages be optional dependencies (lazy import in adapter) or required in requirements.txt? | **ASSUME: required in requirements.txt** — simpler; all adapters installed even if unused. Lazy import still used in factory._create() to defer SDK initialization cost. |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q9 | Should `LLMResponse` include a `latency_ms` field for observability? |
| Q10 | Should the prompt template support per-language variants (`answer_ja.txt`, `answer_vi.txt`)? |
| Q11 | Retry logic on provider failure (e.g. 1 retry on 429 rate limit)? |

---

## Auto-answered from existing files

| Question | Source | Answer |
|----------|--------|--------|
| A01 (spec): OllamaAdapter sync vs async | `backend/rag/retriever.py:8,32` + `backend/api/routes/query.py:11,92` | **ASYNC required** — entire stack is async; sync httpx would block event loop. Spec A01 assumption was incorrect. Fix in /plan: OllamaAdapter must use `async httpx.AsyncClient`. |
| A02 (spec): ClaudeAdapter default model | `CLAUDE.md` model table — "Haiku 4.5: claude-haiku-4-5-20251001" | Confirmed `claude-haiku-4-5-20251001` |
| C015 constraint | `CONSTITUTION.md C015` | Provider must be configurable via `LLM_PROVIDER`. Supported: ollama, openai, claude. Default: ollama. Never hardcode. |
| C014 constraint | `CONSTITUTION.md C014` | Answer must cite ≥1 source. No answer if no chunks. Confidence < 0.4 → low-confidence flag. |
| S005 security | `SECURITY.md S005` | Zero hardcoded secrets — all via os.getenv() |
| P007 memory | `CONSTITUTION.md P007` | Lazy import in factory._create() — don't load all 3 SDKs at startup |

---

## Summary

```
BLOCKERs:      3 — ALL RESOLVED ✅ (Q1/Q2/Q3 answered by lb_mui 2026-04-06)
SHOULD:        5 (Q4–Q8 — auto-assumed)
NICE:          3 (Q9–Q11 — deferred)
Auto-answered: 6 (from retriever.py, query.py, CONSTITUTION.md, CLAUDE.md)
Corrections:   1 (A01 WRONG → OllamaAdapter must be async httpx.AsyncClient)

Status: UNBLOCKED — ready for /checklist
```

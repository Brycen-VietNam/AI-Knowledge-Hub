# Clarify: query-endpoint
Generated: 2026-04-08 | Spec: v1 DRAFT | Stories: S001–S005

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | `lang` override — request body field or header? | ✅ Body field: `"lang": "ja"` in request JSON — confirmed lb_mui 2026-04-08 | PO | ✅ DONE |
| Q2 | LLM timeout budget split — how much of the 1.8s pipeline budget is reserved for `generate_answer()`? | ✅ retrieval 1.0s / LLM 0.8s — confirmed lb_mui 2026-04-08 | PO | ✅ DONE |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q3 | `VALKEY_URL` env var — new var not in existing config. What is the default for local dev? | `VALKEY_URL=valkey://localhost:6379` (pattern matches `OLLAMA_BASE_URL` / `DATABASE_URL`) |
| Q4 | Should `X-RateLimit-Remaining` / `X-RateLimit-Reset` headers be returned on 429 responses as well as 200 responses? | Yes — include on all `/v1/query` responses including 429 (RFC 6585 standard) |
| Q5 | `top_k` default value — spec says optional with range 1–100, but what is the default if omitted? | Default = 10 (matches spec example body; consistent with `retriever.py` convention) |
| Q6 | Should `lang` field accept ISO 639-1 codes only (`ja`, `en`, `vi`, `ko`, `zh`) or any string? | ISO 639-1 subset: `ja`, `en`, `vi`, `ko`, `zh` only. Unknown value → 422 `LANG_UNSUPPORTED` |
| Q7 | Audit log target for 0-result queries — log required even when `search()` returns empty list? | Yes — S001 AC8 specifies "even 0-result" retrieval must log (R006) |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q8 | Should `reason` field in QueryResponse also support `"llm_disabled"` as a value (already in stub)? Current spec only mentions `"no_relevant_chunks"`. |
| Q9 | Rate limiter reuse for `/v1/documents` (20 req/min) — should S003 middleware be wired to `/v1/documents` in the same PR or deferred? |
| Q10 | Should `/v1/metrics` emit per-language latency breakdowns or aggregate only? |

---

## Auto-answered from existing files

| # | Question | Answer | Source |
|---|----------|--------|--------|
| Q-A1 | RBAC filter location — WHERE clause or Python post-filter? | WHERE clause at pgvector level (never Python) | HARD.md R001, CONSTITUTION C001 |
| Q-A2 | RBAC for 0-group users — 403 or public results? | Public-only results (not 403) | Decision D04 (WARM), S001 AC7 |
| Q-A3 | Hybrid search weights — configurable or hardcoded? | Configurable: `RAG_BM25_WEIGHT`=0.3, `RAG_DENSE_WEIGHT`=0.7 | ARCH.md A004, CONSTITUTION C007 |
| Q-A4 | Rate limiting backend — Valkey or Redis? | Valkey (BSD-3). Redis ≥7.4 RSALv2 **forbidden** | CONSTITUTION C016, S003 AC3 |
| Q-A5 | Rate limit: fixed bucket or sliding window? | Sliding window required | SECURITY.md S004, S003 AC2 |
| Q-A6 | Auth on `/v1/query` — required? | Yes. Both OIDC Bearer and API-Key. `/v1/health` is only anonymous route | HARD.md R003, CONSTITUTION C003 |
| Q-A7 | Confidence threshold for `low_confidence` flag? | < 0.4 → `low_confidence=True` | CONSTITUTION C014, S002 AC4 |
| Q-A8 | `sources` field in response — content or doc_id? | `doc_id` strings only. Raw content/PII forbidden | HARD.md R002, CONSTITUTION C002 |
| Q-A9 | LLM provider — hardcoded or configurable? | Configurable via `LLM_PROVIDER` env var. Default: ollama | CONSTITUTION C015 |
| Q-A10 | LLM timeout env var — does it exist? | Yes: `LLM_TIMEOUT_S` in `backend/rag/llm/ollama.py:23` (default 5.0s) — note: this is the provider-level timeout, separate from pipeline budget |
| Q-A11 | `NoRelevantChunksError` → what HTTP status? | 200 with `{answer: null, reason: "no_relevant_chunks"}` (not 4xx/5xx) | Decision D09 (WARM), S002 AC5 |
| Q-A12 | Query max length enforcement — where? | 512 chars on `QueryRequest` Pydantic validator → HTTP 400 | SECURITY.md S003, S004 AC3 |
| Q-A13 | `request_id` — generated or inherited? | Generated: `str(uuid4())` already in query.py stub | S004 AC6 |
| Q-A14 | `generate_answer()` signature | `async def generate_answer(query: str, chunks: list[str]) -> LLMResponse` | `backend/rag/generator.py:7` |
| Q-A15 | Language auto-detection — which library? | `backend/rag/tokenizers/detection.py` (per multilingual-rag-pipeline feature) | WARM query-endpoint, ARCH A003 |

---

## Assumptions (proceed unless PO overrides)

| ID | Assumption | Impact if wrong |
|----|------------|-----------------|
| A1 | ✅ CONFIRMED: `lang` override is in request body as `"lang": "ja"` (not a header) — lb_mui 2026-04-08 | — |
| A2 | ✅ CONFIRMED: Timeout budget: `search()` = 1.0s, `generate_answer()` = 0.8s, total ≤ 1.8s — lb_mui 2026-04-08 | — |
| A3 | `VALKEY_URL` is a new env var — not defined in any existing config file | If already defined elsewhere: check for conflicts and reuse the existing var name |

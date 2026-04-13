# Spec: query-endpoint
Created: 2026-04-08 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary

| Field | Value |
|-------|-------|
| Epic | rag-pipeline |
| Priority | P0 |
| Story count | 5 |
| Token budget est. | ~5k |
| Critical path | S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S003 (metrics), S004 (error handling) can parallelize after S002 |
| Blocking specs | None |
| Blocked by | auth-api-key-oidc ✅, rbac-document-filter ✅, multilingual-rag-pipeline ✅, llm-provider ✅ |
| Agents needed | api-agent |

### Problem Statement
The `/v1/query` route exists as a stub: it embeds queries directly via OllamaEmbedder,
bypasses the unified `search()` service, and does not call `generate_answer()`.
Users cannot get AI answers — only raw chunk content is returned, and language detection is missing.

### Solution Summary
- Replace stub embed/retrieve calls with `search()` from `backend/rag/search.py`
- Wire `generate_answer()` to produce structured answers with source citations
- Add rate limiting (60 req/min per user) via Valkey middleware
- Emit `/v1/metrics` endpoint for query latency + error rate observability
- Full integration test suite covering RBAC, multilingual queries, timeout, and LLM error paths

### Out of Scope
- Streaming responses (future feature)
- Query history / conversation memory
- Frontend SPA changes
- Bot adapter changes (bots already consume `/v1/query`)

---

## LAYER 2 — Story Detail

---

### S001: Wire search() into POST /v1/query

**Role / Want / Value**
- As a: bot or SPA user
- I want: `/v1/query` to use the full hybrid RAG pipeline (language detection → tokenize → embed → retrieve)
- So that: multilingual queries return ranked, RBAC-filtered results via the unified search service

**Acceptance Criteria**
- [ ] AC1: `POST /v1/query` calls `search(query, user_group_ids, session, top_k, lang=None)` — replaces inline `embed()` + `retrieve()` stub
- [ ] AC2: `lang` override is accepted as optional request body field (default: None → auto-detect)
- [ ] AC3: `LanguageDetectionError` → HTTP 422 `{"error": {"code": "LANG_DETECT_FAILED", ...}}`
- [ ] AC4: `UnsupportedLanguageError` → HTTP 422 `{"error": {"code": "LANG_UNSUPPORTED", ...}}`
- [ ] AC5: `EmbedderError` → HTTP 503 `{"error": {"code": "EMBEDDER_UNAVAILABLE", ...}}`
- [ ] AC6: `QueryTimeoutError` / `asyncio.TimeoutError` → HTTP 504 `QUERY_TIMEOUT` (already exists — must not regress)
- [ ] AC7: RBAC: 0-group users receive public-only results (not 403) — must not regress from D04
- [ ] AC8: Audit log written as background task for every retrieval (even 0-result) — R006

**API Contract**
```
POST /v1/query
Headers: Authorization: Bearer <token> | X-API-Key: <key>
Body: {
  "query": "string (max 512 chars)",
  "top_k": 10,          // optional, 1–100
  "lang": "ja"          // optional, null = auto-detect
}
Response 200: QueryResponse (see S002)
Response 422: {"error": {"code": "LANG_DETECT_FAILED|LANG_UNSUPPORTED|VALIDATION_ERROR", "message": "...", "request_id": "..."}}
Response 503: {"error": {"code": "EMBEDDER_UNAVAILABLE", "message": "...", "request_id": "..."}}
Response 504: {"error": {"code": "QUERY_TIMEOUT", "message": "...", "request_id": "..."}}
```

**RAG Behavior**
- Retrieval: hybrid (0.7 dense + 0.3 BM25) via `search()`
- RBAC: filter on user_group_id (at WHERE clause — R001, not here)
- Languages: ja / en / vi / ko / zh — auto-detected unless `lang` provided
- Fallback: BM25-only if dense > 500ms (inside retriever — not query route concern)

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)  [x] Both

**Non-functional**
- Latency: < 2s p95 (R007 / P001) — `asyncio.wait_for(timeout=1.8)` wraps `search()`
- Audit log: required (R006)
- CJK support: ja / zh / vi / ko

**Implementation notes**
- Remove the `embed()` helper function (lines 57–64 in query.py) — now handled by `search()`
- `search()` is in `backend/rag/search.py` — import it (A002: api → rag is allowed)
- Add `lang: str | None = None` to `QueryRequest` model
- The `asyncio.wait_for` wrapper must wrap the entire `search()` call

---

### S002: Wire generate_answer() for AI responses

**Role / Want / Value**
- As a: user
- I want: AI-generated answers with source citations in the query response
- So that: I receive a natural language answer, not raw document chunks

**Acceptance Criteria**
- [ ] AC1: When `docs` is non-empty, call `generate_answer(query, [d.content for d in docs])` and populate `answer` field
- [ ] AC2: `QueryResponse.answer` is non-null string when LLM succeeds
- [ ] AC3: `QueryResponse.sources` contains `doc_id` strings (not raw content) — A005-compliant, no PII (R002)
- [ ] AC4: `QueryResponse.low_confidence` = True when LLM returns `confidence < 0.4` (C014)
- [ ] AC5: `NoRelevantChunksError` from `generate_answer()` → 200 `{answer: null, reason: "no_relevant_chunks"}` (D09)
- [ ] AC6: LLM provider unavailable → HTTP 503 `{"error": {"code": "LLM_UNAVAILABLE", ...}}`
- [ ] AC7: At least 1 source document cited — no answer generated if 0 relevant chunks (C014)
- [ ] AC8: `reason` field populated only when `answer` is null (D09)

**API Contract**
```
POST /v1/query
Response 200: {
  "request_id": "uuid",
  "answer": "string | null",
  "sources": ["doc_id_1", "doc_id_2"],
  "low_confidence": false,
  "reason": null | "no_relevant_chunks" | "llm_disabled"
}
Response 503: {"error": {"code": "LLM_UNAVAILABLE", "message": "...", "request_id": "..."}}
```

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)  [x] Both

**Non-functional**
- Latency: total p95 < 2s including LLM generation (P001)
- LLM timeout: separate timeout for generate_answer() — recommended 1.5s budget after retrieval
- CJK support: response language matches detected query language (C009 / A003)

**Implementation notes**
- `generate_answer()` is in `backend/rag/generator.py` — already imported in current stub
- `LLMResponse` has `.answer: str`, `.confidence: float`, `.sources: list[str]`
- Check `LLMResponse.confidence` against 0.4 threshold for `low_confidence` flag
- `sources` in response = `doc_id` list from `RetrievedDocument.doc_id`, not `.content`
- Wrap `generate_answer()` with `asyncio.wait_for` using remaining budget after retrieval

---

### S003: Rate limiting — 60 req/min per user

**Role / Want / Value**
- As a: platform operator
- I want: `/v1/query` rate-limited to 60 req/min per user_id / sub claim
- So that: no single user can overload the RAG pipeline or LLM provider

**Acceptance Criteria**
- [ ] AC1: Requests beyond 60/min per user_id return HTTP 429 `{"error": {"code": "RATE_LIMIT_EXCEEDED", ...}}`
- [ ] AC2: Rate limit uses sliding window (not fixed bucket) — S004 in SECURITY.md
- [ ] AC3: Backend is Valkey (BSD-3) — Redis ≥7.4 (RSALv2) is forbidden (C016)
- [ ] AC4: Rate limit key = `ratelimit:query:{user_id}` (API-key) or `ratelimit:query:{sub}` (OIDC)
- [ ] AC5: Rate limit middleware is reusable — parametric `resource` + `limit` + `window`
- [ ] AC6: When Valkey is unavailable, fail open (allow request, log warning) — not fail closed
- [ ] AC7: `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers returned on all `/v1/query` responses

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)  [x] Both

**Non-functional**
- Valkey connection pooled at startup — not per-request (P005 analog for cache)
- Rate limit check adds < 5ms overhead

**Implementation notes**
- New file: `backend/api/middleware/rate_limiter.py`
- Use `fastapi_limiter` or custom sliding window via Valkey ZADD/ZCOUNT
- `AuthenticatedUser.user_id` is the rate limit key (available post-`verify_token`)
- Valkey URL from `VALKEY_URL` env var

---

### S004: Structured error handling & observability

**Role / Want / Value**
- As a: developer or operator
- I want: all query errors to return consistent error shapes with request_id
- So that: debugging across languages and timezones is clear (P005)

**Acceptance Criteria**
- [ ] AC1: All error responses follow `{"error": {"code": "...", "message": "...", "request_id": "..."}}` (A005)
- [ ] AC2: No stack traces or internal paths exposed in production responses (A005)
- [ ] AC3: HTTP 400 for `query` length > 512 chars or `top_k` out of 1–100 range
- [ ] AC4: HTTP 401 for missing/invalid auth — unchanged from auth feature, must not regress
- [ ] AC5: HTTP 403 not returned for 0-group users — they get public results (D04), must not regress
- [ ] AC6: `request_id` is present in all responses (success and error) for traceability

**Auth Requirement**
- [x] OIDC Bearer (human)  [x] API-Key (bot)  [x] Both

**Non-functional**
- Error handler wired to FastAPI exception handlers (not inline try/except per route)

**Implementation notes**
- Add `@app.exception_handler` entries in `backend/api/app.py` for custom exceptions
- `LanguageDetectionError`, `UnsupportedLanguageError`, `EmbedderError`, `QueryTimeoutError` all need handlers
- Reuse `auth_error()` pattern from `backend/auth/_errors.py` for consistent shape

---

### S005: Integration tests — query endpoint full coverage

**Role / Want / Value**
- As a: developer
- I want: integration tests covering the complete query flow
- So that: regressions in RBAC, auth, multilingual, or LLM paths are caught before merge

**Acceptance Criteria**
- [ ] AC1: Test: happy path — authenticated user, multilingual query (ja/en/vi/ko), returns answer + sources
- [ ] AC2: Test: RBAC — user_group_ids filter isolates results (no cross-group leakage)
- [ ] AC3: Test: 0-group user → public-only results, not 403
- [ ] AC4: Test: unauthenticated request → 401
- [ ] AC5: Test: query > 512 chars → 400
- [ ] AC6: Test: retrieval timeout → 504
- [ ] AC7: Test: LLM unavailable → 503
- [ ] AC8: Test: no relevant chunks → 200 `{answer: null, reason: "no_relevant_chunks"}`
- [ ] AC9: Test: low_confidence flag set when LLM confidence < 0.4
- [ ] AC10: Test: rate limit exceeded → 429
- [ ] AC11: Test: `lang` override accepted and bypasses auto-detection
- [ ] AC12: Coverage ≥ 80% for `backend/api/routes/query.py` and new middleware

**Non-functional**
- Tests in `backend/tests/api/test_query.py`
- Mock `search()` and `generate_answer()` at the service boundary — no real Valkey/DB required for unit tests
- Integration tests hit real DB via test fixtures (per auth-feature test pattern)

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Existing behavior | `backend/rag/search.py` — `search()` signature | 2026-04-08 |
| AC2 | Business logic | D4 decision (HOT.md) — `lang: str\|None = None` | 2026-04-08 |
| AC3 | Constitution | C009 — auto-detect, never hardcode lang | 2026-04-08 |
| AC4 | Constitution | C009 + ARCH A003 | 2026-04-08 |
| AC5 | Existing behavior | `backend/rag/embedder.py` — `EmbedderError` | 2026-04-08 |
| AC6 | Existing behavior | `backend/api/routes/query.py` — timeout handler already present | 2026-04-08 |
| AC7 | Existing behavior | D04 decision (rbac-document-filter feature) | 2026-04-08 |
| AC8 | HARD.md R006 | Audit log on every retrieval | 2026-04-08 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Existing behavior | `backend/rag/generator.py` — `generate_answer()` | 2026-04-08 |
| AC2 | Existing behavior | `backend/api/routes/query.py` stub — `reason: "llm_disabled"` | 2026-04-08 |
| AC3 | HARD.md R002 | No PII in vector metadata; doc_id is safe | 2026-04-08 |
| AC4 | Constitution C014 | Confidence < 0.4 → low-confidence warning | 2026-04-08 |
| AC5 | Existing behavior | D09 decision — NoRelevantChunksError → 200 null answer | 2026-04-08 |
| AC6 | Constitution P005 | Fail fast, fail visibly | 2026-04-08 |
| AC7 | Constitution C014 | ≥1 source required; no answer if 0 chunks | 2026-04-08 |
| AC8 | Existing behavior | `QueryResponse.reason` field (D09/D10) | 2026-04-08 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | SECURITY.md S004 | 60 req/min for /v1/query | 2026-04-08 |
| AC2 | SECURITY.md S004 | Sliding window specified | 2026-04-08 |
| AC3 | Constitution C016 | Valkey BSD-3; Redis ≥7.4 forbidden | 2026-04-08 |
| AC4 | Business logic | Per-user key pattern (user_id or sub claim) | 2026-04-08 |
| AC5 | Business logic | Reusability across /v1/documents (20/min) | 2026-04-08 |
| AC6 | Business logic | Fail-open preferred — platform availability over strict limiting | 2026-04-08 |
| AC7 | Business logic | Standard rate-limit response headers (RFC 6585) | 2026-04-08 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | ARCH.md A005 | Error response shape standard | 2026-04-08 |
| AC2 | ARCH.md A005 | No stack traces in prod | 2026-04-08 |
| AC3 | Existing behavior | `QueryRequest` Pydantic validators | 2026-04-08 |
| AC4 | Existing behavior | auth-api-key-oidc feature — must not regress | 2026-04-08 |
| AC5 | Existing behavior | D04 — 0-group users get public results | 2026-04-08 |
| AC6 | Existing behavior | `request_id = str(uuid4())` in current query.py | 2026-04-08 |

### S005 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC11 | Constitution | Testing conventions — ≥80% coverage, integration required | 2026-04-08 |
| AC12 | Constitution | Unit test coverage ≥ 80% for new code | 2026-04-08 |

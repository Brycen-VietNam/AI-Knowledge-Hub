# Plan: query-endpoint
Created: 2026-04-08 | Based on spec: v1 | Checklist: PASS (30/31, W01 approved)

---

## LAYER 1 — Plan Summary
> Load this section for sprint planning and status reviews.

| Field | Value |
|-------|-------|
| Total stories | 5 |
| Sessions estimated | 2 |
| Critical path | S001 → S002 → S003 + S004 (parallel) → S005 |
| Token budget total | ~5k tokens |

### Parallel Execution Groups
```
G1 (start immediately, sequential):
  S001 — api-agent   — Wire search() into POST /v1/query

G2 (after S001 complete):
  S002 — api-agent   — Wire generate_answer() for AI responses

G3 (after S002, run together — parallel-safe, touch different files):
  S003 — api-agent   — Rate limiting (new file: middleware/rate_limiter.py)
  S004 — api-agent   — Structured error handling (touches app.py only)

G4 (after G3 complete):
  S005 — api-agent   — Integration tests — full coverage
```

### Agent Assignments
| Agent | Stories | Can start |
|-------|---------|-----------|
| api-agent | S001, S002, S003, S004, S005 | S001 immediately; S002 after S001; S003+S004 after S002; S005 after G3 |

### Parallel Safety Analysis
- S003 + S004 are **parallel-safe**: S003 creates new file `middleware/rate_limiter.py`; S004 modifies `backend/api/app.py` exception handlers only — zero file overlap.
- S001 and S002 are **sequential**: S002 builds on the `QueryResponse` shape and `docs` list produced by S001.
- S005 must be **last**: tests cover all stories, requires their code to be merged.

### Risk
| Risk | Mitigation |
|------|------------|
| Valkey not available in test env | Mock Valkey client in S005 unit tests; use real Valkey only for integration layer |
| LLM timeout budget split (1.0s retrieval / 0.8s LLM) | Enforce with two nested `asyncio.wait_for` calls in S002 |
| `sources` PII leak (current bug) | S001 must patch `[str(d.doc_id) for d in docs]` before S002 builds on it — fix is on critical path |
| Valkey VALKEY_URL not in env config | S003 must add to `backend/api/config.py` (or equivalent) as new env var |

---

## LAYER 2 — Story Plans
> Load one story at a time during /tasks phase.

---

### S001: Wire search() into POST /v1/query
**Agent**: api-agent
**Parallel group**: G1
**Depends on**: none

**Files**
| Action | Path |
|--------|------|
| MODIFY | `backend/api/routes/query.py` |
| MODIFY | `backend/api/schemas.py` (or wherever `QueryRequest` is defined — add `lang: str \| None = None`) |

**Subagent dispatch**: YES (self-contained, no downstream code yet)
**Est. tokens**: ~1.5k
**Test entry**: `pytest backend/tests/api/test_query.py -k "search"` (pre-existing or scaffold)

**Story-specific notes**
- Remove `embed()` helper (lines 57–64 in `query.py`) — this bypass must go before any other S001 change
- Replace inline `embed()` + `retrieve()` stub with `from backend.rag.search import search`
- Wrap entire `search()` call with `asyncio.wait_for(timeout=1.0)` for retrieval budget
- Fix PII bug: change `sources=[d.content for d in docs]` → `sources=[str(d.doc_id) for d in docs]` — R002 compliance, critical path
- Add `lang: str | None = None` to `QueryRequest` — D4 decision (body field, not header — A1 confirmed)
- `asyncio.TimeoutError` → `QueryTimeoutError` propagation must not regress (AC6)
- RBAC: 0-group users must receive public results, not 403 (AC7 — D04 regression guard)
- Audit log written as `BackgroundTask` (AC8 — R006)

**Outputs expected**
- [ ] `query.py` calls `search()` — no inline `embed()` or `retrieve()`
- [ ] `QueryRequest` has `lang: str | None = None` field
- [ ] `sources` in response = `doc_id` list (not content)
- [ ] `asyncio.wait_for(search(...), timeout=1.0)` in place
- [ ] Audit log `BackgroundTask` present
- [ ] Tests: AC1–AC8 covered

---

### S002: Wire generate_answer() for AI responses
**Agent**: api-agent
**Parallel group**: G2
**Depends on**: S001

**Files**
| Action | Path |
|--------|------|
| MODIFY | `backend/api/routes/query.py` |

**Subagent dispatch**: YES (isolated to query.py changes only)
**Est. tokens**: ~1k
**Test entry**: `pytest backend/tests/api/test_query.py -k "answer"` (scaffold or extend)

**Story-specific notes**
- `generate_answer()` is in `backend/rag/generator.py` — already imported in stub
- Call only when `docs` is non-empty (AC7: no answer if 0 chunks)
- Wrap `generate_answer()` with `asyncio.wait_for(timeout=0.8)` — LLM budget after retrieval (A2 confirmed)
- `LLMResponse` fields: `.answer: str`, `.confidence: float`, `.sources: list[str]`
- Set `low_confidence = (response.confidence < 0.4)` (C014)
- `NoRelevantChunksError` → 200 with `{answer: null, reason: "no_relevant_chunks"}` — NOT an error response (D09)
- `QueryResponse.sources` = `doc_id` list from `RetrievedDocument.doc_id` (already fixed in S001)
- `reason` field populated only when `answer` is null (AC8)
- LLM provider unavailable → HTTP 503 `LLM_UNAVAILABLE` (AC6)

**Outputs expected**
- [ ] `generate_answer()` called when `docs` non-empty
- [ ] `QueryResponse.answer` non-null on LLM success
- [ ] `low_confidence` flag set correctly
- [ ] `NoRelevantChunksError` handled as 200 null answer
- [ ] `asyncio.wait_for(generate_answer(...), timeout=0.8)` in place
- [ ] Tests: AC1–AC8 covered

---

### S003: Rate limiting — 60 req/min per user
**Agent**: api-agent
**Parallel group**: G3 (parallel with S004)
**Depends on**: S002

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/api/middleware/rate_limiter.py` |
| MODIFY | `backend/api/app.py` (register middleware) |
| MODIFY | `backend/api/config.py` (add `VALKEY_URL` env var) |

**Subagent dispatch**: YES (new file only — no overlap with S004)
**Est. tokens**: ~1k
**Test entry**: `pytest backend/tests/api/test_rate_limiter.py`

**Story-specific notes**
- Use Valkey (BSD-3 licensed) — Redis ≥7.4 is forbidden (C016 / AC3)
- Sliding window via `ZADD` / `ZCOUNT` on Valkey — not fixed bucket (AC2)
- Rate limit key: `ratelimit:query:{user_id}` (API-key) or `ratelimit:query:{sub}` (OIDC) — (AC4)
- `AuthenticatedUser.user_id` is available post-`verify_token` dependency
- Middleware must be **parametric**: `resource: str`, `limit: int`, `window: int` — reusable for `/v1/documents` (AC5)
- Fail-open when Valkey unavailable: log warning, allow request — not fail-closed (AC6)
- Return `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers on all `/v1/query` responses (AC7)
- Pool Valkey connection at app startup — not per-request (VALKEY_URL from env)

**Outputs expected**
- [ ] `rate_limiter.py` — parametric sliding window, Valkey-backed
- [ ] Registered in `app.py`
- [ ] `VALKEY_URL` in config
- [ ] Fail-open behavior tested
- [ ] `X-RateLimit-*` headers present on responses
- [ ] Tests: AC1–AC7 covered

---

### S004: Structured error handling & observability
**Agent**: api-agent
**Parallel group**: G3 (parallel with S003)
**Depends on**: S002

**Files**
| Action | Path |
|--------|------|
| MODIFY | `backend/api/app.py` (add `@app.exception_handler` entries) |

**Subagent dispatch**: YES (isolated to app.py — no overlap with S003's new file)
**Est. tokens**: ~0.8k
**Test entry**: `pytest backend/tests/api/test_query.py -k "error"` (extend existing)

**Story-specific notes**
- Register FastAPI exception handlers for: `LanguageDetectionError`, `UnsupportedLanguageError`, `EmbedderError`, `QueryTimeoutError` — all must yield A005 shape
- Reuse `auth_error()` pattern from `backend/auth/_errors.py` for error shape consistency
- HTTP 400 for `query > 512 chars` and `top_k` out of 1–100 range — via Pydantic validators on `QueryRequest` (AC3)
- HTTP 401 — unchanged from auth feature, must not regress (AC4)
- HTTP 403 must NOT be returned for 0-group users (AC5 — D04 regression guard)
- `request_id` present in ALL responses: success + error (AC6) — `str(uuid4())` already in current query.py, verify it threads through error handlers
- No stack traces or internal paths in production error responses (AC2 / A005)

**Outputs expected**
- [ ] Exception handlers registered in `app.py`
- [ ] All error responses have `{"error": {"code": "...", "message": "...", "request_id": "..."}}` shape
- [ ] `request_id` present in every response
- [ ] No stack traces in prod mode
- [ ] Tests: AC1–AC6 covered

---

### S005: Integration tests — query endpoint full coverage
**Agent**: api-agent
**Parallel group**: G4
**Depends on**: S001, S002, S003, S004

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/tests/api/test_query.py` (if not exists — extend if exists) |

**Subagent dispatch**: YES (test-only, depends on all stories complete)
**Est. tokens**: ~0.8k
**Test entry**: `pytest backend/tests/api/test_query.py --cov=backend/api/routes/query.py --cov=backend/api/middleware/rate_limiter.py`

**Story-specific notes**
- Mock `search()` and `generate_answer()` at service boundary — no real Valkey/DB for unit tests
- Integration tests hit real DB via test fixtures (per auth-feature pattern — check `conftest.py`)
- Must cover all 12 ACs explicitly; each AC = at least one test function
- AC1: happy path for ja/en/vi/ko in a single parametrized test
- AC2: RBAC cross-group isolation — assert doc from group B not in group A results
- AC9: `low_confidence` flag asserted when mock LLM returns `confidence=0.3`
- AC10: rate limit mock — patch Valkey ZADD/ZCOUNT to simulate exceeded window
- AC12: coverage ≥ 80% for `query.py` + `rate_limiter.py` — enforce with `--cov-fail-under=80`

**Outputs expected**
- [ ] 12 test functions covering AC1–AC12
- [ ] Coverage ≥ 80% on `query.py` and `rate_limiter.py`
- [ ] All tests pass (no skips on happy-path ACs)
- [ ] Parametrized lang test for ja/en/vi/ko

---

## Prompt Caching (W01 mitigation — documented per checklist approval)

Route A applies to all /implement dispatches for this feature:
- **Stable prefix**: `CLAUDE.md` + `query-endpoint.spec.md` + story task file
- **Volatile suffix**: current diff, timestamp, ad-hoc notes
- No direct Anthropic API path in scope → Route B not required

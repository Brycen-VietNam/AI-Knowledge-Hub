# Report: query-endpoint
Generated: 2026-04-13 | Author: Claude (auto) | Status: COMPLETE — pending sign-off

---

## Executive Summary

| Field | Value |
|-------|-------|
| Feature | query-endpoint |
| Branch | feature/query-endpoint |
| Started | 2026-04-08 |
| Completed | 2026-04-13 |
| Stories | 5 / 5 DONE |
| Total tasks | 19 / 19 DONE |
| AC coverage | 35 / 35 (100%) |
| Test pass rate | 42 / 42 (100%) |
| Coverage | 95% overall (query.py=93%, rate_limiter.py=100%) |
| Gate | ≥80% coverage — PASS ✅ |
| Blockers | None |
| Status | COMPLETE — awaiting tech lead + PO sign-off |

The `/v1/query` endpoint was a stub that bypassed language detection and returned raw document content. This feature replaced it with the full hybrid RAG pipeline: unified `search()` service, AI answer generation via `generate_answer()`, Valkey-backed rate limiting (60 req/min), structured exception handlers, and a complete integration test suite at 95% coverage.

---

## Changes Summary

### Code Changes

| File | Action | Story | Description |
|------|--------|-------|-------------|
| `backend/api/routes/query.py` | MODIFIED | S001–S004 | Removed `embed()` stub; wired `search()` + `generate_answer()`; added `@field_validator` control-char strip; constants `_RETRIEVAL_TIMEOUT=1.0`, `_LLM_TIMEOUT=0.8`, `_LOW_CONFIDENCE_THRESHOLD=0.4`; request_id set at route entry; rate limit check + 429; audit log BackgroundTask |
| `backend/api/app.py` | MODIFIED | S003–S004 | Valkey pool + RateLimiter singleton at startup; 5 exception handlers: `LanguageDetectionError(422)`, `UnsupportedLanguageError(422)`, `EmbedderError(503)`, `QueryTimeoutError(504)`, `LLMError(503)` |
| `backend/api/config.py` | CREATED | S003 | `VALKEY_URL` env var; no hardcoded credentials (S005 compliance) |
| `backend/api/middleware/__init__.py` | CREATED | S003 | Package init |
| `backend/api/middleware/rate_limiter.py` | CREATED | S003 | Parametric sliding window via Valkey ZADD/ZCOUNT; fail-open on error; key=`ratelimit:query:{user_id}`; `X-RateLimit-Remaining` / `X-RateLimit-Reset` headers |
| `requirements.txt` | MODIFIED | S003 | Added `valkey>=6.0.0` (BSD-3; Redis ≥7.4 RSALv2 avoided per C016) |
| `tests/api/test_query.py` | CREATED | S001–S005 | 32 tests: S001 fixtures/assertions, S002 LLM paths, S004 validators/error shapes, S005 AC matrix (ja/en/vi/ko, RBAC, timeout, 503, low_confidence, lang override) |
| `tests/api/test_rate_limiter.py` | CREATED | S003–S005 | 10 tests: AC1–AC7 + AC10 (429+headers, 200+remaining) |
| `tests/api/test_query_route.py` | MODIFIED | S001 | Updated patch targets; `sources` assertion fixed (doc_id, not content) |

### Configuration / Environment

| Variable | Description | Default |
|----------|-------------|---------|
| `VALKEY_URL` | Valkey connection string | `redis://localhost:6379` |
| `RAG_BM25_WEIGHT` | BM25 search weight | `0.3` |
| `RAG_DENSE_WEIGHT` | Dense search weight | `0.7` |

### Documentation

| File | Action |
|------|--------|
| `docs/query-endpoint/spec/query-endpoint.spec.md` | Created — 5 stories, 35 ACs |
| `docs/query-endpoint/plan/query-endpoint.plan.md` | Created — parallel execution groups, risk register |
| `docs/query-endpoint/tasks/S001–S005.tasks.md` | Created — 19 tasks |
| `docs/query-endpoint/tasks/query-endpoint.analysis.md` | Created — gap analysis |
| `docs/query-endpoint/reviews/checklist.md` | Created — 30/31 PASS, W01 approved |
| `docs/query-endpoint/reviews/S001.review.md` | Created — APPROVED |
| `.env.example` | Modified — added `VALKEY_URL` |

---

## Test Results

### Summary

| Suite | Tests | Pass | Fail | Skip | Coverage |
|-------|-------|------|------|------|----------|
| `test_query.py` | 32 | 32 | 0 | 0 | — |
| `test_rate_limiter.py` | 10 | 10 | 0 | 0 | — |
| `test_query_route.py` | — | pass | 0 | 0 | — |
| **Total (feature)** | **42** | **42** | **0** | **0** | **95%** |

Coverage breakdown:
- `backend/api/routes/query.py` — **93%** (uncovered: `_write_audit` lines 91–96, BackgroundTask real-DB path; expected gap)
- `backend/api/middleware/rate_limiter.py` — **100%**

Pre-existing failures: 7 tests in `test_query_rbac.py` (stale `retrieve` patches from prior feature; not regressions from query-endpoint; not in scope).

### Coverage Gate
Gate: ≥ 80% — **PASS ✅** (95% achieved)

---

## Code Review Results

### S001 Review (formal — `docs/query-endpoint/reviews/S001.review.md`)

| Category | Result | Notes |
|----------|--------|-------|
| Functionality | APPROVED | `search()` wired; `embed()` removed; sources = doc_id list |
| Security | APPROVED | R002 PII fix confirmed; control-char strip via validator |
| Performance | APPROVED | `asyncio.wait_for(timeout=1.0)` wraps search; constants named |
| Style | APPROVED | Follows existing conventions |
| Tests | APPROVED | AC1–AC8 all covered |

S002–S005: no blocking issues found during implementation; no separate review requested (single api-agent scope).

---

## Acceptance Criteria Status

### S001 — Wire search() into POST /v1/query

| AC | Description | Status |
|----|-------------|--------|
| AC1 | `search()` called — replaces inline `embed()` + `retrieve()` | PASS ✅ |
| AC2 | `lang` override accepted in request body (default: None) | PASS ✅ |
| AC3 | `LanguageDetectionError` → HTTP 422 `LANG_DETECT_FAILED` | PASS ✅ |
| AC4 | `UnsupportedLanguageError` → HTTP 422 `LANG_UNSUPPORTED` | PASS ✅ |
| AC5 | `EmbedderError` → HTTP 503 `EMBEDDER_UNAVAILABLE` | PASS ✅ |
| AC6 | `QueryTimeoutError` → HTTP 504 `QUERY_TIMEOUT` (no regression) | PASS ✅ |
| AC7 | 0-group users → public results, not 403 (D04 no regression) | PASS ✅ |
| AC8 | Audit log written as BackgroundTask (R006) | PASS ✅ |

### S002 — Wire generate_answer() for AI responses

| AC | Description | Status |
|----|-------------|--------|
| AC1 | `generate_answer()` called when docs non-empty | PASS ✅ |
| AC2 | `QueryResponse.answer` non-null on LLM success | PASS ✅ |
| AC3 | `sources` = doc_id strings (no PII, no raw content — R002) | PASS ✅ |
| AC4 | `low_confidence=True` when confidence < 0.4 (C014) | PASS ✅ |
| AC5 | `NoRelevantChunksError` → 200 `{answer: null, reason: "no_relevant_chunks"}` | PASS ✅ |
| AC6 | LLM unavailable → HTTP 503 `LLM_UNAVAILABLE` | PASS ✅ |
| AC7 | No answer if 0 chunks (C014) | PASS ✅ |
| AC8 | `reason` populated only when `answer` is null | PASS ✅ |

### S003 — Rate limiting — 60 req/min per user

| AC | Description | Status |
|----|-------------|--------|
| AC1 | >60/min → HTTP 429 `RATE_LIMIT_EXCEEDED` | PASS ✅ |
| AC2 | Sliding window (not fixed bucket) — ZADD/ZCOUNT | PASS ✅ |
| AC3 | Valkey (BSD-3) backend — Redis ≥7.4 avoided (C016) | PASS ✅ |
| AC4 | Key = `ratelimit:query:{user_id}` | PASS ✅ |
| AC5 | Middleware parametric: `resource`, `limit`, `window` | PASS ✅ |
| AC6 | Valkey unavailable → fail-open (log warning, allow) | PASS ✅ |
| AC7 | `X-RateLimit-Remaining` + `X-RateLimit-Reset` headers present | PASS ✅ |

### S004 — Structured error handling & observability

| AC | Description | Status |
|----|-------------|--------|
| AC1 | All errors: `{"error": {"code", "message", "request_id"}}` (A005) | PASS ✅ |
| AC2 | No stack traces in production responses | PASS ✅ |
| AC3 | HTTP 400 for query >512 chars or top_k out of 1–100 | PASS ✅ |
| AC4 | HTTP 401 for missing/invalid auth (no regression) | PASS ✅ |
| AC5 | HTTP 403 not returned for 0-group users (D04 no regression) | PASS ✅ |
| AC6 | `request_id` present in all responses (success + error) | PASS ✅ |

### S005 — Integration tests — full coverage

| AC | Description | Status |
|----|-------------|--------|
| AC1 | Happy path: ja/en/vi/ko multilingual parametrized | PASS ✅ |
| AC2 | RBAC: cross-group isolation | PASS ✅ |
| AC3 | 0-group → public results, not 403 | PASS ✅ |
| AC4 | Unauthenticated → 401 | PASS ✅ |
| AC5 | query >512 chars → 400 | PASS ✅ |
| AC6 | Retrieval timeout → 504 | PASS ✅ |
| AC7 | LLM unavailable → 503 | PASS ✅ |
| AC8 | No relevant chunks → 200 null answer | PASS ✅ |
| AC9 | `low_confidence=True` when confidence < 0.4 | PASS ✅ |
| AC10 | Rate limit exceeded → 429 + headers | PASS ✅ |
| AC11 | `lang` override accepted, bypasses auto-detect | PASS ✅ |
| AC12 | Coverage ≥ 80% (`query.py`=93%, `rate_limiter.py`=100%) | PASS ✅ |

**Total: 35 / 35 AC — 100% PASS**

---

## Blockers & Open Issues

### Resolved Blockers
| ID | Description | Resolution |
|----|-------------|------------|
| Q1 | `lang` override — body or header? | Confirmed body field — lb_mui 2026-04-08 |
| Q2 | LLM timeout budget | Confirmed: retrieval 1.0s / LLM 0.8s — lb_mui 2026-04-08 |
| Q3 | `VALKEY_URL` new or existing env var | New var; added to `backend/api/config.py` and `.env.example` |
| GAP-1 | `LLMUnavailableError` missing | Resolved: catch `LLMError` as 503 trigger; no separate subclass needed |
| GAP-2 | `backend/api/schemas.py` missing | Resolved: `QueryRequest` stays inline in `query.py` |
| GAP-3 | `backend/api/middleware/` missing | Resolved: created dir + `__init__.py` + `rate_limiter.py` in S003 |

### Deferred / Open Issues
| ID | Description | Severity | Owner | Due |
|----|-------------|----------|-------|-----|
| DEF-1 | 7 pre-existing failures in `test_query_rbac.py` (stale `retrieve` patches from rbac-document-filter era) | LOW | lb_mui | Next sprint |
| DEF-2 | `_write_audit` BackgroundTask real-DB path not covered (lines 91–96 in query.py) | LOW | N/A | Not blocking — expected gap |
| DEF-3 | W01 (prompt caching) — Route B not implemented | WARN | N/A | Approved deferral — no direct Anthropic API path in scope |

---

## Rollback Plan

| Step | Action | Downtime | Data Loss Risk |
|------|--------|----------|----------------|
| 1 | Revert branch merge via `git revert` on merge commit | Zero | None |
| 2 | Remove `VALKEY_URL` from env / Kubernetes secrets | Zero | None |
| 3 | Remove `valkey>=6.0.0` from `requirements.txt` and redeploy | Brief restart | None |
| 4 | Old stub query.py restored — returns raw content (PII leak risk re-introduced) | — | **See note** |

**Note on rollback**: The old stub had a PII bug (`sources=[d.content for d in docs]`). Rolling back re-introduces R002 violation. If rollback is needed, patch the old stub to at least return `doc_id` before deploying. Contact security lead before rolling back.

Valkey data: rate limit counters are ephemeral (60s TTL). No rollback needed for cache state.

---

## Knowledge & Lessons Learned

### What Went Well
- **Gap analysis saved time**: `/analyze` caught 4 structural gaps (missing schemas.py, middleware/, LLMUnavailableError, request_id threading) before implementation started. Zero surprises during `/implement`.
- **Parallel execution plan worked**: S003 + S004 ran in the same session without conflict — files never overlapped (new file vs. app.py exception handlers).
- **Fail-open rate limiter**: Choosing fail-open for Valkey errors was the right call — this matches platform-availability-first principle and was easy to unit test.
- **Named constants over magic numbers**: `_RETRIEVAL_TIMEOUT`, `_LLM_TIMEOUT`, `_LOW_CONFIDENCE_THRESHOLD` eliminated confusion across 5 story implementations.

### What to Improve
- **Pre-existing test debt**: `test_query_rbac.py` had 7 stale patch failures before this feature started. Future features should clean up stale mocks in the same sprint rather than deferring.
- **schemas.py gap**: Several stories planned against `backend/api/schemas.py` which did not exist. `/analyze` caught it, but the spec should have noted inline-model vs. schema-file decision earlier.
- **Coverage path for BackgroundTask**: The `_write_audit` background path requires a real DB connection to cover. Consider a lightweight in-memory DB fixture for audit log tests in the next sprint to close the 7% gap on query.py.

### Rule Updates Triggered
- None — all existing rules (R001–R007, A001–A006, S001–S005, P001–P005) were satisfied. No amendments needed.

---

## Sign-Off

| Role | Name | Status | Date |
|------|------|--------|------|
| Tech Lead | _pending_ | [ ] Approved | — |
| Product Owner | _pending_ | [ ] Approved | — |
| QA Lead | _pending_ | [ ] Approved | — |

After all approvals, run:
```
/report query-endpoint --finalize
```
→ Archives `WARM/query-endpoint.mem.md` → `COLD/query-endpoint.archive.md`
→ Updates `HOT.md` (removes from In Progress)
→ Feature marked DONE

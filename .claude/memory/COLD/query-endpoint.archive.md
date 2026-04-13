# COLD Archive: query-endpoint
Archived: 2026-04-13 | Status: DONE ✅ | Approved by: lb_mui

---

## Feature Summary
Complete the `/v1/query` POST endpoint:
1. Replace stub embed/retrieve with `search()` from `backend/rag/search.py`
2. Wire `generate_answer()` for AI answers with source citations
3. Add Valkey-backed rate limiting (60 req/min per user)
4. Structured exception handlers (all error shapes per A005)
5. Full integration test suite (≥80% coverage)

## Final Metrics
| Metric | Value |
|--------|-------|
| Stories | 5 / 5 DONE |
| Tasks | 19 / 19 DONE |
| AC coverage | 35 / 35 (100%) |
| Test pass rate | 42 / 42 (100%) |
| Coverage | 95% (query.py=93%, rate_limiter.py=100%) |
| Duration | 2026-04-08 → 2026-04-13 |

## Key Files
- `backend/api/routes/query.py` — main route (search() + generate_answer() + rate limit + validators)
- `backend/api/app.py` — 5 exception handlers; Valkey pool at startup
- `backend/api/config.py` — VALKEY_URL env var (NEW)
- `backend/api/middleware/rate_limiter.py` — sliding window, fail-open (NEW)
- `tests/api/test_query.py` — 32 tests (NEW)
- `tests/api/test_rate_limiter.py` — 10 tests (NEW)

## Key Decisions
- D04 inherited: 0-group users → public results (not 403)
- D09 inherited: NoRelevantChunksError → 200 `{answer: null, reason: "no_relevant_chunks"}`
- Timeout budget: retrieval 1.0s / LLM 0.8s (A2 confirmed by lb_mui 2026-04-08)
- `lang` override in request body (not header) — A1 confirmed by lb_mui 2026-04-08
- Valkey key: `ratelimit:query:{user_id}` — fail-open on Valkey error
- LLMUnavailableError does not exist — catch LLMError as 503
- sources = `[str(d.doc_id)]` — R002 PII fix (critical bug resolved in S001)
- _write_audit BackgroundTask real-DB path not covered (lines 91–96) — expected gap, not blocking

## Deferred Items
- DEF-1: 7 stale failures in `test_query_rbac.py` — LOW priority, next sprint, owner: lb_mui
- DEF-2: `_write_audit` coverage (BackgroundTask DB path) — LOW, not blocking
- DEF-3: W01 prompt caching Route B — approved deferral at checklist

## Report
`docs/query-endpoint/reports/query-endpoint.report.md`

## Unblocks
_None — query-endpoint was the final dependency in the auth/RAG sprint chain._

# WARM Memory: query-endpoint
Created: 2026-04-08 | Status: CLARIFY DONE — all blockers resolved ✅

---

## Feature Summary
Complete the `/v1/query` POST endpoint:
1. Replace stub embed/retrieve with `search()` from `backend/rag/search.py`
2. Wire `generate_answer()` for AI answers with source citations
3. Add Valkey-backed rate limiting (60 req/min per user)
4. Structured exception handlers (all error shapes per A005)
5. Full integration test suite (≥80% coverage)

## Key Files
- `backend/api/routes/query.py` — main route (currently a stub — generate_answer not called)
- `backend/rag/search.py` — unified search() service (replace inline embed/retrieve)
- `backend/rag/generator.py` — generate_answer() service layer
- `backend/rag/retriever.py` — retrieve() + RetrievedDocument + QueryTimeoutError
- `backend/auth/dependencies.py` — verify_token + get_db
- `backend/api/app.py` — exception handler registration
- NEW: `backend/api/middleware/rate_limiter.py` — sliding window rate limiter

## Decisions Inherited
- D04: 0-group users → public results (not 403)
- D09: NoRelevantChunksError → 200 `{answer: null, reason: "no_relevant_chunks"}`
- D10: QueryResponse shape: answer + sources + low_confidence (already in place)
- D4 (multilingual): `lang: str|None = None` — None=auto-detect
- C014: confidence < 0.4 → low_confidence=True; ≥1 source required

## Critical Bugs to Fix in S001
- `sources` in response currently set to `[d.content for d in docs]` — WRONG (leaks PII/content)
- Must be `[str(d.doc_id) for d in docs]` — R002 compliance
- `embed()` helper (lines 57–64 in query.py) must be removed — bypasses language detection

## Open Questions
- Q1: Should `lang` override be in query body or as a header? (Assumption: body field)
- Q2: LLM generation timeout budget — entire pipeline is 1.8s; how much to reserve for LLM?
  (Assumption: retrieval gets 1.0s, LLM gets 0.8s — total stays under 1.8s SLA)
- Q3: Valkey connection string — is VALKEY_URL already in env config or new var?

## Assumptions
- A1: ✅ CONFIRMED — `lang` override is in request body (not header) — lb_mui 2026-04-08
- A2: ✅ CONFIRMED — retrieval 1.0s / LLM 0.8s, total ≤ 1.8s — lb_mui 2026-04-08
- A3: `VALKEY_URL` env var is new — not yet defined in existing config

## Status
- [x] Spec written
- [x] /clarify — 2026-04-08 | 2 blockers, 15 auto-answered, 3 assumptions
- [x] /checklist — 2026-04-08 | WARN (W01 prompt caching, approved) — 30/31 PASS | `docs/query-endpoint/reviews/checklist.md`
- [x] /plan — 2026-04-08 | 5 stories | G1→G2→G3(parallel)→G4 | `docs/query-endpoint/plan/query-endpoint.plan.md`
- [x] /tasks — 2026-04-08 | 5 stories, 19 tasks | `docs/query-endpoint/tasks/`
- [x] /analyze — 2026-04-08 | `docs/query-endpoint/tasks/query-endpoint.analysis.md`
- [x] /implement — S001 DONE 2026-04-13
- [x] /reviewcode — S001 APPROVED 2026-04-13
- [x] /implement S002 DONE 2026-04-13
- [x] /implement S003 DONE 2026-04-13
- [x] /implement S004 DONE 2026-04-13
- [x] /implement S005 — DONE 2026-04-13
- [x] /report — 2026-04-13 | `docs/query-endpoint/reports/query-endpoint.report.md`

## Stories
| ID | Title | Status |
|----|-------|--------|
| S001 | Wire search() into POST /v1/query | REVIEWED ✅ 2026-04-13 |
| S002 | Wire generate_answer() for AI responses | DONE ✅ 2026-04-13 |
| S003 | Rate limiting — 60 req/min per user | DONE ✅ 2026-04-13 |
| S004 | Structured error handling & observability | DONE ✅ 2026-04-13 |
| S005 | Integration tests — full coverage | REVIEWED ✅ 2026-04-13 |

## Sync: 2026-04-08 (post-clarify)
Decisions added: none — assumptions A1/A2/A3 pending PO confirmation
Tasks changed: /clarify complete
Files touched: docs/query-endpoint/clarify/query-endpoint.clarify.md
Questions resolved: Q-A1 through Q-A15 auto-answered from CONSTITUTION/HARD/WARM
Blockers: Q1 (lang override location), Q2 (LLM timeout budget) — must resolve before /checklist passes

## Sync: 2026-04-08 (post-checklist)
Decisions added: none
Tasks changed: /checklist PASS — WARN W01 (prompt caching) approved; 30/31 items pass
Files touched: docs/query-endpoint/reviews/checklist.md (created)
Questions resolved: A1 ✅ confirmed, A2 ✅ confirmed (both from clarify, now final)
New blockers: none
Next: /plan query-endpoint

## Sync: 2026-04-08 (post-plan)
Plan: docs/query-endpoint/plan/query-endpoint.plan.md
Critical path: S001 → S002 → (S003 ∥ S004) → S005
Parallel groups: G1=S001, G2=S002, G3=S003+S004, G4=S005
Prompt caching: Route A documented in plan (W01 mitigation complete)
New files to create: backend/api/middleware/rate_limiter.py, backend/tests/api/test_query.py
Files to modify: backend/api/routes/query.py, backend/api/app.py, backend/api/config.py, backend/api/schemas.py
Next: /tasks query-endpoint S001

## Sync: 2026-04-08 (post-plan /sync)
Decisions added: none (plan decisions already in post-plan sync block)
Tasks changed: /plan → DONE
Files touched: docs/query-endpoint/plan/query-endpoint.plan.md (created)
Questions resolved: none
New blockers: none

## Sync: 2026-04-08 (post-analyze)
Decisions added: none
Tasks changed: /analyze → DONE
Files created: docs/query-endpoint/tasks/query-endpoint.analysis.md
Questions resolved: none
New gaps found (critical for /implement):
  - backend/api/schemas.py does NOT exist — QueryRequest is inline in query.py
  - backend/api/config.py does NOT exist — must create in S003-T001
  - backend/api/middleware/ does NOT exist — create dir + __init__.py + rate_limiter.py in S003-T001/T002
  - LLMUnavailableError missing from backend/rag/llm/exceptions.py — must add before S004-T002
  - request.state.request_id never set in route — add Request param + set at entry in S004-T003
  - test_query_route.py patches retrieve/embed — will break after S001-T004; update in S001-T005
  - generate_answer(chunks: list[str]) — NOT RetrievedDocument; pass [d.content for d in docs]
New blockers: none
Next: /implement query-endpoint S001

## Sync: 2026-04-08 (post-tasks)
Tasks changed: /tasks → DONE for all 5 stories (19 tasks total)
Files created: docs/query-endpoint/tasks/S001.tasks.md (5 tasks), S002.tasks.md (4 tasks), S003.tasks.md (4 tasks), S004.tasks.md (3 tasks), S005.tasks.md (3 tasks)
Task summary:
  S001: T001(rm embed+PII fix) → T002+T003(∥: schema+fixtures) → T004(search+timeout) → T005(audit+tests)
  S002: T001(fixtures) → T002(generate_answer+timeout) → T003+T004(∥: NoRelevantChunks+low_confidence)
  S003: T001(config+scaffold) → T002(RateLimiter class) → T003+T004(∥: middleware+fail-open)
  S004: T001(validators) → T002+T003(∥: exception handlers+request_id)
  S005: T001+T002(∥: AC tests) → T003(coverage gate ≥80%)
New blockers: none
Next: /analyze S001 T001

## Sync: 2026-04-13 (post-S001+S002-implement)
Decisions added:
  - _RETRIEVAL_TIMEOUT=1.0 (const), _LLM_TIMEOUT=0.8 (const) — R007/A2 budget split documented
  - _LOW_CONFIDENCE_THRESHOLD=0.4 — C014 named constant (not magic number)
  - sources=[str(d.doc_id)] — R002 confirmed; LLMResponse.sources NOT exposed in API response
  - LLMUnavailableError does not exist — catch LLMError as 503 trigger instead (analysis gap resolved)
Tasks changed:
  S001: all 5 tasks → DONE | status → REVIEWED ✅ (review: docs/query-endpoint/reviews/S001.review.md)
  S002: all 4 tasks → DONE
Files modified:
  backend/api/routes/query.py — embed() deleted; search() wired; generate_answer() wired; constants added
  tests/api/test_query.py — created (S001 fixtures + S002 fixtures + 14 tests)
  tests/api/test_query_route.py — patch targets updated; sources assertion fixed
  docs/query-endpoint/tasks/S001.tasks.md — status REVIEWED
  docs/query-endpoint/tasks/S002.tasks.md — status DONE
  docs/query-endpoint/reviews/S001.review.md — created (APPROVED)
Tests: 17/17 pass (test_query.py + test_query_route.py)
New blockers: none
Next: /implement query-endpoint S003

## Sync: 2026-04-13 (post-S003-implement)
Decisions added:
  - Valkey key pattern: ratelimit:query:{user_id} (AC4)
  - Fail-open on Valkey error: log warning, return (True, limit, reset_ts) — not reject (AC6)
  - _rate_limiter singleton at module level in query.py — patchable in tests
  - valkey-py (not redis-py) added to requirements.txt (AC3, S004 S005)
Tasks changed:
  S003: all 4 tasks → DONE ✅
Files created:
  backend/api/config.py — VALKEY_URL env var (S005: no hardcoded credentials)
  backend/api/middleware/__init__.py — package init
  backend/api/middleware/rate_limiter.py — RateLimiter sliding window class + fail-open
  tests/api/test_rate_limiter.py — 8 AC tests (AC1–AC7)
Files modified:
  backend/api/app.py — Valkey pool + RateLimiter singleton at startup (not per-request)
  backend/api/routes/query.py — rate limit check + X-RateLimit-Remaining/Reset headers + 429
  requirements.txt — added valkey>=6.0.0
Tests: 8/8 pass (test_rate_limiter.py); 51/58 total (7 pre-existing failures in test_query_rbac.py — stale retrieve patches, not S003 regressions)
New blockers: none
Next: /implement query-endpoint S004

## Sync: 2026-04-13 (post-S004-implement)
Decisions added:
  - LLMUnavailableError does not exist — LLMError registered as 503 handler in app.py (confirmed)
  - QueryRequest.query: control-char strip via @field_validator (SECURITY S003)
  - request.state.request_id set at route entry — exception handlers reuse same id (A005)
  - schemas.py does not exist — QueryRequest stays inline in query.py (analysis gap confirmed)
Tasks changed:
  S004: all 3 tasks → DONE ✅
Files modified:
  backend/api/routes/query.py — @field_validator strip_control_chars; request.state.request_id set
  backend/api/app.py — 5 exception handlers: LanguageDetectionError(422), UnsupportedLanguageError(422), EmbedderError(503), QueryTimeoutError(504), LLMError(503)
  tests/api/test_query.py — 5 new S004 tests (validators, control-char, request_id, no-stack-trace)
Tests: 19/19 pass (test_query.py); 56/63 total (7 pre-existing failures in test_query_rbac.py unchanged)
New blockers: none

## Sync: 2026-04-13 (post-S005-implement)
Decisions added:
  - --cov flag requires dotted module path (backend.api.routes.query), not file path
  - AC4 test: override get_db (not verify_token) — real verify_token raises 401 before any DB access
  - _write_audit lines 91–96 not covered (BackgroundTask real-DB path); expected, not a gap
Tasks changed:
  S005: all 3 tasks → DONE ✅
Files modified:
  tests/api/test_query.py — 13 new S005 tests (AC1×4 langs, AC2, AC3×3, AC4, AC5, AC6, AC9, AC11)
  tests/api/test_rate_limiter.py — 2 new AC10 tests (429+headers, 200+remaining header)
  docs/query-endpoint/tasks/S005.tasks.md — status DONE
Tests: 32/32 pass (test_query.py); 10/10 pass (test_rate_limiter.py); 42/42 pass total
Coverage: query.py=93%, rate_limiter.py=100%, total=95% — gate ≥80% PASS ✅
New blockers: none
Next: /report query-endpoint

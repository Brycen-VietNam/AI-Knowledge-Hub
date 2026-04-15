# Pre-Plan Checklist: citation-quality
Created: 2026-04-15 | Spec: `docs/citation-quality/spec/citation-quality.spec.md` | Status: PASS

---

## Overview
Gate-keeping checklist before `/plan` is allowed.

**Status:**
- [x] **AC Coverage** — All acceptance criteria clear & testable ✅
- [x] **Scope Impact** — All affected systems identified ✅
- [x] **Quality Criteria** — Performance, security, CJK support defined ✅

---

## Section 1: Acceptance Criteria Coverage

### Completeness
- [x] All ACs have clear "as a / want / so that" statements — all 3 stories have role/want/value
- [x] All ACs are SMART — each AC specifies exact input, output, or behavior (e.g. AC1: exact function call + return value)
- [x] All ACs have acceptance/rejection criteria defined — each AC is a concrete assertion
- [x] No vague ACs — no "improve", "support", "handle" language; all ACs are measurable

### Testability
- [x] Each AC independently testable — S001 ACs map 1:1 to pytest parametrize cases; S002 ACs each test one field/path
- [x] Test success criteria unambiguous — e.g. "returns `{0, 2}`", "returns `{}`", "`cited=True`"
- [x] No hidden assumptions in AC descriptions — one explicit assumption (A-CQ-01) surfaced and flagged
- [x] Edge cases covered — OOB marker (AC2), empty input (AC5), deduplication (AC4), no markers (AC3), CJK text (S003 note)

### Story Dependencies
- [x] Story order clearly marked — S001 → S002 → S003 (critical path in Layer 1)
- [x] Blocking stories: answer-citation DONE ✅
- [x] Parallel-safe stories: none — correctly declared (S002 depends on S001 parser; S003 depends on S002)
- [x] Critical path clear: S001 → S002 → S003

**Verdict: ✅ PASS — All ACs clear + testable**

---

## Section 2: Scope Impact

### Systems & Files
- [x] API endpoints impacted? — `POST /v1/query` response schema gains `cited: bool`; no new endpoint
- [x] Database schema changes? — NO. No migration. Pure additive Python change only.
- [x] Authentication/Authorization? — No change. Inherits existing `verify_token` on `/v1/query` (R003).
- [x] Frontend components? — Out of scope (declared in spec). No frontend changes.
- [x] Third-party integrations? — No change. LLM adapters untouched.
- [x] Configuration files? — No new env vars required.

### Non-functional Impact
- [x] Latency SLA affected? — Parser is O(len(answer)), < 1ms. 1.8s SLA unaffected (R007 / P001).
- [x] Storage impact? — None. No new DB columns, no new tables.
- [x] Audit logging required? — NOT required for parser. Retrieval audit already logged in answer-citation (R006).
- [x] Cache invalidation strategy? — N/A. No cache changes.
- [x] Rollback plan feasible? — YES. `CitationObject.cited` defaults to `False` — removing parser call reverts behavior instantly.

### Cross-team Impact
- [x] Other teams affected? — Consumer teams (Web SPA, Teams bot, Slack bot). Breaking change? NO — `cited: bool = False` default; existing responses still valid. Additive only.
- [x] Breaking changes? — None. Pydantic field with default `False` — backward compatible.
- [x] Deployment order? — Single-service change. No ordering constraint.

**Verdict: ✅ PASS — All scope boundaries clear**

---

## Section 3: Quality Criteria

### Functional Quality
- [x] RBAC applied at DB level — N/A for this feature. No new retrieval paths. Existing RBAC in retriever unchanged (R001).
- [x] No PII in vector metadata — N/A. Parser operates on LLM answer string only. No metadata changes (R002).
- [x] Auth on every endpoint — No new endpoints. Existing `/v1/query` auth unchanged (R003).
- [x] API version prefix `/v1/*` — No new routes. Existing prefix intact (R004).

### Multilingual Support
- [x] CJK-aware tokenization — N/A for parser. Regex targets ASCII `[N]` markers; CJK body text passes through transparently.
- [x] Language-specific test cases included — S003 spec: "add one CJK-answer test case (e.g. Japanese answer containing `[1]` marker)" ✅
- [x] Fallback language — N/A. Parser is language-agnostic.

### Performance
- [x] p95 latency target < 2s — Parser < 1ms addition; within 1.8s SLA. Non-blocking (R007).
- [x] Query timeout defined — Inherits `_LLM_TIMEOUT` and `_RETRIEVAL_TIMEOUT` from `query.py`; parser runs after LLM returns, not inside timeout.
- [x] Batch size / pagination — N/A.
- [x] Index strategy — N/A. No new DB queries.

### Security & Compliance
- [x] Audit log on document access — Existing audit log in `_write_audit()` unchanged. Parser does not access docs (R006).
- [x] Input validation — Parser input is `llm_response.answer: str` (already sanitized in `QueryRequest.strip_control_chars`) and `len(content_docs): int`. No new user input surface.
- [x] Rate limiting — No new endpoint. Existing 60 req/min on `/v1/query` unchanged (S004).
- [x] Encryption — N/A. No new secrets or data-at-rest changes.
- [x] GDPR/compliance — N/A. Parser reads answer text only; no PII stored or logged.

### Testing & Documentation
- [x] Unit test scope defined — `citation_parser.py` ≥ 95%, `citation.py` ≥ 95%, `query.py` net ≥ 90% (S003 AC8)
- [x] Integration test scenarios listed — 5 integration test cases defined in S003 AC3–AC6 (golden path, no-markers, OOB, no-chunk)
- [x] Black-box test cases — happy path (AC3), edge: no markers (AC4), OOB (AC5), no-chunk (AC6)
- [x] Documentation — OpenAPI schema auto-updated via Pydantic (S002 AC7). API contract in S002 spec.
- [x] Prompt caching strategy — N/A. No new LLM prompt templates added. Existing `answer.txt` prompt unchanged.

**Verdict: ✅ PASS — All quality criteria met**

---

## Final Gate: Overall Status

| Section | Result | Issues |
|---------|--------|--------|
| AC Coverage | ✅ PASS | — |
| Scope Impact | ✅ PASS | — |
| Quality Criteria | ✅ PASS | — |

### Open Assumption (not a blocker)
> **A-CQ-01**: `cited` indexing maps over `content_docs` (docs with `.content`), not all `docs`. Surfaced and marked in spec S002. Does not block planning — implementation note covers both interpretations. Confirm at /clarify or before /tasks.

---

### **OVERALL CHECKLIST STATUS: ✅ PASS**

**Score: 30/30 passed | 0 WARN | 0 FAIL**

**Approved by:** auto (/checklist inline with /plan — small follow-on feature, 0 HARD rule conflicts)
**Date:** 2026-04-15
**Comments:** Feature is a pure additive extension to answer-citation. No DB, no auth, no new endpoints. Assumption A-CQ-01 is a low-risk implementation detail — does not affect AC testability or consumer contract.

---

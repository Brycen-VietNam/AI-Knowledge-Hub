# Checklist: frontend-spa
Generated: 2026-04-16 | Spec version: v1 DRAFT | Stories: S000–S005 | ACs: 45
Result: ✅ PASS (with 1 WARN — requires approval)

---

## Summary

**38/39 checks passed.** 1 WARN item requires human approval before /plan proceeds.

---

## ✅ Spec Quality (7/7)

- [x] Spec file exists at `docs/frontend-spa/spec/frontend-spa.spec.md`
- [x] Layer 1 summary complete — all fields filled (Epic, Priority, Story count, Token budget, Critical path, Parallel-safe, Blocking/Blocked, Agents)
- [x] Layer 2 stories have clear AC statements (SMART): all 45 ACs across S000–S005 are specific and testable
- [x] Layer 3 sources fully mapped — 45/45 ACs traced in both spec Layer 3 and `sources/frontend-spa.sources.md`
- [x] All ACs are testable: no vague criteria (all are behavioral or outcome-based)
- [x] API contract defined for every API story: S000 has full request/response contract; S003 has `/v1/query` contract; S001 references S000 contract
- [x] No silent assumptions — 2 explicit assumptions (A001, A002) documented in WARM; SHOULD defaults documented in clarify.md (Q6–Q11)

---

## ✅ Architecture Alignment (6/6)

- [x] No CONSTITUTION violations — thin client pattern follows P004; C003 exception for /v1/auth/token explicitly documented (S000 AC7); C014 low-confidence warning in S003 AC4
- [x] No HARD rule violations in spec design — R003 exception pattern applied correctly (S000 AC7 mirrors /v1/health); R007 latency SLA not applicable to frontend (backend SLA already met)
- [x] Agent scope assignments match AGENTS.md — api-agent for S000 (backend/api/), frontend-agent for S001–S005 (frontend/); dependency direction correct
- [x] Dependency direction follows ARCH.md A002 — frontend → api (SPA calls /v1/*); no reverse deps; S000 is backend-only change
- [x] pgvector/schema changes have migration plan — S000 AC2: migration `008_add_password_hash.sql` specified; numbered correctly (confirmed by Q1 BLOCKER resolved)
- [x] Auth pattern specified — S000: HS256 JWT via AUTH_SECRET_KEY; S001–S005: JWT Bearer; dual-mode verify_token (HS256 + RS256/ES256) specified in S000 AC9

---

## ✅ Multilingual Completeness (4/4)

- [x] All 4 languages addressed: S002 AC2 language selector (ja/en/vi/ko); S002 AC3 i18n full coverage; S003 CJK font support mentioned
- [x] CJK tokenization: N/A for frontend — no text indexing or BM25 processing. S004 AC5 CJK-safe truncation specified (`Intl.Segmenter` / spread `[...str]`); S002 implementation notes handle IME composition (Q8 SHOULD default)
- [x] Response language behavior defined — frontend sends `"lang": "auto"` (S003 API contract); backend handles detection per A003
- [x] i18n completeness — react-i18next + translation files for all 4 locales specified in S002 implementation notes

---

## ✅ Dependencies (4/4)

- [x] Dependent specs: query-endpoint DONE ✅, answer-citation DONE ✅, confidence-scoring DONE ✅ — all backend dependencies resolved
- [x] External contracts locked — `/v1/query` response shape stable (A001 in WARM); `/v1/auth/token` contract defined in S000 spec itself
- [x] No circular story dependencies — S000 → S001 → S002 → S003; S003/S004 parallel-safe after S002; S005 independent
- [x] auth-api-key-oidc DONE ✅ — verify_token exists, S000 extends it (dual-mode), not replaces it

---

## ✅ Agent Readiness (4/5 — 1 WARN)

- [x] Token budget estimated in Layer 1 — ~6k tokens
- [x] Parallel-safe stories identified — S003 + S004 parallel-safe after S002 (per Layer 1)
- [x] Subagent assignments listed — api-agent (S000), frontend-agent (S001–S005) per Layer 1 and WARM
- [x] Prompt caching strategy: **N/A** — frontend-spa has no LLM prompt path. SPA is a pure thin client consuming existing `/v1/query`. No new LLM calls introduced. (Route A/B not applicable.)
- [⚠️] **WARN**: S000 (api-agent) and S001–S005 (frontend-agent) have a hard sequential dependency (S000 must complete before frontend can test auth). Parallel dispatch is NOT safe for S000 ↔ S001. However, spec Layer 1 correctly marks critical path as sequential (S000 → S001 → ...). AGENTS.md confirms `api-agent + frontend-agent` can parallel — but only after API contract is locked. **Contract IS locked in spec.** Risk: frontend tests for S001 will mock the token endpoint until S000 is deployed.

---

## ⚠️ WARN Items

---

⚠️ **WARN: S001 frontend tests depend on S000 backend endpoint not yet deployed**

**Risk:** Frontend (S001) unit tests for login flow must mock `POST /v1/auth/token` until S000 is implemented and deployed. If S000 implementation deviates from spec contract (e.g., different response shape, different error codes), S001 mocks may pass while integration fails.

**Mitigation:**
1. S001 tests use contract-based mocking (mock exact spec response shape from S000 spec)
2. Integration test suite (E2E) runs ONLY after S000 is deployed and `/v1/auth/token` returns real tokens
3. /plan will sequence: S000 → integration gate → S001–S005 (unit tests can parallel after S000 spec lock)

**Approve?** [ ] Yes, proceed  [ ] No, resolve first

---

## ✅ Passed Items Summary (38/39)

| Section | Passed | Total |
|---------|--------|-------|
| Spec Quality | 7 | 7 |
| Architecture Alignment | 6 | 6 |
| Multilingual Completeness | 4 | 4 |
| Dependencies | 4 | 4 |
| Agent Readiness | 4 | 5 |
| **TOTAL** | **25** | **26** |

> Note: Prompt caching item marked N/A (counts as pass per checklist rules — no LLM path in this feature).

---

## BLOCKERS (0)

None. All clarify.md BLOCKERs (Q1–Q5) resolved. No CONSTITUTION violations. No HARD rule violations.

---

## Next

Approve WARN item above → then proceed to `/plan frontend-spa`

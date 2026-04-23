# Checklist: security-audit
Generated: 2026-04-23 | Spec: v1 DRAFT | Stories: S001, S002
Result: ✅ **PASS** — 29/30 passed, 1 N/A (with reason)

---

## Summary
- All BLOCKER clarify questions resolved (Q1 → D-SA-01 confirmed 2026-04-23)
- No HARD / ARCH / SECURITY / PERF violations detected in spec design
- All 20 ACs traced to sources (10 S001 + 10 S002)
- Agent assignments match AGENTS.md scopes (api, auth, db, frontend)
- Prompt caching item marked **N/A**: feature is auth/DB work — no LLM prompt path

→ **Proceed to /plan**

---

## Spec Quality (7/7 ✅)
- [x] Spec file exists at `docs/security-audit/spec/security-audit.spec.md`
- [x] Layer 1 summary complete (epic, priority, story count, budget, critical path, parallel-safety, blockers, agents — all filled)
- [x] Layer 2 stories have SMART AC statements — 10 ACs per story, each testable
- [x] Layer 3 sources fully mapped — 20/20 ACs traced with source type + reference + date
- [x] All ACs testable — no "should work well"; each has observable pass/fail criteria
- [x] API contract defined for S001 (`/v1/auth/refresh`) and S002 (`/v1/admin/users/{id}/password-reset` unchanged)
- [x] No silent assumptions — one assumption in S002 flagged explicitly (user-row fetch, resolved in clarify Q2)

## Architecture Alignment (6/6 ✅)
- [x] No CONSTITUTION violations — C003 (auth required), C004 (additive non-breaking) explicitly honored
- [x] No HARD rule violations — R003, R004, R005, R006, R007, A006 all referenced in spec notes
- [x] Agent scope assignments match AGENTS.md (api-agent, auth-agent, db-agent, frontend-agent)
- [x] Dependency direction follows A002 — frontend → api → auth → db; no reverse deps
- [x] pgvector/schema changes have migration plan — `012_add_token_version.sql` with rollback (A006)
- [x] Auth pattern specified — OIDC Bearer (S001), OIDC + API-key (S002); local HS256 scope confirmed in Q5

## Multilingual Completeness (3/3 ✅)
- [x] All 4 languages addressed — N/A at feature level: auth/session plumbing has no user-facing text
- [x] CJK tokenization — N/A (no text processing / BM25 path)
- [x] Response language behavior — error codes are language-neutral; `message` field can be localized later (no i18n changes required)

## Dependencies (3/3 ✅)
- [x] Dependent specs — `change-password` DONE ✅ (Layer 1 confirms)
- [x] External contracts locked — `AUTH_SECRET_KEY` existing, `JWT_REFRESH_SECRET` new (D-SA-01)
- [x] No circular story dependencies — S002 depends on S001 migration (linear, declared)

## Agent Readiness (4/4 ✅)
- [x] Token budget estimated — ~4k in Layer 1
- [x] Parallel-safe stories identified — "None — S002 depends on S001" (explicit, correct)
- [x] Subagent assignments listed — api, auth, db, frontend
- [x] Prompt caching strategy — **N/A**: no LLM prompt path in this feature (pure auth + DB); Policy v1 rule allows N/A marking with reason

## Spec Gaps (from clarify) — all handled
- GAP-01: `JWT_SECRET` vs `AUTH_SECRET_KEY` naming → resolved at /plan (use existing `AUTH_SECRET_KEY` + new `JWT_REFRESH_SECRET`)
- GAP-02: `_verify_local_jwt` query must extend `SELECT id` → `SELECT id, token_version` → captured for S002/T001
- GAP-03: `/v1/auth/token` additive `refresh_token` field → safe per C004

---

## Blockers
None.

## Warnings
None requiring approval.

## Next
→ Run `/plan security-audit`

# WARM Memory: security-audit
Created: 2026-04-23 | Status: IN_PROGRESS | Phase: /tasks S001 DONE → next: /analyze S001

## Plan
- Path: `docs/security-audit/plan/security-audit.plan.md` (2026-04-23)
- Critical path: **S001 → S002** (sequential; both touch `backend/auth/jwt.py` + `dependencies.py`)
- Parallel groups: G1=S001, G2=S002 (no parallelization — AGENTS.md auth rule)
- Token budget total: ~8k (plus ~1.5–3k near-scope from SI items)
- Agents: auth-agent (lead), api-agent, db-agent, frontend-agent

## Scope Impact (flagged at /plan)
- **SI-01 🔴**: Migration bumps `012 → 013` (`012_add_must_change_password.sql` already exists)
- **SI-02 🟡**: `_verify_local_jwt` SELECT must be extended (not just add column)
- **SI-03 🟡**: Frontend password touchpoints = 5 files (spec lists 2) — incl. `ChangePasswordModal.tsx`
- **SI-04 🟡**: `authStore.login()` signature change requires call-site sweep
- **SI-06 ✅**: OIDC refresh-token scope — D-SA-07: local HS256 only; OIDC users renew via IdP; reject with AUTH_UNSUPPORTED
- **SI-08 ✅**: Self-serve change-password bump — D-SA-08: YES — same atomic UPDATE+1 as admin; user gets fresh token

## Open items before /tasks
~~1. OIDC refresh-token scope (SI-06)~~ ✅ D-SA-07 resolved
~~2. Self-serve password-change token_version bump (Q9/SI-08)~~ ✅ D-SA-08 resolved
3. Confirm migration slot 013 is free — check before /tasks

---

## Spec Summary
Resolves 2 formally deferred security items from the change-password sprint.

| Story | Title | ACs | Status |
|-------|-------|-----|--------|
| S001 | Remove plaintext password from authStore + refresh-token endpoint | 10 | SPECIFIED |
| S002 | JWT session invalidation via token_version column | 10 | SPECIFIED |

**Total ACs:** 20 | **Assumptions:** 2 | **Blockers:** 0

---

## Key Decisions
- D-SA-01 (2026-04-23): Refresh token uses **separate `JWT_REFRESH_SECRET`** env var — confirmed by lb_mui 2026-04-23
- D-SA-02 (2026-04-23): Refresh token stored in memory (authStore) only — not localStorage — security boundary decision
- D-SA-03 (2026-04-23): `token_version` claim shortened to `tv` in JWT payload — avoids collision with standard claims
- D-SA-04 (2026-04-23): `token_version` check reuses existing user row fetch in `verify_token` (RBAC path) — no extra DB query (PERF P004)
- D-SA-07 (2026-04-23): `/v1/auth/refresh` is **local HS256 only** — OIDC users renew via IdP; `verify_refresh_token()` uses `JWT_REFRESH_SECRET` only; OIDC-format tokens rejected with AUTH_UNSUPPORTED (not AUTH_FAILED)
- D-SA-08 (2026-04-23): Self-serve `/v1/auth/change-password` **does bump `token_version`** — same atomic `token_version=token_version+1` UPDATE as admin path; user receives fresh access_token in response (no UX disruption; invalidates stolen tokens)

---

## S001 Tasks (7 tasks — /tasks DONE 2026-04-23)
File: `docs/security-audit/tasks/S001.tasks.md`
| Task | Title | Status |
|------|-------|--------|
| T001 | `jwt.py` — `create_refresh_token()` + `verify_refresh_token()` | TODO |
| T002 | `auth.py` — login response adds `refresh_token` | TODO |
| T003 | `auth.py` — `POST /v1/auth/refresh` route | TODO |
| T004 | `auth.py` login SELECT extends to `token_version` | TODO |
| T005 | `authStore.ts` — remove `password`, add `refreshToken` + refresh timer | TODO |
| T006 | Frontend callsites — `LoginForm`, `ChangePasswordPage`, `ChangePasswordModal` | TODO |
| T007 | `users.py` — self-serve bump `token_version` + 200 with new tokens | TODO |
Critical path: T001 → T002 → T004 → T005 → T007

## Files to Touch (by story)

### S001
- `backend/api/routes/auth.py` — add `/v1/auth/refresh` route; update `/v1/auth/token` to return refresh_token
- `backend/auth/jwt.py` — add `create_refresh_token()`, `verify_refresh_token()`
- `frontend/src/store/authStore.ts` — remove `password` field, add `refreshToken` field
- `frontend/src/pages/ChangePasswordPage.tsx` — replace `authStore.password` with silent refresh call
- `frontend/src/components/auth/LoginForm.tsx` — remove `password` arg from login() call [SI-04]
- `frontend/src/components/auth/ChangePasswordModal.tsx` — remove authStore.password ref [SI-03]
- `backend/api/routes/users.py` — bump token_version + return 200 with tokens [D-SA-08]

### S002
- `backend/db/migrations/013_add_token_version.sql` — ADD COLUMN + rollback section [SI-01: 012 taken]
- `backend/db/models/user.py` — add `token_version: int = 1`
- `backend/auth/jwt.py` — `create_access_token()` must embed `tv` claim
- `backend/auth/dependencies.py` (or `verify_token`) — add `tv` claim validation
- `backend/api/routes/admin.py` — atomic `UPDATE ... SET password_hash=..., token_version=token_version+1`

---

## Clarify Status (2026-04-23)
- Clarify: `docs/security-audit/clarify/security-audit.clarify.md`
- **BLOCKER Q1** ✅ RESOLVED: `JWT_REFRESH_SECRET` riêng — confirmed lb_mui 2026-04-23
- Q2 AUTO-ANSWERED: `_verify_local_jwt` does `SELECT id` only (not full row) — S002 must extend to `SELECT id, token_version` ([dependencies.py:83](backend/auth/dependencies.py#L83))
- GAP-01: Spec said "JWT_SECRET" — actual env var is `AUTH_SECRET_KEY`; use existing name + add `JWT_REFRESH_SECRET`
- Q3–Q6: default assumptions documented in clarify file (safe to proceed if Q1 answered)
- NICE Q7–Q9: non-blocking, deferred to /plan discussion

---

## Constitution Checks (passed)
- C003: `/v1/auth/refresh` is NOT exempt from auth — uses `verify_refresh_token` dependency ✅
- C004: No breaking change to `/v1/auth/token` or `/v1/auth/change-password` ✅
- R003: All new endpoints have auth dependency ✅
- R004: All new routes use `/v1/` prefix ✅
- A006: Migration file 012 precedes ORM update ✅
- PERF P004: token_version reuses existing user row fetch ✅

---

## Deferred Items Resolved
- DEFERRED-SEC-001 → S001 (this feature)
- DEFERRED-SEC-002 → S002 (this feature)

---

## Sync: 2026-04-23 (Session #116)
Decisions added: D-SA-01 (JWT_REFRESH_SECRET riêng — confirmed), D-SA-02 (memory-only refresh token), D-SA-03 (tv claim name)
Tasks changed: /specify → DONE, /clarify → DONE, Q1 BLOCKER → RESOLVED
Files touched:
  - docs/security-audit/spec/security-audit.spec.md (created + updated D-SA-01)
  - docs/security-audit/sources/security-audit.sources.md (created)
  - docs/security-audit/clarify/security-audit.clarify.md (created + Q1 resolved)
  - .claude/memory/WARM/security-audit.mem.md (created + updated)
  - .claude/memory/HOT.md (updated)
Questions resolved: Q1 (JWT_REFRESH_SECRET riêng), Q2 (auto-confirmed: SELECT id only in _verify_local_jwt:L83)
Spec gaps logged: GAP-01 (env var name), GAP-02 (SELECT extension), GAP-03 (additive response field)
New blockers: none
Status: CLARIFIED — 0 blockers → ready for /checklist

---

## Sync: 2026-04-23 (Session #117)
Decisions added: D-SA-05 (migration 012→013), D-SA-06 (S001/S002 sequential — auth rule)
Tasks changed: /checklist → PASS (29/30, 1 N/A), /plan → DONE
Files touched:
  - docs/security-audit/reviews/checklist.md (created — PASS)
  - docs/security-audit/plan/security-audit.plan.md (created — 2 stories, sequential, 10 scope-impact findings)
  - .claude/memory/WARM/security-audit.mem.md (updated — plan + SI summary)
  - .claude/memory/HOT.md (updated — session #117)
Questions resolved: none new
New blockers: none
Open items (non-blocking, resolve before /tasks S002):
  - SI-06 — OIDC refresh-token scope (default: local HS256 only per Q5 pattern)
  - SI-08 / Q9 — self-serve `/v1/auth/change-password` token_version bump (default: no)
Scope-impact catalog (10 items, full detail in plan):
  - 🔴 SI-01 migration rename 012→013
  - 🟡 SI-02 _verify_local_jwt SELECT extension
  - 🟡 SI-03 5 frontend password files (ChangePasswordModal added to scope)
  - 🟡 SI-04 authStore.login() signature sweep
  - 🟡 SI-05 /v1/auth/token response +refresh_token
  - 🟡 SI-06 OIDC scope (open)
  - 🟢 SI-07 admin handler verified
  - 🟡 SI-08 self-serve bump (open)
  - 🟡 SI-09 SPA proactive refresh timer lifecycle
  - 🟢 SI-10 no RAG surface touched
Status: PLANNED — ready for /tasks after SI-06 + SI-08 resolved

---

## Sync: 2026-04-23 (Session #118)
Decisions added: D-SA-07 (OIDC local HS256 only → AUTH_UNSUPPORTED), D-SA-08 (self-serve change-password bumps token_version → 200+tokens)
Tasks changed: /tasks S001 → DONE (7 tasks defined), /analyze S001 → DONE
Files touched:
  - docs/security-audit/tasks/S001.tasks.md (created — 7 tasks, T001→T002→T004→T005→T007 critical path)
  - docs/security-audit/tasks/S001.analysis.md (created — deep scan 10 files)
  - .claude/memory/WARM/security-audit.mem.md (updated — S001 task board, D-SA-07/08, SI-06/08 resolved)
  - .claude/memory/HOT.md (updated — session #118)
Questions resolved: SI-06 (D-SA-07), SI-08 (D-SA-08)
New blockers: none
Key analysis findings (carry into /implement):
  1. backend/auth/jwt.py does NOT exist — T001 creates it; extract jwt.encode from auth.py:L104
  2. LoginForm.tsx:L39–53 — inline refresh re-posts credentials (core DEFERRED-SEC-001 vuln)
  3. ChangePasswordPage.tsx:L14 reads authStore.password — needs new UI input (Option A: local state)
  4. ChangePasswordModal.tsx has no authStore.password ref (clean) but needs token update after T007
  5. test_users.py asserts 204 — must change to 200 after T007
  6. scheduleRefresh stays public; timer NOT inlined in login(); LoginForm uses refreshAccessToken as callback
Status: IN_PROGRESS — /tasks S001 DONE, /analyze S001 DONE → next: /implement S001 T001

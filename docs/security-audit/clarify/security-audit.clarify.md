# Clarify: security-audit
Generated: 2026-04-23 | Spec: v1 DRAFT | Stories: S001, S002

---

## BLOCKER — Must answer before /plan ✅ ALL RESOLVED

| # | Story | Question | Answer | Owner | Due |
|---|-------|----------|--------|-------|-----|
| Q1 | S001 | Should the refresh token use a **separate** `JWT_REFRESH_SECRET` env var, or the same `AUTH_SECRET_KEY` differentiated by a `sub_type: "refresh"` claim in the payload? | ✅ **Separate `JWT_REFRESH_SECRET`** env var — independent rotation, standard practice | lb_mui | 2026-04-23 |

---

## SHOULD — Assume if unanswered by sprint start

| # | Story | Question | Default assumption | Rationale |
|---|-------|----------|--------------------|-----------|
| Q2 | S002 | Does `verify_token` currently fetch the full user row (for RBAC `group_ids`) so `token_version` can be read from the same query? | **No — lightweight fetch only.** `_verify_local_jwt` currently does `SELECT id FROM users WHERE id=... AND is_active=TRUE` ([dependencies.py:83–88](backend/auth/dependencies.py#L83-L88)). A `token_version` column check will require upgrading this query to `SELECT id, token_version FROM users WHERE id=... AND is_active=TRUE`. | Auto-confirmed from source code; no extra DB round-trip if we extend the existing SELECT |
| Q3 | S001 | What is the intended refresh token TTL? Spec proposes 8 hours (standard workday). | **8 hours** — covers full workday without forcing re-login. Configurable via `AUTH_REFRESH_TOKEN_EXPIRE_HOURS` env var (default 8). | S005 env-var pattern; no hardcoding |
| Q4 | S001 | Should the frontend silently auto-refresh the access token proactively (e.g., at `exp - 5min`), or only on-demand when a 401 is received? | **Proactive refresh at `exp - 5min`** — consistent with existing D011 decision (`frontend/src/api/routes/auth.py` comment: "SPA does proactive refresh at exp-5min") | Avoids mid-request 401 flash; consistent with existing design intent |
| Q5 | S002 | Should `token_version` validation apply to **all** auth paths (local JWT, OIDC, API-key), or only local HS256 JWT? | **Local HS256 JWT only** — OIDC tokens are validated by the external IdP (Keycloak) which handles revocation natively; API-keys have their own revocation path (`api_keys.is_active` column). | Scoped to the risk: DEFERRED-SEC-002 is specifically about local password-reset flows |
| Q6 | S002 | Migration file number: should it be `012` (sequential from last known migration) or is there a gap to fill? | **012** — last confirmed migration in `backend/db/migrations/` is `011` (from change-password sprint). No gap known. | A006 naming convention |

---

## NICE — Won't block

| # | Story | Question |
|---|-------|----------|
| Q7 | S001 | Should the refresh endpoint return a `must_change_password` flag (same as `/v1/auth/token`) so the SPA can re-enforce the force-change gate after a silent refresh? |
| Q8 | S001 | Should failed refresh attempts (expired/tampered token) be written to the audit log? The spec currently says no, treating refresh as infrastructure — but some compliance frameworks expect it. |
| Q9 | S002 | Should `token_version` also be incremented when a user resets their **own** password (via `POST /v1/auth/change-password`), or only when an admin resets it? |

---

## Auto-answered from existing files

| # | Question | Answer source |
|---|----------|---------------|
| Q2 (partial) | Does verify_token fetch user row? | `backend/auth/dependencies.py:83–88` — `SELECT id FROM users WHERE id=... AND is_active=TRUE` (id only, not full row) → Q2 becomes SHOULD with known default |
| All /v1/ prefix | Must new endpoints use /v1/ prefix? | HARD R004 + CONSTITUTION C004 — confirmed ✅ |
| Auth on /v1/auth/refresh | Must refresh endpoint require auth? | CONSTITUTION C003 / HARD R003 — all /v1/* except /v1/health require auth ✅ |
| No breaking change | Can /v1/auth/token response be extended? | CONSTITUTION C004 — additive-only extension is non-breaking; no /v2/ needed ✅ |
| Migration-first | Can ORM be updated before migration? | ARCH A006 — migration file written and reviewed first, ORM updated after ✅ |
| Secret source | Can JWT_REFRESH_SECRET be hardcoded? | CONSTITUTION S005 / HARD R005 — all secrets via env vars only ✅ |
| Test coverage | What coverage is required? | CONSTITUTION Testing §: ≥80% for new code; integration tests for critical journeys (auth is critical) ✅ |

---

## Spec Gaps Found (agent-flagged, no human input needed)

| ID | Gap | Resolution |
|----|-----|------------|
| GAP-01 | `AUTH_SECRET_KEY` env var name differs from spec's `JWT_SECRET`. Spec text says "JWT_SECRET"; actual code uses `AUTH_SECRET_KEY` ([auth.py:33](backend/api/routes/auth.py#L33)). | Use `AUTH_SECRET_KEY` (existing) and add `JWT_REFRESH_SECRET` (new). Update spec text at /plan to align names. |
| GAP-02 | `_verify_local_jwt` uses minimal `SELECT id FROM users` — adding `token_version` requires extending to `SELECT id, token_version FROM users`. This is a code change, not just a new column check. | Captured as implementation detail for S002/T001 task. Not a spec blocker. |
| GAP-03 | `/v1/auth/token` login response currently does NOT include `refresh_token` field. Adding it is additive (non-breaking per C004), but existing SPA code that destructures the response must handle the new field gracefully. | Frontend stores `refreshToken` in authStore only — no risk of accidental consumption. Flag in /plan as safe additive change. |

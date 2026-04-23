# Plan: security-audit
Created: 2026-04-23 | Author: sonnet (/plan) | Based on: spec v1, checklist PASS, clarify (0 blockers)

---

## LAYER 1 — Plan Summary

```
Stories: 2  |  Sessions est.: 1–2  |  Critical path: S001 → S002
Parallel groups:
  G1 (sequential):  S001  — auth refresh-token + authStore cleanup
  G2 (after G1):    S002  — token_version column + verify_token check + admin reset bump
Token budget total: ~8k  (S001 ~4k + S002 ~4k)
Agents: auth-agent (lead), api-agent, db-agent, frontend-agent
```

### Why sequential (no parallelization)
- **AGENTS.md rule**: "Never parallelize auth stories + anything else." Both S001 and S002 are auth-layer.
- **Shared files**: Both stories modify `backend/auth/jwt.py` (token creation) and `backend/auth/dependencies.py` (`_verify_local_jwt`). Merge conflicts inevitable if run in parallel.
- **Logical chain**: S002's `token_version` claim (`tv`) must be embedded in tokens created by S001's `create_refresh_token()`. Building S001 first gives S002 a complete token-creation surface to extend.

---

## ⚠️ Scope Impact Analysis (per user request: "xem xét thêm phạm vi tác động")

### Critical findings flagged for /tasks + /analyze

| # | Finding | Impact | Action at /tasks |
|---|---------|--------|------------------|
| **SI-01** | 🔴 **Migration number collision** | Spec says `012_add_token_version.sql`, but `012_add_must_change_password.sql` already exists (committed in change-password sprint). | **Bump to `013_add_token_version.sql`**. Update spec AC1 + implementation notes at /tasks. |
| **SI-02** | 🟡 `_verify_local_jwt` DB query extension | `backend/auth/dependencies.py:84` currently does `SELECT id FROM users ...` — must extend to `SELECT id, token_version FROM users ...`. Confirmed in clarify Q2 + GAP-02. | Add as explicit subtask in S002 (not a pure column-add migration — requires query change). |
| **SI-03** | 🟡 **5 frontend files touch `password`** | `authStore.ts`, `LoginForm.tsx`, `ChangePasswordPage.tsx`, `ChangePasswordModal.tsx`, `index.css` (CSS only — styling, safe to ignore). Spec covers only 2 files. | /tasks S001 must enumerate all 5. `ChangePasswordModal.tsx` is an extra touchpoint not in spec. |
| **SI-04** | 🟡 `authStore.login()` signature change | Current: `login(token, username, password, mustChangePassword?)`. After S001: `login(accessToken, refreshToken, username, mustChangePassword?)`. This is a **call-site sweep** — every caller of `login()` must be updated. | Grep for `authStore.login(` or `login(` callers during /analyze. |
| **SI-05** | 🟡 `/v1/auth/token` login response shape | Currently returns `access_token + must_change_password` (auth.py:123). Adding `refresh_token` is additive (C004-safe) but SPA login handler must extract + persist it. | Map in /tasks: API route change + SPA login handler change must land in same PR. |
| **SI-06** | 🟡 **OIDC path scope** | Clarify Q5: `token_version` applies to **local HS256 only**. OIDC Keycloak tokens use IdP-native revocation. Refresh-token endpoint (S001) — clarify whether OIDC users also get a local refresh token or rely on OIDC's own refresh. | Add to /clarify SHOULD list at /tasks: does S001 issue refresh tokens for OIDC-authenticated users, or is S001 local-JWT-only? |
| **SI-07** | 🟢 Admin reset handler path verified | `backend/api/routes/admin.py:872` `admin_password_reset()` confirmed — uses `admin_password_reset:{user_id}` audit key. S002 AC5 (atomic UPDATE) is a clean extension to existing handler. | None — low risk. |
| **SI-08** | 🟡 **Self-serve change-password flow** | Clarify Q9 (NICE, unresolved): should `/v1/auth/change-password` (self-serve) also bump `token_version`? Spec says admin-reset only. If user changes own password and other sessions should die → needs Q9 answer. | Decision deferred to /tasks; if product says "bump on self-change too", adds ~0.5k tokens + 2 test cases. |
| **SI-09** | 🟡 Proactive refresh timer in SPA | Clarify Q4: SPA will proactively refresh at `exp - 5min`. Requires new timer in `authStore` (`_refreshTimer` field already exists — good). | /tasks S001 must include timer setup + teardown on logout. |
| **SI-10** | 🟢 No RAG / embedding / multilingual surface touched | Feature is pure auth + DB + frontend state. No impact on pgvector, BM25, CJK tokenizer, or query pipeline. | None. |

### Risk tiering for scope creep
- **Hard-scoped (in spec):** S001 + S002 ACs as written — ~8k tokens
- **Near-scope (likely to expand at /tasks):** SI-03 (5 files), SI-04 (call-site sweep), SI-09 (timer lifecycle) — adds ~1.5k
- **Decision-needed (may expand):** SI-06 (OIDC), SI-08 (self-serve bump) — adds ~1–2k if both enabled
- **Out-of-scope (stays deferred):** refresh token rotation, token blacklist, multi-device session mgmt (spec §"Out of Scope")

---

## LAYER 2 — Per-Story Plan

### S001: Remove plaintext password from authStore — refresh-token endpoint
Agent: **auth-agent** (primary) + **api-agent** + **frontend-agent**
Parallel: G1 (sequential, blocks S002)
Depends: none (change-password feature DONE)

**Files**

CREATE
- (none — all additive to existing files)

MODIFY — backend
- `backend/auth/jwt.py` — add `create_refresh_token(sub, token_version)`, `verify_refresh_token(token)`; uses `JWT_REFRESH_SECRET` env var (D-SA-01)
- `backend/auth/dependencies.py` — add `verify_refresh_token` dependency (separate from `verify_token` — only accepts refresh tokens)
- `backend/api/routes/auth.py` — (a) extend `POST /v1/auth/token` response to include `refresh_token`; (b) add `POST /v1/auth/refresh` route
- `backend/core/config.py` (or equivalent) — register `JWT_REFRESH_SECRET`, `AUTH_REFRESH_TOKEN_EXPIRE_HOURS` env vars

MODIFY — frontend
- `frontend/src/store/authStore.ts` — remove `password` field; add `refreshToken` field; update `login()` signature; add silent `refreshAccessToken()` action; wire `_refreshTimer` for proactive refresh at `exp - 5min` (Q4)
- `frontend/src/components/auth/LoginForm.tsx` — stop passing `password` to `login()`; use new signature
- `frontend/src/pages/ChangePasswordPage.tsx` — replace `authStore.password` with `await refreshAccessToken()` to obtain fresh access token before calling change-password endpoint
- `frontend/src/components/auth/ChangePasswordModal.tsx` — **[SI-03]** same treatment as ChangePasswordPage (modal variant)
- `frontend/src/api/auth.ts` (or `routes/auth.ts`) — add `refreshAccessToken()` HTTP client function
- `frontend/src/index.css` — no change (CSS contains only `password` selectors for styling)

TESTS
- `backend/tests/auth/test_refresh_token.py` — 4 paths: success, expired, tampered, missing header (AC9)
- `backend/tests/api/test_auth_routes.py` — existing tests updated for new `refresh_token` field in login response
- `frontend/src/store/authStore.test.ts` — verify no `password` field; refresh timer behavior; memory-only refreshToken
- `frontend/src/pages/ChangePasswordPage.test.tsx` — verify silent refresh call, no `authStore.password` access

**Env vars added**
- `JWT_REFRESH_SECRET` (required) — separate from `AUTH_SECRET_KEY`
- `AUTH_REFRESH_TOKEN_EXPIRE_HOURS` (default 8) — from clarify Q3
- `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` (confirm default 15) — align with spec AC2

**Rules check**
- ✅ R003: new endpoint is protected (verify_refresh_token dep)
- ✅ R004: `/v1/auth/refresh` uses `/v1/` prefix
- ✅ R005: secrets via env vars only
- ✅ R007: < 200ms (no RAG path)
- ✅ S005: no hardcoded secrets
- ✅ C004: additive response changes only; no `/v2/`
- ✅ A001: auth-agent owns `backend/auth/`; api-agent owns routes; no cross-import violations
- ✅ A005: error shape `{"error": {"code", "message", "request_id"}}`

Est. tokens: ~4k
Subagent dispatch: **YES** — self-contained, but orchestrate auth-agent → api-agent → frontend-agent in series (auth primitives must exist before route + SPA can call them)

---

### S002: JWT session invalidation on admin password reset — token_version
Agent: **db-agent** → **auth-agent** → **api-agent**
Parallel: G2 (after G1 complete)
Depends: **S001** (refresh token path must embed `tv` claim too)

**Files**

CREATE
- ⚠️ **`backend/db/migrations/013_add_token_version.sql`** — **[SI-01] renumbered from spec's 012** (012 already exists as `012_add_must_change_password.sql`)
  - Body: `ALTER TABLE users ADD COLUMN token_version INT NOT NULL DEFAULT 1;`
  - Rollback comment: `-- ROLLBACK: ALTER TABLE users DROP COLUMN token_version;`

MODIFY — backend
- `backend/db/models/user.py` — add `token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)` (after migration reviewed per A006)
- `backend/auth/jwt.py` — extend `create_access_token()` + `create_refresh_token()` (from S001) to accept `token_version` and embed as `tv` claim (D-SA-03)
- `backend/auth/dependencies.py` — **[SI-02]** change `_verify_local_jwt` SELECT from `SELECT id FROM users WHERE id=:user_id AND is_active=TRUE` → `SELECT id, token_version FROM users WHERE id=:user_id AND is_active=TRUE`; compare with `tv` claim; return `401 ERR_TOKEN_INVALIDATED` on mismatch
- `backend/api/routes/auth.py` — `/v1/auth/token` login: fetch user's current `token_version` (already in `SELECT id, password_hash, must_change_password` — extend to also read `token_version`), pass to `create_access_token` + `create_refresh_token`
- `backend/api/routes/admin.py` — `admin_password_reset()` at line 872: change password-update SQL to atomic `UPDATE users SET password_hash=:ph, token_version=token_version+1 WHERE id=:uid`

TESTS
- `backend/tests/db/test_user_model.py` — `token_version` field defaults to 1, increments
- `backend/tests/auth/test_token_version.py` — 4 paths: matching version passes, stale version rejected (ERR_TOKEN_INVALIDATED), increment on reset, new login post-reset issues valid token (AC9)
- `backend/tests/api/test_admin_routes.py` — atomic update (password_hash + token_version in same transaction); 401 on old JWT after reset (AC6)
- Load test: `verify_token` overhead < 5ms additional (AC8 — reuse existing SELECT)

**Rules check**
- ✅ R001 (RBAC before retrieval): check is on user row already fetched, no bypass
- ✅ R003, R004: unchanged
- ✅ R007 latency: no extra round-trip (extended SELECT, not new query)
- ✅ P004 (N+1): reuses single SELECT
- ✅ A006: migration file created + reviewed FIRST, ORM updated after
- ✅ S001 (SQL injection): atomic UPDATE uses named params (`:ph`, `:uid`) — no string interpolation

**Scope excluded** (per Q5)
- OIDC tokens: IdP handles revocation (not touched)
- API-key auth: `api_keys.is_active` handles revocation (not touched)
- `/v1/auth/change-password` self-serve bump: **Q9 deferred** — default is "no bump on self-change" unless product decides otherwise

Est. tokens: ~4k
Subagent dispatch: **YES** — db-agent writes migration first, pauses for /analyze review (A006), then auth-agent + api-agent extend

---

## Dispatch Order (execution)
```
1. /tasks security-audit --story S001
2. /analyze security-audit --story S001
3. /implement security-audit --story S001
4. /reviewcode security-audit --story S001
5. /tasks security-audit --story S002
6. /analyze security-audit --story S002   ← confirm SI-02 query extension details
7. /implement security-audit --story S002   ← db-agent migration first (A006)
8. /reviewcode security-audit --story S002
9. /report security-audit
```

---

## Open items to resolve before /tasks
1. **SI-06** — OIDC refresh-token scope: issue local refresh tokens for OIDC users, or OIDC-native only? (defaults to local HS256 only per Q5 pattern)
2. **SI-08 / Q9** — Bump `token_version` on self-serve `/v1/auth/change-password` too? (default: no)
3. **Migration number confirm** — `013` vs skip-to-next-available; verify no other in-flight migration grabs 013

> Recommend resolving 1 and 2 before /tasks S002 to avoid rework.

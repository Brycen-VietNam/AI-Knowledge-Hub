# Spec: security-audit
Created: 2026-04-23 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | security-hardening |
| Priority | P1 |
| Story count | 2 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 |
| Parallel-safe stories | None — S002 depends on S001 DB migration |
| Blocking specs | None |
| Blocked by | change-password (DONE ✅) |
| Agents needed | api-agent, auth-agent, db-agent, frontend-agent |

### Problem Statement
Two security risks were deferred during the `change-password` sprint: (1) raw password stored in JS heap via `authStore`, enabling XSS extraction during the session; (2) admin-reset JWTs stay valid up to 60 min after reset, allowing compromised sessions to persist. Both were accepted as short-term risk with a commitment to fix in the next security sprint.

### Solution Summary
- **S001**: Add `POST /v1/auth/refresh` endpoint; remove `password` field from `authStore`; `ChangePasswordPage` uses refresh token instead of stored plaintext password
- **S002**: Add `token_version INT` to `users` table; embed version in JWT on login; `verify_token` rejects mismatched version; admin password-reset increments `token_version`, immediately invalidating all existing sessions for that user
- Backend follows existing HARD rules: R003 (auth on every endpoint), R004 (/v1/ prefix), R006 (audit log)
- DB changes follow A006: numbered migration file first, ORM updated after review
- No breaking change to existing `/v1/auth/token` or `/v1/auth/change-password` contracts

### Out of Scope
- Refresh token rotation (rolling refresh tokens) — overkill for internal tool
- Revocation store / token blacklist — `token_version` column is sufficient
- Offline/PWA session handling
- Multi-device session management

---

## LAYER 2 — Story Detail

---

### S001: Remove plaintext password from authStore — add refresh-token endpoint

**Role / Want / Value**
- As a: security team member
- I want: the browser to never hold plaintext password in JS memory beyond the login moment
- So that: an XSS attack cannot exfiltrate the user's current password from the Zustand store

**Acceptance Criteria**
- [ ] AC1: `POST /v1/auth/refresh` endpoint exists and requires `Authorization: Bearer <refresh_token>` header
- [ ] AC2: `/v1/auth/refresh` returns a new `access_token` (15-min TTL) + new `refresh_token` (8-hour TTL); response shape identical to `/v1/auth/token`
- [ ] AC3: `/v1/auth/token` (login) returns both `access_token` and `refresh_token` in response body
- [ ] AC4: `authStore.ts` no longer contains a `password` field; any `setPassword()` / `clearPassword()` calls removed
- [ ] AC5: `ChangePasswordPage.tsx` no longer passes `authStore.password` as `current_password`; it obtains a fresh `access_token` via silent refresh before calling `POST /v1/auth/change-password`
- [ ] AC6: If refresh token is expired or invalid, `/v1/auth/refresh` returns `401 {"error": {"code": "ERR_REFRESH_EXPIRED", "message": "Refresh token expired or invalid", "request_id": "..."}}`
- [ ] AC7: `/v1/auth/refresh` requires authentication via refresh token; it is NOT exempt from auth (only `/v1/health` is exempt — CONSTITUTION C003)
- [ ] AC8: Refresh token is stored in `authStore` (memory only, not localStorage) with same lifecycle as existing access token
- [ ] AC9: Unit tests cover: successful refresh, expired refresh token, tampered refresh token, missing auth header
- [ ] AC10: Existing `POST /v1/auth/token` and `POST /v1/auth/change-password` contracts are not broken

**API Contract**
```
POST /v1/auth/refresh
Headers: Authorization: Bearer <refresh_token>
Body: (none)
Response 200: {
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "<jwt>"
}
Response 401: {"error": {"code": "ERR_REFRESH_EXPIRED", "message": "Refresh token expired or invalid", "request_id": "..."}}
```

**Auth Requirement**
- [x] OIDC Bearer (refresh token) — both human OIDC and API-key paths must produce refresh tokens

**Non-functional**
- Latency: < 200ms p95 (no RAG path — pure auth)
- Audit log: not required for token refresh (token refresh is infra, not document access)
- CJK support: not applicable

**Implementation notes**
- Refresh token: signed JWT, `sub_type: "refresh"` claim, signed with **`JWT_REFRESH_SECRET`** env var (separate from `AUTH_SECRET_KEY` — D-SA-01, confirmed 2026-04-23)
- `backend/auth/jwt.py` — add `create_refresh_token()` and `verify_refresh_token()` functions
- `backend/api/routes/auth.py` — add `/v1/auth/refresh` route; update `/v1/auth/token` to return refresh token
- `frontend/src/store/authStore.ts` — remove `password` field, add `refreshToken` field
- `frontend/src/pages/ChangePasswordPage.tsx` — replace `authStore.password` usage with `await refreshAccessToken()`
- CONSTITUTION C003: `/v1/auth/refresh` is a protected endpoint — `verify_refresh_token` dependency required, not `verify_token`

> **Decision D-SA-01** (confirmed 2026-04-23): Refresh token uses separate `JWT_REFRESH_SECRET` env var. Independent rotation — rotating `JWT_REFRESH_SECRET` invalidates all refresh tokens without affecting access tokens.

---

### S002: JWT session invalidation on admin password reset — token_version column

**Role / Want / Value**
- As a: system administrator
- I want: resetting a user's password to immediately invalidate all their existing JWT sessions
- So that: a compromised or handed-off session cannot remain active after a forced password reset

**Acceptance Criteria**
- [ ] AC1: Migration `012_add_token_version.sql` adds `token_version INT NOT NULL DEFAULT 1` column to `users` table, with rollback section
- [ ] AC2: ORM model `User` in `backend/db/models/user.py` includes `token_version: int = 1` field, updated after migration
- [ ] AC3: `POST /v1/auth/token` (login) embeds `token_version` as a claim in both access token and refresh token JWTs
- [ ] AC4: `verify_token` middleware reads `token_version` from JWT claim and validates it against DB; mismatch returns `401 {"error": {"code": "ERR_TOKEN_INVALIDATED", "message": "Session invalidated", "request_id": "..."}}`
- [ ] AC5: `POST /v1/admin/users/{id}/password-reset` increments `users.token_version` for the target user atomically (within the same DB transaction as the password hash update)
- [ ] AC6: After password reset, the target user's next request with old JWT returns `401 ERR_TOKEN_INVALIDATED`
- [ ] AC7: The token owner's own subsequent `/v1/auth/token` login with the new password produces a JWT with the incremented `token_version`, which passes `verify_token`
- [ ] AC8: `token_version` validation adds no DB round-trip beyond what `verify_token` already does (user row is already fetched for RBAC group lookup — reuse that query)
- [ ] AC9: Unit tests cover: valid token with matching version, token with stale version, version increment on reset, atomic increment + password update
- [ ] AC10: Existing admin password-reset API contract (`POST /v1/admin/users/{id}/password-reset`) is not broken — same request/response shape

**API Contract**
```
POST /v1/admin/users/{id}/password-reset   (no change to shape)
Headers: Authorization: Bearer <admin_access_token>
Body: {"new_password": "<string>"}
Response 200: {"message": "Password reset successfully"}
Response 401 (stale JWT after reset):
  {"error": {"code": "ERR_TOKEN_INVALIDATED", "message": "Session invalidated", "request_id": "..."}}
```

**Auth Requirement**
- [x] OIDC Bearer (human admin)
- [x] API-Key (bot/service account — if service resets passwords programmatically)

**Non-functional**
- Latency: `verify_token` overhead must stay < 5ms additional (reuse existing user row fetch — no extra query)
- Audit log: password reset already writes to audit_logs (R006 — existing behavior); `token_version` increment is part of same transaction, no separate log entry needed
- CJK support: not applicable

**Implementation notes**
- Migration filename: `backend/db/migrations/012_add_token_version.sql` (follows A006 naming)
- `token_version` claim name in JWT: `tv` (short, avoids collision with standard claims)
- `backend/auth/jwt.py` — `create_access_token()` must accept and embed `token_version`
- `backend/auth/dependencies.py` (or equivalent `verify_token`) — add version check after user fetch
- `backend/api/routes/admin.py` — `password_reset()` handler: atomic `UPDATE users SET password_hash=..., token_version=token_version+1 WHERE id=...`
- HARD rule R001: version check is on the user row already fetched — no raw retrieval bypass
- ARCH rule A006: migration file written + reviewed before ORM updated

> **Assumption**: The user row is already fetched inside `verify_token` for RBAC lookups. If not, a lightweight `SELECT token_version FROM users WHERE id=:sub` query must be added — confirm in /analyze.

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC3 | Existing behavior | `change-password` report — DEFERRED-SEC-001 | Refresh-token endpoint identified as fix for password-in-store risk | 2026-04-22 |
| AC4–AC5 | Existing behavior | `frontend/src/store/authStore.ts`, `frontend/src/pages/ChangePasswordPage.tsx` | `password` field currently set on login and used silently in ChangePasswordPage | 2026-04-22 |
| AC6–AC7 | Business logic | CONSTITUTION C003 + HARD R003 | All /v1/* require auth; /v1/health sole exception | 2026-03-18 |
| AC8 | Business logic | Security team decision — memory-only token storage | localStorage persists across browser restart — memory-only preferred for refresh token | 2026-04-22 |
| AC9 | Requirement doc | CONSTITUTION — Testing §: 80% coverage + integration tests for critical journeys | Auth is a critical journey | 2026-03-18 |
| AC10 | Existing behavior | `backend/api/routes/auth.py` current contract | Non-breaking extension per CONSTITUTION C004 | 2026-04-13 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2 | Existing behavior | `change-password` report — DEFERRED-SEC-002 | `token_version` column identified as fix for session persistence after reset | 2026-04-22 |
| AC3–AC4 | Business logic | HARD R003, ARCH A001 | `verify_token` is the auth boundary; version check must live here | 2026-03-18 |
| AC5 | Existing behavior | `backend/api/routes/admin.py` — `password_reset()` | Atomic update required to avoid race between hash + version updates | 2026-04-21 |
| AC6–AC7 | Conversation | `/clarify change-password` Q4 — 60-min TTL accepted risk; token_version fix deferred | Stakeholder acceptance of 60-min window documented; fix committed to security sprint | 2026-04-17 |
| AC8 | Business logic | PERF P004 — N+1 prevention; HARD R007 — latency SLA | Reuse existing user fetch to avoid extra DB round-trip | 2026-03-18 |
| AC9 | Requirement doc | CONSTITUTION — Testing §: 80% coverage | Security-touching code requires high test coverage | 2026-03-18 |
| AC10 | Existing behavior | `backend/api/routes/admin.py` current contract | Non-breaking — only internal behaviour changes (token_version increment) | 2026-04-21 |

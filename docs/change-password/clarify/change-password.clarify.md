# Clarify: change-password
Generated: 2026-04-22 | Spec: v1 DRAFT | Stories: S001–S005
Resolved: 2026-04-22 | All 4 blockers answered by lb_mui

---

## BLOCKER — Resolved ✅

| # | Question | Answer | Owner | Resolved |
|---|----------|--------|-------|----------|
| Q1 | Does `POST /v1/auth/token` return `must_change_password`, or separate `GET /v1/users/me`? | **A — Add to login response.** `auth.py` already queries `users` table; add `must_change_password` to same SELECT + return field. `LoginForm` stores it in `authStore`. | lb_mui | 2026-04-22 |
| Q2 | Force-change gate: omit "Current Password" field, or use stored password silently? | **A — Use `authStore.password` silently** (hidden, not shown to user). User only inputs New Password + Confirm. ⚠️ Security note recorded below. | lb_mui | 2026-04-22 |
| Q3 | Admin reset: always set `must_change_password = true`, or admin chooses? | **A — Always `true`.** Every admin reset forces user to change on next login. Simpler and more secure. | lb_mui | 2026-04-22 |
| Q4 | Session invalidation on admin reset — in scope or deferred? | **A — Deferred.** 60-min JWT TTL accepted as risk window. ⚠️ Deferred work recorded below. | lb_mui | 2026-04-22 |

---

## ⚠️ Security Note — Q2: Raw password in `authStore`

**Current behavior:** `authStore.ts:24` stores `password: string` in-memory (Zustand) after login. This enables proactive JWT refresh without re-prompting the user (`auth.py` uses username+password to re-issue tokens — no refresh-token flow exists yet).

**Risk assessment:**
- Stored in JS heap only (not `localStorage`, not cookies) — cleared on logout/tab close
- Not sent to any endpoint other than `/v1/auth/token`
- No XSS vector today (no user-generated HTML rendered)

**Why this is acceptable for now:**
- Scope-limited: raw password storage is an existing design decision (D002 in frontend-spa), not introduced by change-password
- The alternative (refresh-token flow or PKCE) would require significant auth refactor

**What should be fixed later (post change-password):**
- Implement a refresh-token endpoint (`POST /v1/auth/refresh`) so raw password no longer needs to be stored
- Once refresh-token exists, remove `password` from `authStore` entirely
- Tracked as: `DEFERRED-SEC-001: Remove raw password from authStore — implement refresh-token flow`

---

## ⚠️ Deferred Work — Q4: Session Invalidation

**Current behavior:** JWT is stateless HS256. After admin resets a user's password, the user's existing token remains valid until expiry (default 60 min, configured via `AUTH_TOKEN_EXPIRE_MINUTES`).

**Risk window:** Up to 60 minutes where old token still works after password reset.

**How to implement later (when needed):**
1. Add `token_version INT NOT NULL DEFAULT 1` to `users` table (new migration)
2. Include `token_version` in JWT payload at issue time (`auth.py`)
3. `verify_token` dependency checks `token.token_version == db.users.token_version`
4. Admin reset increments `token_version` → all existing tokens immediately invalid
5. Self-service password change can optionally increment too (invalidates other devices)

**Tracked as:** `DEFERRED-SEC-002: JWT session invalidation on password reset — implement token_version in users table`

---

## SHOULD — Confirmed assumptions

| # | Question | Decision |
|---|----------|----------|
| Q5 | `GET /v1/admin/users` return `has_password: bool`? | **Yes** — add `(password_hash IS NOT NULL) AS has_password` to SELECT in `admin_list_users()`. No schema change. |
| Q6 | `ChangePasswordModal` from user pill dropdown or profile page? | **Dropdown** — add "Change Password" item to `.user-pill` in `App.tsx`. No new page for self-service. |
| Q7 | bcrypt cost factor? | **Keep 12** — consistent with existing `admin.py:424`. |
| Q8 | Password maximum length? | **Cap at 128 chars** — return 422 `ERR_PASSWORD_TOO_LONG`. bcrypt truncates at 72 bytes; guard against DoS. |
| Q9 | i18n keys exist? | **No — add** `auth.change_password.*` namespace to all 4 language files. |

---

## NICE — Won't block

| # | Question | Default |
|---|----------|---------|
| Q10 | Force-change page explanation banner in all 4 languages? | Yes — use i18n key `auth.force_change.notice` |
| Q11 | Password strength indicator? | Out of scope — deferred |
| Q12 | "Reset Password" button position in UsersTab — next to "Delete" or in expandable row? | Next to "Delete" button (row-level action, same pattern) |

---

## Auto-answered from existing files

| # | Question | Answer | Source |
|---|----------|--------|--------|
| A1 | Does `GET /v1/users/me` exist? | **No** — must create in S001 (`backend/api/routes/users.py`) | `backend/api/routes/` — no `users.py` |
| A2 | Does `generate_password()` helper exist? | **No** — `admin.py:375` uses `secrets.token_hex(16)` inline. Extract to `backend/auth/utils.py`. | `backend/api/routes/admin.py:375` |
| A3 | Does login response include `must_change_password`? | **No** — add per Q1 resolution. | `backend/api/routes/auth.py:116–121` |
| A4 | Does `GET /v1/admin/users` return `has_password`? | **No** — add per Q5 decision. | `backend/api/routes/admin.py:766–776` |
| A5 | Does user pill support dropdown? | **No** — static div only. Must add click handler + dropdown for S003. | `frontend/src/App.tsx:39–44` |
| A6 | Does `ProtectedRoute` support `must_change_password` gate? | **No** — checks `token !== null` only. Gate logic to add in S005. | `frontend/src/components/auth/ProtectedRoute.tsx:11–17` |
| A7 | Does `authStore` store raw password? | **Yes** — `authStore.ts:11,24`. Used silently in S005 force-change. See ⚠️ security note above. | `frontend/src/store/authStore.ts:11,24` |
| A8 | Is bcrypt used? | **Yes** — `admin.py:424`, `auth.py:86`. | codebase |
| A9 | Migration for `must_change_password` exists? | **No** — next will be `012_add_must_change_password.sql`. | `backend/db/migrations/` |
| A10 | OIDC detection pattern? | **Yes** — `stored_hash is None` check in `auth.py:84–88`. Reuse in S001/S002. | `backend/api/routes/auth.py:84` |

---

## Summary

**Status: UNBLOCKED ✅** — All 4 blockers resolved. Ready for `/checklist change-password`.

**Spec changes needed before /plan:**
- S001: Update `GET /v1/users/me` contract + add `must_change_password` to login response
- S001: Add `ERR_PASSWORD_TOO_LONG` (AC new) — 128-char max
- S002: Confirm AC8 wording: always set `must_change_password = true` (no option)
- S003: Add user-pill dropdown to `App.tsx` as prerequisite
- S005: Update AC4 — `authStore.password` used silently (not shown to user)

**Deferred items:**
- `DEFERRED-SEC-001`: Remove raw password from authStore → implement refresh-token flow
- `DEFERRED-SEC-002`: JWT session invalidation → implement `token_version` in `users` table

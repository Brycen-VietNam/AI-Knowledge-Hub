# Spec: change-password
Created: 2026-04-22 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | auth |
| Priority | P1 |
| Story count | 5 |
| Token budget est. | ~5k |
| Critical path | S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S003 + S004 (frontend parallel after S001); S005 depends on S003 |
| Blocking specs | — |
| Blocked by | user-management (DONE — `users` table with `password_hash`, `POST /v1/admin/users`) |
| Agents needed | api-agent (S001–S002), frontend-agent (S003–S004) |

### Problem Statement
Users created via admin have no way to change their own password after login.
Admin has no way to force-reset a user's password without recreating the account.
Self-service password change is required for basic security hygiene and user autonomy.

### Solution Summary
- `PATCH /v1/users/me/password` — authenticated user changes their own password (current + new)
- `POST /v1/admin/users/{id}/password-reset` — admin force-sets any user's password
- Backend: `must_change_password` flag on `users` table — set `true` on create, cleared on first self-service change
- Frontend: **Force-change gate** — after login if `must_change_password=true`, redirect to `ChangePasswordPage` before any other route
- Frontend: `ChangePasswordModal` in user profile menu (self-service, repeat use)
- Frontend: "Reset Password" action in `UsersTab` admin panel (admin force-reset)
- CSS: all modal and page styles defined in `frontend/src/index.css` using global CSS classes (no inline styles, no CSS modules)

### Out of Scope
- Forgot-password / email-based reset flow (requires email service — deferred)
- OIDC users (password_hash is NULL — skip silently)
- Password expiry / rotation policy enforcement
- Password history (prevent reuse) — deferred
- Multi-factor authentication

---

## LAYER 2 — Story Detail

---

### S001: Backend — PATCH /v1/users/me/password (Self-Service Change)

**Role / Want / Value**
- As a: logged-in human user
- I want: to change my own password by providing my current password and a new one
- So that: I can maintain account security without involving an admin

**Acceptance Criteria**
- [ ] AC1: `PATCH /v1/users/me/password` requires valid OIDC Bearer token (human users only; API-key rejected with 403)
- [ ] AC2: Request body: `{"current_password": "...", "new_password": "..."}` — both required
- [ ] AC3: `current_password` is verified against stored `password_hash` using bcrypt — mismatch returns 400 `ERR_WRONG_PASSWORD`
- [ ] AC4: `new_password` minimum 8 characters; fails < 8 with 422 `ERR_PASSWORD_TOO_SHORT`
- [ ] AC5: On success, `password_hash` updated in `users` table AND `must_change_password` set to `false`; returns 204 No Content
- [ ] AC6: OIDC users (password_hash IS NULL) receive 400 `ERR_PASSWORD_NOT_APPLICABLE`
- [ ] AC7: Route protected by `Depends(verify_token)` — no anonymous access (R003)
- [ ] AC8: Audit log entry written: `user_id`, action=`password_change`, `timestamp` (R006 extension)
- [ ] AC9: `POST /v1/auth/token` login response includes `must_change_password: bool` (added to existing response — no extra round-trip)
- [ ] AC10: `new_password` maximum 128 characters; fails > 128 with 422 `ERR_PASSWORD_TOO_LONG` (bcrypt DoS guard)

**API Contract**
```
PATCH /v1/users/me/password
Headers: Authorization: Bearer <oidc_token>
Body: {"current_password": "string", "new_password": "string"}
Response 204: (empty) — password updated, must_change_password = false
Response 400: {"error": {"code": "ERR_WRONG_PASSWORD", "message": "...", "request_id": "..."}}
Response 400: {"error": {"code": "ERR_PASSWORD_NOT_APPLICABLE", "message": "...", "request_id": "..."}}
Response 403: {"error": {"code": "ERR_API_KEY_NOT_ALLOWED", "message": "...", "request_id": "..."}}
Response 422: {"error": {"code": "ERR_PASSWORD_TOO_SHORT", "message": "...", "request_id": "..."}}
Response 422: {"error": {"code": "ERR_PASSWORD_TOO_LONG", "message": "...", "request_id": "..."}}

POST /v1/auth/token (existing — extended)
Response 200: {"access_token": "...", "token_type": "bearer", "expires_in": N,
               "is_admin": bool, "must_change_password": bool}
```

**Auth Requirement**
- [x] OIDC Bearer (human) — only; API-key callers (bots) rejected with 403

**Non-functional**
- Latency: < 500ms p95 (bcrypt cost factor ≤ 12)
- Audit log: required (action = `password_change`)
- CJK support: not applicable

**Implementation notes**
- Reuse `verify_token` from `backend/auth/`. Add `is_human_user` guard (API-key → 403).
- bcrypt via `passlib[bcrypt]` — already used in user-management.
- Route file: `backend/api/routes/users.py` (new file, separate from admin routes).

---

### S002: Backend — POST /v1/admin/users/{id}/password-reset (Admin Force-Reset)

**Role / Want / Value**
- As a: platform admin
- I want: to force-set any user's password without knowing their current one
- So that: I can unlock accounts and onboard users who haven't self-served

**Acceptance Criteria**
- [ ] AC1: `POST /v1/admin/users/{id}/password-reset` requires `require_admin` dependency
- [ ] AC2: Request body: `{"new_password": "string"}` — required; or `{"generate": true}` for auto-generated 16-char password
- [ ] AC3: When `generate: true`, response 200 returns `{"password": "plaintext_once"}` — only time plaintext is shown
- [ ] AC4: When explicit `new_password` provided, response 204 No Content
- [ ] AC5: `new_password` minimum 8 characters; `generate: true` always produces ≥ 16 chars
- [ ] AC6: If user does not exist, returns 404 `ERR_USER_NOT_FOUND`
- [ ] AC7: OIDC users (password_hash IS NULL) receive 400 `ERR_PASSWORD_NOT_APPLICABLE`
- [ ] AC8: On success, `must_change_password` is set to `true` for the target user — forces them to change password on next login
- [ ] AC9: Audit log entry: `admin_user_id`, target `user_id`, action=`admin_password_reset`, `timestamp`
- [ ] AC10: Route follows R003 (auth), R004 (/v1/ prefix), A005 (error shape)

**API Contract**
```
POST /v1/admin/users/{id}/password-reset
Headers: Authorization: Bearer <admin_token>
Body (explicit): {"new_password": "string"}
Body (generated): {"generate": true}
Response 200: {"password": "plaintext_value"}   ← only when generate=true
Response 204: (empty)                            ← when new_password provided
Response 400: {"error": {"code": "ERR_PASSWORD_NOT_APPLICABLE", ...}}
Response 404: {"error": {"code": "ERR_USER_NOT_FOUND", ...}}
Response 422: {"error": {"code": "ERR_PASSWORD_TOO_SHORT", ...}}
```

**Auth Requirement**
- [x] OIDC Bearer (human) via `require_admin` dependency

**Non-functional**
- Latency: < 500ms p95
- Audit log: required (action = `admin_password_reset`)
- CJK support: not applicable

**Implementation notes**
- Route file: `backend/api/routes/admin/users.py` (append to existing admin user routes).
- Reuse `generate_password()` helper from user-management S001 if it exists; otherwise create in `backend/auth/utils.py`.

---

### S003: Frontend — ChangePasswordModal (Self-Service)

**Role / Want / Value**
- As a: logged-in user
- I want: a modal to change my password from the user profile menu
- So that: I can manage my own credentials from the UI

**Acceptance Criteria**
- [ ] AC1: Profile menu (top-right user pill) has "Change Password" option — hidden for OIDC users (no password_hash)
- [ ] AC2: `ChangePasswordModal` has fields: Current Password, New Password, Confirm New Password — all type=password
- [ ] AC3: Client-side: New Password and Confirm must match before submit; mismatch shows inline error
- [ ] AC4: Client-side: New Password ≥ 8 characters validated before submit
- [ ] AC5: On submit, calls `PATCH /v1/users/me/password`; success shows toast "Password changed" and closes modal
- [ ] AC6: `ERR_WRONG_PASSWORD` shows inline error "Current password is incorrect"
- [ ] AC7: `ERR_PASSWORD_NOT_APPLICABLE` hides the "Change Password" menu item (OIDC path)
- [ ] AC8: Loading state on submit button; disabled while request in-flight
- [ ] AC9: All user-facing strings use i18n keys (no hardcoded English/Japanese strings in JSX)

**Auth Requirement**
- [x] OIDC Bearer (human) — token from existing auth context

**Non-functional**
- Latency: UI response < 200ms; API call async
- Audit log: not applicable (backend handles)
- CJK support: i18n strings for ja / en / vi / ko

**Implementation notes**
- New component: `frontend/src/components/auth/ChangePasswordModal.tsx`
- Wire into existing profile/user pill in `App.tsx` or `Header.tsx`.
- Reuse existing modal pattern from admin-spa (e.g. `UserFormModal`).
- **CSS**: All styles in `frontend/src/index.css` — add classes:
  - `.change-password-modal` — modal container (reuse `.modal` base if exists)
  - `.change-password-form` — form layout (vertical stack, gap)
  - `.change-password-field` — label + input group
  - `.change-password-error` — inline error text (red, small)
  - `.change-password-actions` — button row (right-align: Cancel + Submit)
  - No inline styles, no CSS modules, no Tailwind.

> **Assumption**: Profile/user pill already exists in the header (from frontend-spa). Confirm or /clarify.

---

### S004: Frontend — Admin Reset Password Action in UsersTab

**Role / Want / Value**
- As a: platform admin
- I want: a "Reset Password" button per user row in the Users tab
- So that: I can force-reset a user's password from the admin UI

**Acceptance Criteria**
- [ ] AC1: Each non-OIDC user row in `UsersTab` has a "Reset Password" button
- [ ] AC2: Clicking "Reset Password" opens `ResetPasswordModal` with options: enter new password OR auto-generate
- [ ] AC3: Auto-generate: calls `POST /v1/admin/users/{id}/password-reset` with `{"generate": true}`; shows generated password in a copyable field with one-time warning
- [ ] AC4: Manual: calls same endpoint with `{"new_password": "..."}` after client validation (≥ 8 chars)
- [ ] AC5: Success toast shown; modal closes; no page reload needed
- [ ] AC6: OIDC users (identifiable via user.has_password flag or absence of password_hash) do not show "Reset Password" button
- [ ] AC7: All user-facing strings use i18n keys
- [ ] AC8: Loading state on submit; disabled while in-flight

**Auth Requirement**
- [x] OIDC Bearer (admin) — token from existing auth context

**Non-functional**
- Latency: UI response < 200ms; API call async
- Audit log: not applicable (backend handles)
- CJK support: i18n strings for ja / en / vi / ko

**Implementation notes**
- New component: `frontend/src/components/admin/ResetPasswordModal.tsx`
- Wire into existing `UsersTab` component (from user-management S008).
- Reuse `ApiKeyPanel` copy-to-clipboard pattern for the generated password display.
- **CSS**: All styles in `frontend/src/index.css` — add classes:
  - `.reset-password-modal` — modal container
  - `.reset-password-options` — radio/toggle area (manual vs generate)
  - `.reset-password-generated` — generated password display box (monospace, bordered, copyable)
  - `.reset-password-copy-btn` — copy button beside generated password
  - `.reset-password-warning` — one-time warning text (amber/orange, small)
  - `.reset-password-actions` — button row
  - No inline styles, no CSS modules, no Tailwind.

> **Assumption**: `UsersTab` user objects include a boolean indicating whether the user has a password (vs OIDC). Backend API may need to expose `has_password: bool` in user list response. Confirm or /clarify.

---

### S005: Frontend — Force-Change Password Gate (First Login)

**Role / Want / Value**
- As a: newly created user logging in for the first time
- I want: to be required to change my password before accessing any other page
- So that: the admin-set initial password is replaced with a personal one immediately

**Acceptance Criteria**
- [ ] AC1: After successful login, frontend checks `must_change_password` from `/v1/users/me` (or login response)
- [ ] AC2: If `must_change_password === true`, user is redirected to `/change-password` route (full page, not modal)
- [ ] AC3: All other routes are blocked while `must_change_password === true` — any direct URL attempt redirects to `/change-password`
- [ ] AC4: `ChangePasswordPage` uses `PATCH /v1/users/me/password`; "Current Password" field is hidden — `authStore.password` is passed silently as `current_password` in the request body (user only inputs New Password + Confirm)
- [ ] AC5: On successful change, `must_change_password` is cleared, user is redirected to `/` (home/query page)
- [ ] AC6: "Cancel" / "Skip" is not available on the force-change page — user cannot dismiss it
- [ ] AC7: All user-facing strings use i18n keys (ja / en / vi / ko)
- [ ] AC8: OIDC users (`must_change_password` will always be `false`) are never shown this page

**Auth Requirement**
- [x] OIDC Bearer (human) — user is already authenticated at this point

**Non-functional**
- Latency: redirect decision < 50ms (client-side check, no extra network call if login response includes flag)
- Audit log: not applicable (S001 handles it on `PATCH /v1/users/me/password`)
- CJK support: i18n strings for ja / en / vi / ko

**Implementation notes**
- New page: `frontend/src/pages/ChangePasswordPage.tsx`
- New route: `/change-password` in `App.tsx` router
- Guard logic: in `ProtectedRoute` or `App.tsx` — if `must_change_password`, redirect before rendering any guarded page
- **CSS**: All styles in `frontend/src/index.css` — add classes:
  - `.force-change-page` — full-page centered layout (card on white/brand bg)
  - `.force-change-card` — card container (same as `.login-card` if exists)
  - `.force-change-title` — heading ("Please set a new password")
  - `.force-change-notice` — notice banner (blue/info, explains why this is required)
  - `.force-change-form` — form layout (reuse `.change-password-form` where possible)
  - `.force-change-submit` — primary submit button (full width)
  - No inline styles, no CSS modules, no Tailwind.

> **Assumption**: Login response (or `/v1/users/me`) includes `must_change_password: bool`. Confirm at /clarify.
> **Assumption**: Force-change gate omits "Current Password" field (admin set it; user doesn't know it). Confirm or /clarify.

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Business logic | CONSTITUTION.md C003 | All /v1/* require auth; API-key bots have no "self" context | 2026-04-22 |
| AC2 | Business logic | Standard password-change UX pattern | Require current password to prevent session hijack | 2026-04-22 |
| AC3 | Existing behavior | user-management S001 (bcrypt) | bcrypt already used for password storage | 2026-04-22 |
| AC4 | Business logic | Industry minimum / NIST 800-63 | 8-char minimum is widely accepted baseline | 2026-04-22 |
| AC5 | Business logic | S005 AC1 dependency + REST convention | must_change_password must be cleared on success for gate to lift | 2026-04-22 |
| AC6 | Existing behavior | user-management spec Out of Scope | OIDC users have NULL password_hash — unsupported | 2026-04-22 |
| AC7 | HARD.md R003 | Auth on every endpoint | Applies to all /v1/* routes | 2026-04-22 |
| AC8 | HARD.md R006 | Audit log on document access | Extended to auth events for security hygiene | 2026-04-22 |
| AC9 | Business logic | S005 AC1 requirement | Frontend needs flag to implement force-change gate | 2026-04-22 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Existing behavior | user-management S003/S004 (require_admin) | Reuse admin guard pattern | 2026-04-22 |
| AC2 | Business logic | Admin UX — unlock / onboard flow | Admin may not know current password | 2026-04-22 |
| AC3 | Existing behavior | user-management S001 D2 (one-time plaintext) | Same pattern: generated password shown once | 2026-04-22 |
| AC4 | Business logic | REST convention | 204 when no body to return | 2026-04-22 |
| AC5 | Business logic | Security hygiene | Generated passwords should exceed manual minimum | 2026-04-22 |
| AC6 | Business logic | Standard CRUD error | User not found → 404 | 2026-04-22 |
| AC7 | Existing behavior | user-management spec OIDC note | NULL password_hash = OIDC user | 2026-04-22 |
| AC8 | HARD.md R006 | Audit log | Admin action on another user's credentials is high-risk event | 2026-04-22 |
| AC9 | HARD.md R003, R004, A005 | Hard rules | Route, prefix, error shape standards | 2026-04-22 |

### S003 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Business logic | UX: hide irrelevant options for OIDC users | Prevents confusion; OIDC users cannot use password change | 2026-04-22 |
| AC2 | Business logic | Standard change-password UX | Three fields: current, new, confirm | 2026-04-22 |
| AC3 | Business logic | Client-side validation before network call | Reduce unnecessary API calls | 2026-04-22 |
| AC4 | Business logic | Matches AC4 of S001 | Consistent 8-char minimum across UI + API | 2026-04-22 |
| AC5 | Business logic | Standard form submit flow | Toast + close on success | 2026-04-22 |
| AC6 | Existing behavior | S001 API error shape | Map ERR_WRONG_PASSWORD to user-friendly message | 2026-04-22 |
| AC7 | Existing behavior | S001 AC6 | OIDC path: no password_hash | 2026-04-22 |
| AC8 | Business logic | UX: prevent double-submit | Loading state is standard practice | 2026-04-22 |
| AC9 | CONSTITUTION.md | Language in Code + multilingual principle | i18n mandatory; no hardcoded strings | 2026-04-22 |

### S004 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Business logic | Admin needs per-user action | Row-level action button pattern from UsersTab | 2026-04-22 |
| AC2 | Business logic | Admin workflow: manual or auto-generate | Mirrors S002 API options | 2026-04-22 |
| AC3 | Existing behavior | user-management S001 D2 + ApiKeyPanel copy pattern | Generated password shown once, copyable | 2026-04-22 |
| AC4 | Business logic | Matches S002 AC5 minimum | Consistent validation | 2026-04-22 |
| AC5 | Business logic | UX: no page reload | SPA pattern; toast notification | 2026-04-22 |
| AC6 | Business logic | Mirrors S003 AC1 | OIDC users: hide reset button | 2026-04-22 |
| AC7 | CONSTITUTION.md | Multilingual principle | i18n mandatory | 2026-04-22 |
| AC8 | Business logic | UX: prevent double-submit | Loading state | 2026-04-22 |

### S005 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1 | Business logic | S001 AC9 + S002 AC8 | Backend exposes and controls the flag | 2026-04-22 |
| AC2 | Business logic | Security requirement | User must change before accessing platform | 2026-04-22 |
| AC3 | Business logic | Security requirement | Route guard prevents bypass via direct URL | 2026-04-22 |
| AC4 | Business logic | UX — force-gate context | Admin set the password; user doesn't know it; omit current-password field | 2026-04-22 |
| AC5 | Business logic | S001 AC5 clears flag | Gate lifts when PATCH succeeds | 2026-04-22 |
| AC6 | Business logic | Security requirement | No skip — force is mandatory | 2026-04-22 |
| AC7 | CONSTITUTION.md | Multilingual principle P003 | All strings via i18n | 2026-04-22 |
| AC8 | Business logic | S001 AC9 — OIDC users never have flag set | OIDC users always skip this gate | 2026-04-22 |

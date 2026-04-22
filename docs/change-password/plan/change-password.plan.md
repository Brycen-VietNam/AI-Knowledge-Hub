# Plan: change-password
Generated: 2026-04-22 | Spec: v1 DRAFT | Checklist: PASS ✅

---

## Layer 1 — Plan Summary

| Field | Value |
|-------|-------|
| Stories | 5 (S001–S005) |
| Sessions est. | 2 |
| Critical path | S001 → S002 → S003+S004 (parallel) → S005 |
| Token budget total | ~14k |
| Agents | api-agent (S001–S002), frontend-agent (S003–S005) |

### Parallel Groups

| Group | Stories | Condition |
|-------|---------|-----------|
| G1 | S001 (api-agent) | first — migration + self-service endpoint |
| G2 | S002 (api-agent) | after G1 — admin reset endpoint, shares users.py pattern |
| G3 | S003 (frontend-agent) + S004 (frontend-agent) | after G1 complete, API contract locked — parallel-safe (different files) |
| G4 | S005 (frontend-agent) | after G3 — depends on ChangePasswordModal pattern + authStore gate |

> Note: S003 and S004 touch different files (`ChangePasswordModal.tsx` vs `ResetPasswordModal.tsx` + `UsersTab.tsx`). Parallel-safe per AGENTS.md.
> auth-agent NOT dispatched — reuse existing `verify_token` and `require_admin` from backend/auth/. No auth boundary changes needed.

---

## Layer 2 — Per-Story Plans

---

### S001: Backend — PATCH /v1/users/me/password (Self-Service)
**Agent:** api-agent | **Group:** G1 | **Depends:** none (user-management DONE)
**Sequential** — foundational: migration + login response change affect all downstream stories

**Files:**
```
CREATE: backend/db/migrations/012_add_must_change_password.sql
MODIFY: backend/db/models/user.py                          — add must_change_password field
MODIFY: backend/api/routes/auth.py (line 116–121)          — add must_change_password to login response SELECT + return
CREATE: backend/api/routes/users.py                        — new route file: PATCH /v1/users/me/password
MODIFY: backend/api/routes/__init__.py (or main router)    — register users router
MODIFY: backend/auth/utils.py                              — extract generate_password() from admin.py:375
```

**Key implementation notes:**
- Migration first: `ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT TRUE;`
- Rollback: `ALTER TABLE users DROP COLUMN must_change_password;`
- `PATCH /v1/users/me/password`: requires `Depends(verify_token)` + `is_human_user` guard (API-key → 403)
- OIDC check: `if stored_hash is None → 400 ERR_PASSWORD_NOT_APPLICABLE` (pattern from auth.py:84)
- bcrypt verify current → update hash → set `must_change_password = False`
- Password length: assert `8 ≤ len(new_password) ≤ 128` before bcrypt call
- Audit log: `await audit_log.write(user_id, action="password_change", timestamp)`
- Login response: add `must_change_password: bool` to SELECT + `LoginResponse` schema

**Est. tokens:** ~3k
**Test:** `pytest tests/api/test_users.py tests/api/test_auth.py -v`
**Subagent dispatch:** YES — self-contained; returns diff + migration SQL + test result

---

### S002: Backend — POST /v1/admin/users/{id}/password-reset (Admin Force-Reset)
**Agent:** api-agent | **Group:** G2 | **Depends:** S001 (users.py file, generate_password helper)
**Sequential** — must follow S001 (reuses helper, appends to admin routes)

**Files:**
```
MODIFY: backend/api/routes/admin/users.py                  — append POST /v1/admin/users/{id}/password-reset
MODIFY: backend/api/routes/admin/users.py (list endpoint)  — add has_password: (password_hash IS NOT NULL) to SELECT
MODIFY: backend/auth/utils.py                              — use generate_password() (extracted in S001)
```

**Key implementation notes:**
- Route: `POST /v1/admin/users/{id}/password-reset` with `Depends(require_admin)`
- Body: `{"new_password": str} | {"generate": true}` — Pydantic union or discriminated model
- When `generate=true`: call `generate_password(length=16)` → hash → store → return `{"password": plaintext}` 200
- When `new_password` provided: hash → store → return 204 No Content
- Always set `must_change_password = True` on target user (D-CP-03)
- OIDC check: `if user.password_hash is None → 400 ERR_PASSWORD_NOT_APPLICABLE`
- 404: `if user not found → ERR_USER_NOT_FOUND`
- Audit log: `admin_user_id`, `target_user_id`, `action="admin_password_reset"`, `timestamp`
- `GET /v1/admin/users` list: add `(password_hash IS NOT NULL) AS has_password` to SELECT

**Est. tokens:** ~2k
**Test:** `pytest tests/api/test_admin_users.py -v`
**Subagent dispatch:** YES — append-only to existing file; returns diff + test result

---

### S003: Frontend — ChangePasswordModal (Self-Service)
**Agent:** frontend-agent | **Group:** G3 | **Depends:** S001 (API contract locked)
**Parallel-safe with S004** — different files, no shared state

**Files:**
```
CREATE: frontend/src/components/auth/ChangePasswordModal.tsx
MODIFY: frontend/src/App.tsx (lines 39–44)                 — add dropdown to user pill + "Change Password" item
MODIFY: frontend/src/index.css                             — append CSS classes (see below)
MODIFY: frontend/src/i18n/<lang>.json (×4)                — add auth.change_password.* keys (ja/en/vi/ko)
```

**CSS classes to add to index.css:**
```
.change-password-modal
.change-password-form
.change-password-field
.change-password-error
.change-password-actions
```

**Key implementation notes:**
- Hide "Change Password" from profile menu when `user.has_password === false` (OIDC users)
- Client validation before submit: new === confirm, len(new) ≥ 8
- On submit: `PATCH /v1/users/me/password` with Bearer token from authStore
- Success: toast "Password changed" + close modal
- `ERR_WRONG_PASSWORD` → inline error on Current Password field
- Loading state on submit button while request in-flight
- Reuse existing modal pattern (e.g. UserFormModal structure)

**Est. tokens:** ~3k
**Test:** `npm test -- --testPathPattern=ChangePasswordModal`
**Subagent dispatch:** YES — new file + CSS append; parallel with S004

---

### S004: Frontend — Admin ResetPasswordModal in UsersTab
**Agent:** frontend-agent | **Group:** G3 | **Depends:** S001 (API contract locked)
**Parallel-safe with S003** — different files

**Files:**
```
CREATE: frontend/src/components/admin/ResetPasswordModal.tsx
MODIFY: frontend/src/components/admin/UsersTab.tsx         — add "Reset Password" button per non-OIDC row
MODIFY: frontend/src/index.css                             — append CSS classes (see below)
MODIFY: frontend/src/i18n/<lang>.json (×4)                — add auth.reset_password.* keys (ja/en/vi/ko)
```

**CSS classes to add to index.css:**
```
.reset-password-modal
.reset-password-options
.reset-password-generated
.reset-password-copy-btn
.reset-password-warning
.reset-password-actions
```

**Key implementation notes:**
- "Reset Password" button shown only for rows where `user.has_password === true`
- Modal: radio/toggle — "Set password manually" vs "Auto-generate"
- Auto-generate: `POST /v1/admin/users/{id}/password-reset` with `{"generate": true}` → show plaintext in copyable field with one-time warning
- Manual: validate ≥ 8 chars → `POST /v1/admin/users/{id}/password-reset` with `{"new_password": "..."}`
- Reuse ApiKeyPanel copy-to-clipboard pattern for generated password display
- Success toast; modal closes; no page reload

> ⚠️ index.css conflict risk with S003: both append CSS. If dispatched in parallel, merge carefully — no overlapping class names (confirmed: all prefixed `.change-password-*` vs `.reset-password-*`).

**Est. tokens:** ~3k
**Test:** `npm test -- --testPathPattern=ResetPasswordModal`
**Subagent dispatch:** YES — new file + CSS append; parallel with S003

---

### S005: Frontend — Force-Change Password Gate
**Agent:** frontend-agent | **Group:** G4 | **Depends:** S003 (authStore gate pattern + ChangePasswordPage reuses form)
**Sequential** — must follow G3 (depends on ChangePasswordModal pattern; touches App.tsx and ProtectedRoute which S003 also modifies)

**Files:**
```
CREATE: frontend/src/pages/ChangePasswordPage.tsx
MODIFY: frontend/src/App.tsx                               — add /change-password route + force-gate guard logic
MODIFY: frontend/src/components/auth/ProtectedRoute.tsx    — add must_change_password redirect (lines 11–17)
MODIFY: frontend/src/store/authStore.ts                    — read/store must_change_password from login response
MODIFY: frontend/src/index.css                             — append CSS classes (see below)
MODIFY: frontend/src/i18n/<lang>.json (×4)                — add auth.force_change.* keys (ja/en/vi/ko)
```

**CSS classes to add to index.css:**
```
.force-change-page
.force-change-card
.force-change-title
.force-change-notice
.force-change-form
.force-change-submit
```

**Key implementation notes:**
- `authStore`: add `mustChangePassword: boolean` field; set from login response `must_change_password`
- `ProtectedRoute`: if `mustChangePassword === true` and route !== `/change-password` → redirect to `/change-password`
- `ChangePasswordPage`: full-page layout; NO "Current Password" field shown
- Silent pass: use `authStore.password` as `current_password` in PATCH body (user only inputs New + Confirm)
- No Cancel/Skip — force is mandatory; no dismiss path
- On success: set `mustChangePassword = false` in store → redirect to `/`
- OIDC users: `must_change_password` always `false` from backend → gate never activates

**Est. tokens:** ~3k
**Test:** `npm test -- --testPathPattern=ChangePasswordPage|ProtectedRoute`
**Subagent dispatch:** YES — after G3 complete

---

## Execution Order

```
G1: S001 (api-agent)
     ↓ migration applied, login response extended, users.py created
G2: S002 (api-agent)
     ↓ admin reset route + has_password in user list
G3: S003 (frontend-agent) ║ S004 (frontend-agent)   ← parallel
     ↓ both merged (watch index.css conflict)
G4: S005 (frontend-agent)
     ↓ gate wired, authStore updated, force-change page complete
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| index.css merge conflict (S003 + S004 parallel) | Medium | Low | No overlapping class names; prefix isolated; review before merge |
| authStore.password used silently in S005 | Low | Medium | Documented as DEFERRED-SEC-001; scope-limited to existing design (D002) |
| JWT still valid 60 min after admin reset | Low | Medium | Documented as DEFERRED-SEC-002; accepted risk with 60-min TTL |
| App.tsx modified by both S003 (dropdown) and S005 (route guard) | Medium | Low | S005 runs after S003 (G4 after G3); no parallel conflict |

---

## Deferred Items (do not implement)
- `DEFERRED-SEC-001`: refresh-token endpoint to remove raw password from authStore
- `DEFERRED-SEC-002`: token_version column for JWT session invalidation on password reset
- Password history / reuse prevention
- Password expiry / rotation policy
- Forgot-password / email-based reset
- Password strength indicator

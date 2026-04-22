---
name: change-password WARM memory
description: Feature memory for change-password — self-service change, admin force-reset, first-login force-change gate
type: project
---

# WARM: change-password
Created: 2026-04-22 | Status: SPEC DRAFT

---

## Feature Summary
5 stories: 2 backend (self-service PATCH + admin reset POST), 2 frontend modals, 1 frontend force-change gate page.
Key addition: `must_change_password` flag — set on create/admin-reset, cleared on first successful self-service change.

## Files
- Spec: `docs/change-password/spec/change-password.spec.md`
- Sources: `docs/change-password/sources/change-password.sources.md`

## Stories
| ID | Title | Status |
|----|-------|--------|
| S001 | Backend PATCH /v1/users/me/password (self-service + clears flag) | SPEC |
| S002 | Backend POST /v1/admin/users/{id}/password-reset (sets flag) | SPEC |
| S003 | Frontend ChangePasswordModal (self-service, profile menu) | SPEC |
| S004 | Frontend Admin ResetPasswordModal in UsersTab | SPEC |
| S005 | Frontend Force-Change Gate (/change-password page, first login) | SPEC |

## Key Decisions
- D1: API-key callers cannot use PATCH /v1/users/me/password — 403 (bots have no "self" identity)
- D2: Admin generate → 200 + `{"password": "..."}` (one-time); explicit new_password → 204
- D3: OIDC users (password_hash IS NULL) receive 400 ERR_PASSWORD_NOT_APPLICABLE on both paths
- D4: `must_change_password` flag: set `true` by admin create (user-management) + admin reset; cleared by self-service PATCH
- D5: Force-change gate omits "Current Password" field (admin set it; user doesn't know it)
- D6: All CSS in `frontend/src/index.css` — global classes, no inline styles, no CSS modules, no Tailwind

## CSS Classes Required
- S003: `.change-password-modal`, `.change-password-form`, `.change-password-field`, `.change-password-error`, `.change-password-actions`
- S004: `.reset-password-modal`, `.reset-password-options`, `.reset-password-generated`, `.reset-password-copy-btn`, `.reset-password-warning`, `.reset-password-actions`
- S005: `.force-change-page`, `.force-change-card`, `.force-change-title`, `.force-change-notice`, `.force-change-form`, `.force-change-submit`

## Assumptions (confirm at /clarify)
- A1: `GET /v1/admin/users` (user list) needs `has_password: bool` field — not currently confirmed
- A2: Profile/user pill exists in header (from frontend-spa) — confirm component location
- A3: Login response or `/v1/users/me` needs `must_change_password: bool` — confirm which
- A4: Force-change gate omits current-password field — confirm or clarify UX preference
- A5: No session invalidation on password change (deferred to security hardening)

## Schema Change Required
- `users` table: add `must_change_password BOOLEAN DEFAULT TRUE` column
- Migration: `backend/db/migrations/NNN_add_must_change_password.sql`
- user-management `POST /v1/admin/users` needs update to set `must_change_password=true` on create

## Files to Touch (est.)
- `backend/db/migrations/NNN_add_must_change_password.sql` (new migration)
- `backend/api/routes/users.py` (new — self-service route)
- `backend/api/routes/admin/users.py` (append — admin reset + update user create to set flag)
- `backend/auth/utils.py` (generate_password helper — may already exist)
- `frontend/src/index.css` (append CSS classes for all 3 UI components)
- `frontend/src/pages/ChangePasswordPage.tsx` (new — force-change gate)
- `frontend/src/components/auth/ChangePasswordModal.tsx` (new)
- `frontend/src/components/admin/ResetPasswordModal.tsx` (new)
- `frontend/src/App.tsx` (add /change-password route + gate guard)
- `frontend/src/components/admin/UsersTab.tsx` (add reset button)

## Blocked By
- user-management DONE ✅ (users table, password_hash, require_admin, UsersTab)

## Clarify Status (2026-04-22) ✅ UNBLOCKED
File: `docs/change-password/clarify/change-password.clarify.md`
- 4 BLOCKERS resolved by lb_mui 2026-04-22
- 5 SHOULD assumptions confirmed
- 10 auto-answered from code

## Resolved Decisions
- Q1 ✅: `must_change_password` added to login response (`POST /v1/auth/token`) — no extra round-trip
- Q2 ✅: Force-change gate uses `authStore.password` silently — user only inputs New + Confirm
- Q3 ✅: Admin reset always sets `must_change_password = true` — no admin override
- Q4 ✅: Session invalidation deferred — 60-min JWT TTL accepted as risk window

## Deferred Security Items
- `DEFERRED-SEC-001`: Remove raw password from `authStore` → implement refresh-token endpoint `POST /v1/auth/refresh`
- `DEFERRED-SEC-002`: JWT session invalidation on password reset → implement `token_version INT` in `users` table

## Key Code Facts (from scan)
- `GET /v1/users/me` does NOT exist — create in S001 (`backend/api/routes/users.py`)
- `generate_password()` does NOT exist — extract from `admin.py:375` to `backend/auth/utils.py`
- Login response extended: add `must_change_password: bool` to `auth.py` SELECT + return
- `GET /v1/admin/users` needs `has_password: (password_hash IS NOT NULL)` added to SELECT
- User pill in `App.tsx:39–44` is static — needs dropdown for S003
- `authStore.ts:11` stores raw password — S005 uses silently; documented as tech debt
- Next migration: `012_add_must_change_password.sql`
- Password validation: min 8 chars, max 128 chars (new — bcrypt DoS guard)

## Sync: 2026-04-22
Decisions added: D-CP-01, D-CP-02, D-CP-03, D-CP-04
Tasks changed: SPEC→DRAFT, CLARIFY→DONE
Files touched:
  - docs/change-password/spec/change-password.spec.md (created + updated)
  - docs/change-password/sources/change-password.sources.md (created)
  - docs/change-password/clarify/change-password.clarify.md (created + resolved)
  - .claude/memory/WARM/change-password.mem.md (created + updated)
  - .claude/memory/HOT.md (updated)
Questions resolved: Q1, Q2, Q3, Q4 (all blockers)
New blockers: none

## Plan
File: `docs/change-password/plan/change-password.plan.md`
Critical path: S001 → S002 → S003+S004 (parallel) → S005
Groups: G1(S001) → G2(S002) → G3(S003‖S004) → G4(S005)
Sessions est.: 2 | Token budget: ~14k

## Task Status Board (generated 2026-04-22)

### S001 — Backend PATCH /v1/users/me/password ✅ DONE
| Task | Title | Status |
|------|-------|--------|
| T001 | DB migration: add must_change_password column | DONE |
| T002 | Update User ORM model + UserResponse schema | DONE |
| T003 | Extract generate_password() to auth/utils.py | DONE |
| T004 | Create backend/api/routes/users.py with PATCH endpoint | DONE |
| T005 | Extend login response with must_change_password field | DONE |
| T006 | Register users router in main app | DONE |

### S002 — Backend POST /v1/admin/users/{id}/password-reset
| Task | Title | Status |
|------|-------|--------|
| T001 | Add POST /v1/admin/users/{id}/password-reset route | TODO |
| T002 | Add has_password to GET /v1/admin/users list | TODO |
| T003 | Tests: admin reset + has_password + audit log | TODO |

### S003 — Frontend ChangePasswordModal ✅ DONE
| Task | Title | Status |
|------|-------|--------|
| T001 | Add CSS classes for ChangePasswordModal to index.css | DONE |
| T002 | Add i18n keys (change-password) to 4 lang files | DONE |
| T003 | Create ChangePasswordModal.tsx component | DONE |
| T004 | Wire user-pill dropdown in App.tsx + OIDC hide | DONE |

### S004 — Frontend Admin ResetPasswordModal ✅ DONE
| Task | Title | Status |
|------|-------|--------|
| T001 | Add CSS classes for ResetPasswordModal to index.css | DONE |
| T002 | Add i18n keys (reset-password) to 4 lang files | DONE |
| T003 | Create ResetPasswordModal.tsx component | DONE |
| T004 | Add Reset Password button to UsersTab.tsx rows | DONE |

### S005 — Frontend Force-Change Gate ✅ DONE
| Task | Title | Status |
|------|-------|--------|
| T001 | Add CSS classes for force-change page to index.css | DONE |
| T002 | Add i18n keys (force-change) to 4 lang files | DONE |
| T003 | Extend authStore to store mustChangePassword from login | DONE |
| T004 | Create ChangePasswordPage.tsx (force-change form) | DONE |
| T005 | Add /change-password route + ProtectedRoute gate | DONE |

## Next Step
/report change-password

## Key Convention: Migration Execution
- D-CP-06: After writing any migration SQL file, agent must apply it to DB immediately via `psql`
- If `$DATABASE_URL` not set → agent prompts user: host, port, db name, user, password (or full string)
- Applies to: S001/T001 and any future migration tasks

## Sync: 2026-04-22
Decisions added: D-CP-05 (checklist PASS — files at .claude/, not root)
Tasks changed: CHECKLIST→PASS, PLAN→DONE
Files touched:
  - docs/change-password/reviews/checklist.md (created — 29/29 PASS)
  - docs/change-password/plan/change-password.plan.md (created)
  - .claude/memory/WARM/change-password.mem.md (plan path added)
  - .claude/memory/HOT.md (updated)
Questions resolved: none new
New blockers: none

## Sync: 2026-04-22 (tasks complete)
Tasks changed: PLAN→TASKS
Files touched:
  - docs/change-password/tasks/S001.tasks.md (created — 6 tasks)
  - docs/change-password/tasks/S002.tasks.md (created — 3 tasks)
  - docs/change-password/tasks/S003.tasks.md (created — 4 tasks)
  - docs/change-password/tasks/S004.tasks.md (created — 4 tasks)
  - docs/change-password/tasks/S005.tasks.md (created — 5 tasks)
  - .claude/memory/WARM/change-password.mem.md (task board added)
Questions resolved: none new
New blockers: none

## Sync: 2026-04-22 (S001/T001 patched + /sync)
Decisions added: D-CP-06 (migration must be applied to DB immediately; ask user for connection info)
Tasks changed: none (all still TODO)
Files touched:
  - docs/change-password/tasks/S001.tasks.md (T001 patched — added post-implementation DB apply step)
  - .claude/memory/WARM/change-password.mem.md (D-CP-06 convention added)
  - .claude/memory/HOT.md (session #109, D-CP-06 added)
Questions resolved: none new
New blockers: none

## Sync: 2026-04-22 (S001 DONE — /implement complete + migration applied)
Decisions added: D-CP-07 (apply migrations via `docker exec knowledge-hub-postgres psql -c "..."` — file copy fails on Windows path)
Tasks changed: S001 T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE, T006→DONE
Files created:
  - backend/db/migrations/012_add_must_change_password.sql
  - backend/auth/utils.py (generate_password helper)
  - backend/api/routes/users.py (PATCH /v1/users/me/password)
  - tests/auth/test_utils.py (4 tests)
  - tests/api/test_users.py (7 tests — 204/401/400/403/422×2 + route smoke)
Files modified:
  - backend/db/models/user.py (must_change_password ORM field)
  - backend/api/routes/auth.py (SELECT + return must_change_password; mock fixed)
  - backend/api/app.py (users.router registered)
  - backend/api/routes/__init__.py (users export)
  - tests/api/test_auth.py (_mock_db_row updated for row[2])
  - docs/change-password/tasks/S001.tasks.md (all tasks → DONE)
Test results: 11/11 new PASS | 12/12 auth PASS | DB column confirmed live
Questions resolved: none new
New blockers: none
Next: /implement S002

## Sync: 2026-04-22 (S003 + S004 DONE — /implement complete)
Decisions added: none new
Tasks changed: S003 T001→DONE, T002→DONE, T003→DONE, T004→DONE | S004 T001→DONE, T002→DONE, T003→DONE, T004→DONE
Files created:
  - frontend/src/components/auth/ChangePasswordModal.tsx (S003)
  - frontend/src/components/admin/ResetPasswordModal.tsx (S004)
  - frontend/src/components/admin/UsersTab.tsx (S004 — new; admin-spa UsersTab is separate)
  - frontend/tests/components/auth/ChangePasswordModal.test.tsx (S003 — 4 tests)
  - frontend/tests/components/admin/ResetPasswordModal.test.tsx (S004 — 7 tests)
  - frontend/tests/components/admin/UsersTab.test.tsx (S004 — 5 tests)
Files modified:
  - frontend/src/index.css (appended .change-password-* + .reset-password-* + .user-pill-dropdown classes)
  - frontend/src/i18n/locales/en.json (auth.change_password.* + auth.reset_password.* keys)
  - frontend/src/i18n/locales/ja.json (same)
  - frontend/src/i18n/locales/vi.json (same)
  - frontend/src/i18n/locales/ko.json (same)
  - frontend/src/App.tsx (user-pill → dropdown; ChangePasswordModal wired; OIDC hide via password===null)
  - docs/change-password/tasks/S003.tasks.md (all tasks → DONE)
  - docs/change-password/tasks/S004.tasks.md (all tasks → DONE)
Test results: 229/229 main SPA PASS (+12 new S004 tests) | admin-spa failures pre-existing (React version mismatch — unrelated)
Key note: frontend/src/components/admin/UsersTab.tsx is a new minimal component; admin-spa/src/components/UsersTab.tsx is the full feature-complete admin SPA component (separate codebase)
Questions resolved: none new
New blockers: none
Next: /report change-password

## Sync: 2026-04-22 (S005 DONE — /implement complete)
Decisions added: none new
Tasks changed: S005 T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE
Files created:
  - frontend/src/pages/ChangePasswordPage.tsx (S005 — force-change gate)
  - frontend/tests/pages/ChangePasswordPage.test.tsx (S005 — 6 tests)
Files modified:
  - frontend/src/index.css (appended .force-change-* classes)
  - frontend/src/i18n/locales/en.json (auth.force_change.* keys)
  - frontend/src/i18n/locales/ja.json (same)
  - frontend/src/i18n/locales/vi.json (same)
  - frontend/src/i18n/locales/ko.json (same)
  - frontend/src/store/authStore.ts (mustChangePassword field + clearMustChangePassword + login updated)
  - frontend/src/components/auth/LoginForm.tsx (must_change_password read from token response, passed to login())
  - frontend/src/components/auth/ProtectedRoute.tsx (mustChangePassword gate → /change-password redirect)
  - frontend/tests/components/auth/ProtectedRoute.test.tsx (3 new gate tests added, beforeEach updated)
  - frontend/src/App.tsx (ChangePasswordPage import + /change-password route)
  - docs/change-password/tasks/S005.tasks.md (all tasks → DONE)
Test results: 318/318 main SPA PASS (+16 new S005 tests) | admin-spa failures pre-existing
Questions resolved: none new
New blockers: none
Next: /report change-password

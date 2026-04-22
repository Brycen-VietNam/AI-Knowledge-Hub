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

### S001 — Backend PATCH /v1/users/me/password
| Task | Title | Status |
|------|-------|--------|
| T001 | DB migration: add must_change_password column | TODO |
| T002 | Update User ORM model + UserResponse schema | TODO |
| T003 | Extract generate_password() to auth/utils.py | TODO |
| T004 | Create backend/api/routes/users.py with PATCH endpoint | TODO |
| T005 | Extend login response with must_change_password field | TODO |
| T006 | Register users router in main app | TODO |

### S002 — Backend POST /v1/admin/users/{id}/password-reset
| Task | Title | Status |
|------|-------|--------|
| T001 | Add POST /v1/admin/users/{id}/password-reset route | TODO |
| T002 | Add has_password to GET /v1/admin/users list | TODO |
| T003 | Tests: admin reset + has_password + audit log | TODO |

### S003 — Frontend ChangePasswordModal
| Task | Title | Status |
|------|-------|--------|
| T001 | Add CSS classes for ChangePasswordModal to index.css | TODO |
| T002 | Add i18n keys (change-password) to 4 lang files | TODO |
| T003 | Create ChangePasswordModal.tsx component | TODO |
| T004 | Wire user-pill dropdown in App.tsx + OIDC hide | TODO |

### S004 — Frontend Admin ResetPasswordModal
| Task | Title | Status |
|------|-------|--------|
| T001 | Add CSS classes for ResetPasswordModal to index.css | TODO |
| T002 | Add i18n keys (reset-password) to 4 lang files | TODO |
| T003 | Create ResetPasswordModal.tsx component | TODO |
| T004 | Add Reset Password button to UsersTab.tsx rows | TODO |

### S005 — Frontend Force-Change Gate
| Task | Title | Status |
|------|-------|--------|
| T001 | Add CSS classes for force-change page to index.css | TODO |
| T002 | Add i18n keys (force-change) to 4 lang files | TODO |
| T003 | Extend authStore to store mustChangePassword from login | TODO |
| T004 | Create ChangePasswordPage.tsx (force-change form) | TODO |
| T005 | Add /change-password route + ProtectedRoute gate | TODO |

## Next Step
/analyze S001 T001

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

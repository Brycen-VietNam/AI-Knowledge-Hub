---
name: change-password archive
description: Completed feature — self-service change, admin force-reset, first-login force-change gate. Archived 2026-04-22.
type: project
---

# COLD Archive: change-password
Archived: 2026-04-22 | Status: DONE ✅

---

## Feature Summary
5 stories: S001 backend self-service PATCH, S002 backend admin reset POST, S003 frontend ChangePasswordModal, S004 frontend Admin ResetPasswordModal, S005 frontend Force-Change Gate page.
Key addition: `must_change_password` boolean flag — set on admin create/reset, cleared on first successful self-service change.

## Results
- AC Coverage: 43/43 (100%)
- Test Pass Rate: 340/340 (318 frontend + 22 backend) — 100%
- Critical Blockers: 0
- Duration: 1 session (2026-04-22)

## Key Decisions
- D1: API-key callers → 403 on PATCH /v1/users/me/password (bots have no "self" identity)
- D2: Admin generate → 200 + `{"password": "..."}` one-time; explicit new_password → 204
- D3: OIDC users (NULL password_hash) → 400 ERR_PASSWORD_NOT_APPLICABLE on both paths
- D4: `must_change_password` flag set by admin create + reset; cleared by self-service PATCH
- D5: Force-change gate omits "Current Password" field; uses `authStore.password` silently
- D6: All CSS in `frontend/src/index.css` — global classes only, no modules, no Tailwind
- D-CP-06: Apply migrations to DB immediately after writing SQL file
- D-CP-07: Windows — use `docker exec knowledge-hub-postgres psql -c "..."` (not psql -f with file copy)

## Deferred Security Items
- DEFERRED-SEC-001: Remove raw password from `authStore` → implement POST /v1/auth/refresh
- DEFERRED-SEC-002: JWT session invalidation on password reset → token_version column in users table

## Files Touched (major)
- `backend/db/migrations/012_add_must_change_password.sql`
- `backend/db/models/user.py`
- `backend/auth/utils.py`
- `backend/api/routes/users.py` (new)
- `backend/api/routes/admin.py` (appended)
- `backend/api/routes/auth.py` (extended login response)
- `frontend/src/index.css` (17 new CSS classes)
- `frontend/src/i18n/locales/{en,ja,vi,ko}.json`
- `frontend/src/components/auth/ChangePasswordModal.tsx` (new)
- `frontend/src/components/auth/ProtectedRoute.tsx`
- `frontend/src/components/auth/LoginForm.tsx`
- `frontend/src/store/authStore.ts`
- `frontend/src/pages/ChangePasswordPage.tsx` (new)
- `frontend/src/App.tsx`
- `frontend/admin-spa/src/components/ResetPasswordModal.tsx` (new)
- `frontend/admin-spa/src/components/UsersTab.tsx`
- `frontend/admin-spa/src/api/adminApi.ts`

## Report
`docs/change-password/reports/change-password.report.md`

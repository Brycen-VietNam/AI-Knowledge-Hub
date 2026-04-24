# WARM: ux-form-validation
Created: 2026-04-24 | Status: REVIEWED | Phase: ready for /report

---

## Spec Summary
**Problem:** Form validation UX gaps in both SPAs — backend 422s surface as generic errors, no password toggles, no real-time confirm match.
**Scope:** Frontend-only (Admin SPA + Frontend SPA). No backend changes.
**CSS rule:** Decision D6 — only `index.css`, no inline styles, modules, or Tailwind.

## Stories (5)
| Story | Title | AC count | Priority |
|-------|-------|----------|----------|
| S001 | CSS Foundation (field-error, field-hint, password-field-row, btn-eye) | 7 | P1 (blocker for others) |
| S002 | UserFormModal — 422 parsing + hints (Admin SPA) | 10 | P1 (real bug) |
| S003 | LoginForm — password toggle (Frontend SPA) | 6 | P3 |
| S004 | ChangePasswordModal + Page — real-time confirm match (Frontend SPA) | 7 | P2 |
| S005 | ResetPasswordModal + AssignGroupModal (Admin SPA) | 7 | P4/P5 |

**Total ACs:** 30 | **Sources:** 30/30 traced

## Key Files
- Admin SPA: `frontend/admin-spa/src/components/UserFormModal.tsx`, `ResetPasswordModal.tsx`, `AssignGroupModal.tsx`
- Frontend SPA: `frontend/src/components/auth/LoginForm.tsx`, `frontend/src/components/auth/ChangePasswordModal.tsx`, `frontend/src/pages/ChangePasswordPage.tsx`
- CSS: `frontend/src/index.css`, `frontend/admin-spa/src/index.css`

## Decisions
- D6 (2026-04-17): Only `index.css` — no inline styles, no CSS modules, no Tailwind
- Backlog notes (2026-04-22): No backend changes; all error messages via i18n keys; manual docker test per BK

## Resolved Findings (2026-04-24)
- A1 RESOLVED: `admin-spa/src/index.css` line 922 has `.password-field-row` — only add `.btn-eye` to admin-spa; port all 4 classes to frontend-spa
- A2 RESOLVED: i18n uses nested JSON (en/vi/ja/ko) in `i18n/locales/`. Add new hint keys under existing `auth.*` namespace. Must add to all 4 locales in each SPA.
- A3 RESOLVED: `ResetPasswordModal.tsx` line 71 already has `setTimeout(() => setCopied(false), 2000)` — S005 AC3 is already done, verify visual only.

## Open Questions
(none — all resolved)

## Tasks: S001
| Task | Title | Status |
|------|-------|--------|
| T001 | Append 4 utility classes to `frontend/src/index.css` | DONE |
| T002 | Append `.btn-eye` to `frontend/admin-spa/src/index.css` | DONE |
| T003 | Build smoke-check both SPAs | DONE |
File: `docs/ux-form-validation/tasks/S001.tasks.md`

## Status
- [x] Spec: `docs/ux-form-validation/spec/ux-form-validation.spec.md`
- [x] Sources: `docs/ux-form-validation/sources/ux-form-validation.sources.md`
- [x] Clarify: skipped — all 3 open questions resolved by reading source files directly
- [x] Plan: `docs/ux-form-validation/plan/ux-form-validation.plan.md`
- [x] Tasks S001: `docs/ux-form-validation/tasks/S001.tasks.md` — DONE (builds pass)
- [x] Tasks S002: `docs/ux-form-validation/tasks/S002.tasks.md` — DONE (build pass)
- [x] Tasks S003: `docs/ux-form-validation/tasks/S003.tasks.md` — DONE (build pass)
- [x] Tasks S004: `docs/ux-form-validation/tasks/S004.tasks.md` — DONE (build pass)
- [x] Tasks S005: `docs/ux-form-validation/tasks/S005.tasks.md` — DONE (build pass)
- [x] Implementation: ALL 5 stories DONE
- [x] Review: `docs/ux-form-validation/reviews/ux-form-validation.review.md` — APPROVED (1 warning)
- [ ] Report

## Critical Path (from plan)
S001 → [S002 ‖ S003] → [S004 ‖ S005]
Total files: 14 (2 CSS + 5 TSX + 4×2 locale JSON)

---

## Sync: 2026-04-24 (session end)
Decisions added: D-UX-04 (admin-spa had no auth.* namespace — added as new block)
Tasks changed: S001→DONE, S002→DONE, S003→DONE, S004→DONE, S005→DONE
Files touched:
  CSS: frontend/src/index.css (+4 classes), frontend/admin-spa/src/index.css (+1 class)
  TSX: UserFormModal.tsx, LoginForm.tsx, ChangePasswordModal.tsx, ChangePasswordPage.tsx, ResetPasswordModal.tsx, AssignGroupModal.tsx
  Locales (frontend-spa): en/vi/ja/ko — login.show/hide_password, auth.change_password.hint_password
  Locales (admin-spa): en/vi/ja/ko — user.form.hint_sub/email/password, auth.reset_password.hint_password, assign_groups_hint_min
Questions resolved: all
New blockers: none

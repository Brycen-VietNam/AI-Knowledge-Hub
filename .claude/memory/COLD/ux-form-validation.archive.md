# COLD Archive: ux-form-validation
Archived: 2026-04-24 | Status: DONE ✅

---

## Spec Summary
**Problem:** Form validation UX gaps in both SPAs — backend 422s surface as generic errors, no password toggles, no real-time confirm match.
**Scope:** Frontend-only (Admin SPA + Frontend SPA). No backend changes.
**CSS rule:** Decision D6 — only `index.css`, no inline styles, modules, or Tailwind.

## Stories (5)
| Story | Title | AC count | Result |
|-------|-------|----------|--------|
| S001 | CSS Foundation | 7 | 7/7 PASS |
| S002 | UserFormModal — 422 parsing + hints (Admin SPA) | 10 | 8/10 PASS + 2 PARTIAL |
| S003 | LoginForm — password toggle (Frontend SPA) | 6 | 6/6 PASS |
| S004 | ChangePasswordModal + Page — real-time confirm match | 7 | 7/7 PASS |
| S005 | ResetPasswordModal + AssignGroupModal (Admin SPA) | 7 | 7/7 PASS |

**Total ACs:** 28/30 FULL PASS | 2 PARTIAL (deferred) | 0 FAIL

## Key Files Changed
- Admin SPA: `UserFormModal.tsx`, `ResetPasswordModal.tsx`, `AssignGroupModal.tsx`, `admin-spa/src/index.css`
- Frontend SPA: `LoginForm.tsx`, `ChangePasswordModal.tsx`, `ChangePasswordPage.tsx`, `frontend/src/index.css`
- Locales: 8 JSON files (en/vi/ja/ko × 2 SPAs)

## Decisions
- D6: Only `index.css` — no inline styles, no CSS modules, no Tailwind
- D-UX-01: `.password-field-row` already in admin-spa line 922; only add `.btn-eye`
- D-UX-02: All 4 CSS classes ported to frontend-spa
- D-UX-03: S005 AC3 copy timeout already at line 71 — verify only
- D-UX-04: `auth.*` namespace added as new top-level block in admin-spa locales

## Open / Deferred
- W-001: `fieldErrors` not cleared on onChange in UserFormModal — 1-line fix deferred

## Report
`docs/ux-form-validation/reports/ux-form-validation.report.md`

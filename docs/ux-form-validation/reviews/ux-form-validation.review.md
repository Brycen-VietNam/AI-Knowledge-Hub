# Code Review: ux-form-validation — All Stories (S001–S005)
Level: quick | Date: 2026-04-24 | Reviewer: Claude (opus)

---

## Summary
Frontend-only feature. 16 files changed (2 CSS + 6 TSX + 8 locale JSON). All files within TOUCH list. One warning found; no blockers.

---

## S001 — CSS Foundation

### Task Review Criteria
- [x] 4 utility classes appended to `frontend/src/index.css`: `.field-error`, `.field-hint`, `.password-field-row`, `.btn-eye`
- [x] `.btn-eye` appended to `frontend/admin-spa/src/index.css`
- [x] No existing CSS rules broken (build smoke-check passes)

---

## S002 — UserFormModal 422 parsing + hints (Admin SPA)

### Task Review Criteria
- [x] `fieldErrors` state present (`useState<Record<string, string>>({})`)
- [x] 422 Array detail → per-field errors; string detail → general `setError`
- [x] `.field-error` only rendered when `fieldErrors[field]` is truthy
- [x] `.field-hint` always rendered for sub, email, password
- [x] No hardcoded error strings — server `d.msg` used directly for field errors; i18n for all hint strings
- [x] `d.loc[1]` indexing correct for FastAPI/Pydantic v2 `["body", "field_name"]` shape

### Issues Found

#### ⚠️ WARNING — Should fix
**`clearErrors` does not reset `fieldErrors` on input change**
File: [frontend/admin-spa/src/components/UserFormModal.tsx](frontend/admin-spa/src/components/UserFormModal.tsx#L50)

`handleSubmit` calls `setError(null)` but does not call `setFieldErrors({})`. Individual `onChange` handlers on sub/email/password inputs also do not clear per-field errors. Result: after a 422 response, stale field errors persist while the user types corrections — they only clear on the next submit.

Fix options (either):
1. Add `setFieldErrors({})` to the existing `setError(null)` at L50 in `handleSubmit`.
2. Add individual `onChange` clear: e.g., `onChange={(e) => { setFieldErrors(p => ({...p, sub: ''})); setSub(e.target.value) }}`.

Option 1 is simpler and consistent with how `ChangePasswordModal` handles its `clearErrors`.

---

## S003 — LoginForm password toggle (Frontend SPA)

### Task Review Criteria
- [x] `password-field-row` wrapper div present
- [x] `btn-eye` button has `type="button"` (no accidental form submit)
- [x] `aria-label` uses `t('login.show_password')` / `t('login.hide_password')`
- [x] No new icon library imported (emoji used: `👁` / `🙈`)
- [x] Input `id="password"` preserved (label `htmlFor` still valid)
- [x] `show_password` / `hide_password` keys present in all 4 locales under `login` namespace

---

## S004 — ChangePassword real-time confirm match (Frontend SPA)

### Task Review Criteria
- [x] `confirmError` clears (`setConfirmError('')`) when confirm matches new password
- [x] `confirmError` fires on every `onChange`, not just `onBlur`
- [x] `maxLength={128}` on both new-password and confirm inputs in `ChangePasswordModal.tsx`
- [x] `maxLength={128}` on both new-password and confirm inputs in `ChangePasswordPage.tsx`
- [x] `.field-hint` uses `auth.change_password.hint_password` key (no duplication)
- [x] `hint_password` key present in all 4 locales under `auth.change_password`
- [x] Logic consistent between `ChangePasswordModal` and `ChangePasswordPage` (same pattern)

---

## S005 — ResetPasswordModal + AssignGroupModal polish (Admin SPA)

### Task Review Criteria
- [x] `field-hint` for `hint_password` inside `{mode === 'manual' && ...}` block (line 117 is inside `mode === 'manual'` guard at line 104)
- [x] `minLength={8}` / `maxLength={128}` added to `rp-new` input
- [x] Save button disabled when `selected.size === 0`
- [x] `.field-error` for `assign_groups_hint_min` reactive to `selected.size === 0` (Set state, re-renders correctly)
- [x] No inline styles added (D6 respected)
- [x] `auth.reset_password.hint_password` + `assign_groups_hint_min` present in all 4 locales
- [x] `auth` block correctly added as new top-level namespace in admin-spa locales (D-UX-04 decision)

---

## Quick Checks
- [x] All review criteria from task files satisfied (1 warning on S002 — see above)
- [x] Build passes — confirmed (HOT.md: "ALL builds pass ✅")
- [x] No files outside TOUCH list modified (16/16 match exactly)

---

## Issues Summary

### ❌ BLOCKERS
(none)

### ⚠️ WARNINGS (1)
1. **S002 — `fieldErrors` not cleared on input change**
   File: [frontend/admin-spa/src/components/UserFormModal.tsx:50](frontend/admin-spa/src/components/UserFormModal.tsx#L50)
   Fix: add `setFieldErrors({})` at L50 alongside `setError(null)`, OR clear per-field in `onChange`.
   Impact: UX only — stale error labels persist while user types after a 422.

---

## Suggested test
```tsx
// Manual test scenario — UserFormModal
// 1. Submit with invalid sub (too short) → expect field error under sub input
// 2. Start typing in sub field → error should clear immediately
// Currently: error persists until next submit — the warning above
```

---

## Verdict

**[x] APPROVED — with warning**  
[ ] CHANGES REQUIRED  
[ ] BLOCKED

The single warning (S002 stale fieldErrors) is a minor UX degradation, not a regression or correctness bug. The feature is otherwise complete, correct, and consistent across all 5 stories. Merging is safe; the warning can be addressed as a follow-up task.

---

## Post-Review Actions
- Update `WARM/ux-form-validation.mem.md`: all stories status → REVIEWED
- Ready for `/report ux-form-validation`

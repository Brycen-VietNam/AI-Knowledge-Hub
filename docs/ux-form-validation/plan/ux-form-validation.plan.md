# Plan: ux-form-validation
Created: 2026-04-24 | Spec: `docs/ux-form-validation/spec/ux-form-validation.spec.md` | Status: DRAFT

---

## LAYER 1 — Plan Summary

| Field | Value |
|-------|-------|
| Stories | 5 |
| Sessions est. | 1–2 (all frontend, no backend) |
| Critical path | S001 → S002 → S003 → S004 → S005 |
| Parallel groups | G1: S001 (blocker) → G2: S002 + S003 (parallel-safe) → G3: S004 + S005 (parallel-safe) |
| Agent | frontend-agent (single agent, both SPAs) |
| Token budget total | ~12k |
| Checklist | Skipped — P2 frontend-only, no ARCH/HARD rule intersection |

### Parallelization notes
- **G1 (S001) must complete first** — CSS classes must exist before any component uses them
- **G2: S002 + S003** — different SPAs, different files, no shared edits → parallel-safe
- **G3: S004 + S005** — different files/SPAs → parallel-safe
- Sequential rule: never parallelize two stories touching the same file
  - S002 touches `UserFormModal.tsx` only; S003 touches `LoginForm.tsx` only ✓
  - S004 touches `ChangePasswordModal.tsx` + `ChangePasswordPage.tsx`; S005 touches `ResetPasswordModal.tsx` + `AssignGroupModal.tsx` ✓

### i18n strategy (all stories)
- Files: `frontend/src/i18n/locales/{en,vi,ja,ko}.json` (frontend-spa)
- Files: `frontend/admin-spa/src/i18n/locales/{en,vi,ja,ko}.json` (admin-spa)
- Namespace pattern: nest under `auth.*` or `user.form.*` (existing pattern)
- **All new keys must be added to all 4 locales** in the relevant SPA

---

## LAYER 2 — Per-Story Plans

---

### S001: CSS Foundation
**Agent:** frontend-agent | **Group:** G1 (sequential — must finish before G2/G3) | **Depends:** none

**Files:**
- MODIFY: `frontend/src/index.css` — append 4 new classes
- MODIFY: `frontend/admin-spa/src/index.css` — append `.btn-eye` only (`.password-field-row` already at line 922)

**CSS to add to `frontend/src/index.css`:**
```css
.field-error        { font-size: 12px; color: var(--red); margin-top: 4px; }
.field-hint         { font-size: 11.5px; color: var(--text-3); margin-top: 4px; }
.password-field-row { display: flex; gap: 8px; align-items: center; }
.btn-eye            { background: none; border: none; cursor: pointer; color: var(--text-3); padding: 4px; }
```

**CSS to add to `frontend/admin-spa/src/index.css`:**
```css
.btn-eye { background: none; border: none; cursor: pointer; color: var(--text-3); padding: 4px; }
```

**Est. tokens:** ~1k
**Test:** `npm run build` in both `frontend/` and `frontend/admin-spa/` — no errors
**Subagent dispatch:** NO — trivial 2-file edit

---

### S002: UserFormModal — 422 parsing + hints (Admin SPA)
**Agent:** frontend-agent | **Group:** G2 (after S001) | **Depends:** S001

**Files:**
- MODIFY: `frontend/admin-spa/src/components/UserFormModal.tsx`
- MODIFY: `frontend/admin-spa/src/i18n/locales/en.json` — add hint keys
- MODIFY: `frontend/admin-spa/src/i18n/locales/vi.json`
- MODIFY: `frontend/admin-spa/src/i18n/locales/ja.json`
- MODIFY: `frontend/admin-spa/src/i18n/locales/ko.json`

**Key logic in `UserFormModal.tsx`:**
```ts
// State
const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

// On 422 response
if (res.status === 422 && res.data?.detail) {
  const errs: Record<string, string> = {}
  res.data.detail.forEach((d: { loc: string[]; msg: string }) => {
    if (d.loc[1]) errs[d.loc[1]] = d.msg
  })
  setFieldErrors(errs)
} else {
  setGeneralError(t('common.error.unexpected'))
}

// Per-field: onBlur validation + render
<input onBlur={() => validateField('email', value)} />
{fieldErrors.email && <p className="field-error">{fieldErrors.email}</p>}
<p className="field-hint">{t('user.form.hint_email')}</p>
```

**New i18n keys (admin-spa, all 4 locales):**
```json
"user": {
  "form": {
    "hint_sub": "3–200 chars: a-z A-Z 0-9 _ . @ -",
    "hint_email": "Must be a valid domain (e.g. user@company.com)",
    "hint_password": "Minimum 12 characters"
  }
}
```

**Est. tokens:** ~3k
**Test:** Manual — create user with `test1@test.local` → error appears under email field
**Subagent dispatch:** NO — single component + i18n

---

### S003: LoginForm — password toggle (Frontend SPA)
**Agent:** frontend-agent | **Group:** G2 (after S001, parallel with S002) | **Depends:** S001

**Files:**
- MODIFY: `frontend/src/components/auth/LoginForm.tsx`
- MODIFY: `frontend/src/i18n/locales/en.json` — add `login.show_password` / `login.hide_password`
- MODIFY: `frontend/src/i18n/locales/vi.json`
- MODIFY: `frontend/src/i18n/locales/ja.json`
- MODIFY: `frontend/src/i18n/locales/ko.json`

**Key logic in `LoginForm.tsx`:**
```tsx
const [showPassword, setShowPassword] = useState(false)

<div className="password-field-row">
  <input
    type={showPassword ? 'text' : 'password'}
    ...
  />
  <button
    type="button"
    className="btn-eye"
    onClick={() => setShowPassword(p => !p)}
    aria-label={showPassword ? t('login.hide_password') : t('login.show_password')}
  >
    {showPassword ? '🙈' : '👁'}
  </button>
</div>
```

> **Note:** Use a simple text/SVG icon — no new icon library dependency. If project already has an icon set, use it; otherwise use a Unicode character or inline SVG (2–3 path).

**New i18n keys (frontend-spa, all 4 locales):**
```json
"login": {
  "show_password": "Show password",
  "hide_password": "Hide password"
}
```

**Est. tokens:** ~2k
**Test:** Manual — toggle shows/hides password text; keyboard Enter/Space activates button
**Subagent dispatch:** NO

---

### S004: ChangePasswordModal + ChangePasswordPage — real-time confirm match
**Agent:** frontend-agent | **Group:** G3 (after G2) | **Depends:** S001

**Files:**
- MODIFY: `frontend/src/components/auth/ChangePasswordModal.tsx`
- MODIFY: `frontend/src/pages/ChangePasswordPage.tsx`
- MODIFY: `frontend/src/i18n/locales/{en,vi,ja,ko}.json` — add hint key

**Key logic (same pattern for both files):**
```tsx
// Existing error key: auth.change_password.error.mismatch already exists in en.json
// Add: auth.change_password.hint_password = "8–128 characters"

const [confirmError, setConfirmError] = useState('')

// confirmPassword onChange handler
onChange={(e) => {
  setConfirmPassword(e.target.value)
  if (e.target.value && e.target.value !== newPassword) {
    setConfirmError(t('auth.change_password.error.mismatch'))
  } else {
    setConfirmError('')
  }
}}

// Render
<input type="password" maxLength={128} ... />
{confirmError && <p className="field-error">{confirmError}</p>}
<p className="field-hint">{t('auth.change_password.hint_password')}</p>
```

**New i18n keys (frontend-spa, all 4 locales):**
```json
"auth": {
  "change_password": {
    "hint_password": "8–128 characters"
  }
}
```

> **Note:** `auth.change_password.error.mismatch` already exists in en.json ("New passwords do not match.") — reuse it, do not add duplicate.

**Est. tokens:** ~2.5k
**Test:** Manual — type mismatched confirmPassword → error appears immediately; fix → error clears
**Subagent dispatch:** NO

---

### S005: ResetPasswordModal + AssignGroupModal — polish (Admin SPA)
**Agent:** frontend-agent | **Group:** G3 (after G2, parallel with S004) | **Depends:** S001

**Files:**
- MODIFY: `frontend/admin-spa/src/components/ResetPasswordModal.tsx`
- MODIFY: `frontend/admin-spa/src/components/AssignGroupModal.tsx`
- MODIFY: `frontend/admin-spa/src/i18n/locales/{en,vi,ja,ko}.json` — add hint keys

**ResetPasswordModal changes (manual mode input only):**
```tsx
<input
  id="rp-new"
  type="password"
  minLength={8}
  maxLength={128}
  ...
/>
<p className="field-hint">{t('auth.reset_password.hint_password')}</p>
// AC3 (copy timeout) already done at line 71 — no change needed
```

**AssignGroupModal changes:**
```tsx
// Derive from existing selectedGroupIds state
const hasNoGroups = selectedGroupIds.length === 0

<button type="submit" disabled={isLoading || hasNoGroups}>
  {t('btn_save')}
</button>
{hasNoGroups && <p className="field-error">{t('assign_groups_hint_min')}</p>}
```

**New i18n keys (admin-spa, all 4 locales):**
```json
// auth.reset_password.hint_password = "Minimum 8 characters"
// assign_groups_hint_min = "Select at least 1 group"
```

**Est. tokens:** ~2k
**Test:** Manual — reset modal shows hint; assign modal Save disabled with 0 groups selected; message clears on re-select
**Subagent dispatch:** NO

---

## Execution Order

```
[G1] S001 — CSS Foundation (both index.css)
      ↓
[G2] S002 (Admin SPA — UserFormModal)   ←→ S003 (Frontend SPA — LoginForm)   [parallel]
      ↓
[G3] S004 (Frontend SPA — ChangePassword*)  ←→ S005 (Admin SPA — Reset+Assign) [parallel]
```

**Recommended single-session order** (if not parallelizing):
S001 → S002 → S003 → S004 → S005

Total files touched: 14 (2 CSS + 5 TSX + 4×2 locale JSON)

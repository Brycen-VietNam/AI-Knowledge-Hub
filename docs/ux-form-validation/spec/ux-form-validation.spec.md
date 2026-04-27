# Spec: ux-form-validation
Created: 2026-04-24 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | frontend-ux |
| Priority | P2 |
| Story count | 5 |
| Token budget est. | ~5k |
| Critical path | S001 (CSS foundation) → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S002, S003 after S001 CSS merged |
| Blocking specs | none |
| Blocked by | none |
| Agents needed | frontend-agent only |

### Problem Statement
Form validation UX across both SPAs is incomplete: backend 422 errors surface as generic messages, password fields lack visibility toggles, and confirm-password mismatches are only caught on submit. Users cannot diagnose or self-correct input errors without trial and error.

### Solution Summary
- Add CSS foundation classes (`.field-error`, `.field-hint`, `.password-field-row`, `.btn-eye`) to both `index.css` files
- Parse Pydantic 422 `detail` array → display inline field-level errors in UserFormModal (Admin SPA)
- Add hint text under `sub`, `email`, `password` fields in UserFormModal; inline blur validation
- Add password show/hide toggle to LoginForm (Frontend SPA)
- Real-time confirm-password match check in ChangePasswordModal + ChangePasswordPage
- Disable Save in AssignGroupModal when no group selected; show inline empty-selection message
- Add `maxLength` + `minLength` constraints + hint text to ResetPasswordModal manual mode

### Out of Scope
- Backend validation logic changes (none)
- Password strength indicator (deferred per BK-003)
- i18n key system changes (use existing i18n keys; add new keys as needed)
- Any new API endpoints
- Automated E2E tests (manual docker build + up per BK per backlog notes)

---

## LAYER 2 — Story Detail

---

### S001: CSS Foundation — field-error, field-hint, password-field-row

**Role / Want / Value**
- As a: frontend-agent
- I want: shared CSS classes for inline errors, hints, and password row layout
- So that: all subsequent stories (S002–S005) have a consistent, Decision-D6-compliant styling base

**Acceptance Criteria**
- [ ] AC1: `.field-error` added to `frontend/src/index.css` — `font-size: 12px; color: var(--red); margin-top: 4px`
- [ ] AC2: `.field-hint` added to `frontend/src/index.css` — `font-size: 11.5px; color: var(--text-3); margin-top: 4px`
- [ ] AC3: `.password-field-row` added to `frontend/src/index.css` — `display: flex; gap: 8px; align-items: center`
- [ ] AC4: `.btn-eye` added to `frontend/src/index.css` — `background: none; border: none; cursor: pointer; color: var(--text-3); padding: 4px`
- [ ] AC5: `.password-field-row` and `.btn-eye` added to `frontend/src/index.css` only — admin-spa already has `.password-field-row` (line 922); only missing `.btn-eye`
- [ ] AC6: No inline styles, no CSS modules, no Tailwind introduced (Decision D6)
- [ ] AC7: Both SPAs build cleanly (`npm run build`) after CSS additions

**Auth Requirement**
- [x] Not applicable (CSS only)

**Non-functional**
- Latency: N/A
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
`admin-spa/src/index.css` already has `.password-field-row` at line 922 (with child `input` styling). Only add `.btn-eye` to admin-spa. Port all 4 classes to `frontend/src/index.css`.

---

### S002: UserFormModal — inline 422 parsing + field hints (Admin SPA)

**Role / Want / Value**
- As a: admin user creating a new user
- I want: field-level error messages from the backend and hint text on all fields
- So that: I understand exactly which field failed and what format is expected, without guessing

**Acceptance Criteria**
- [ ] AC1: On 422 response, parse `detail` array → map `detail[i].loc[1]` (field name) → render inline error under matching field using `.field-error` class
- [ ] AC2: If no field match found for a 422 detail item, display it in the existing form-level error zone (not "unexpected error")
- [ ] AC3: Hint text rendered under `sub` field: _"3–200 ký tự, chỉ dùng a-z A-Z 0-9 _ . @ -"_ (via i18n key `hint.sub`)
- [ ] AC4: Hint text rendered under `email` field: _"Email phải là domain hợp lệ (vd: user@company.com)"_ (via i18n key `hint.email`)
- [ ] AC5: Hint text rendered under `password` field: _"Tối thiểu 12 ký tự"_ (via i18n key `hint.password_admin`)
- [ ] AC6: All hint elements use `.field-hint` CSS class
- [ ] AC7: On field blur, run client-side validation and show inline error immediately (do not wait for submit)
- [ ] AC8: Inline errors clear when the field value becomes valid
- [ ] AC9: `test1@test.local` submitted → 422 parsed → error appears under email field (not "unexpected error")
- [ ] AC10: No backend changes required

**Auth Requirement**
- [x] OIDC Bearer (admin session)

**Non-functional**
- Latency: N/A (client-side only)
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
File: `frontend/admin-spa/src/components/UserFormModal.tsx`. Pydantic 422 shape: `{ detail: [{ loc: ["body", "fieldName"], msg: "...", type: "..." }] }`. Map `loc[1]` → field key. Store per-field errors in component state (e.g. `fieldErrors: Record<string, string>`).

---

### S003: LoginForm — password show/hide toggle (Frontend SPA)

**Role / Want / Value**
- As a: user logging in
- I want: a button to toggle password visibility
- So that: I can verify what I've typed without retyping

**Acceptance Criteria**
- [ ] AC1: Password input has a toggle button (eye icon) rendered inside or immediately after the input using `.password-field-row` and `.btn-eye` classes
- [ ] AC2: Toggle switches input `type` between `"password"` and `"text"`
- [ ] AC3: Button is keyboard-accessible (focusable, activatable via Enter/Space)
- [ ] AC4: Button has accessible label (`aria-label="Show password"` / `"Hide password"` toggled)
- [ ] AC5: No inline style on the button or row (Decision D6)
- [ ] AC6: Generic login error message is NOT changed (intentional per spec — security)

**Auth Requirement**
- [x] Not applicable (pre-auth UI)

**Non-functional**
- Latency: N/A
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
File: `frontend/src/components/auth/LoginForm.tsx`. Use local `useState<boolean>` for `showPassword`. Eye icon: use existing icon library or a simple SVG — no new dependency. Port `.password-field-row` + `.btn-eye` from admin-spa if not done by S001.

---

### S004: ChangePasswordModal + ChangePasswordPage — real-time confirm match (Frontend SPA)

**Role / Want / Value**
- As a: user changing their password
- I want: immediate feedback when confirm-password doesn't match
- So that: I know about the mismatch before clicking submit

**Acceptance Criteria**
- [ ] AC1: In `ChangePasswordModal.tsx` — `confirmPassword` onChange handler checks if value matches `newPassword`; if not, display inline error under confirmPassword field using `.field-error`
- [ ] AC2: In `ChangePasswordPage.tsx` — same real-time match check behavior
- [ ] AC3: Inline error clears when confirmPassword matches newPassword
- [ ] AC4: `maxLength={128}` attribute on all password inputs (currentPassword, newPassword, confirmPassword) in both files
- [ ] AC5: Hint text under newPassword in both files: _"8–128 ký tự"_ (via i18n key `hint.password_user`) using `.field-hint`
- [ ] AC6: Password strength indicator is **deferred** — not implemented in this story
- [ ] AC7: Submit button remains enabled regardless of mismatch (backend validates definitively); only the inline error is shown

> **Assumption**: `ChangePasswordModal` and `ChangePasswordPage` share the same field names (`currentPassword`, `newPassword`, `confirmPassword`). Confirm with `/clarify` if component structure differs significantly.

**Auth Requirement**
- [x] OIDC Bearer (authenticated user)

**Non-functional**
- Latency: N/A (client-side only)
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
Files: `frontend/src/components/auth/ChangePasswordModal.tsx`, `frontend/src/pages/ChangePasswordPage.tsx`. Real-time check triggered on `onChange` of `confirmPassword` (not `onBlur`). Add `minLength={8}` as well for HTML5 hint on native form validation — does not replace backend enforcement.

---

### S005: ResetPasswordModal (manual mode) + AssignGroupModal (Admin SPA)

**Role / Want / Value**
- As a: admin user
- I want: clear constraints on the reset-password manual input and a guardrail on group assignment
- So that: I don't submit forms that will definitely be rejected by the backend

**Acceptance Criteria**
- [ ] AC1: `ResetPasswordModal.tsx` manual mode — hint text under password input: _"Tối thiểu 8 ký tự"_ (via i18n key `hint.password_reset`) using `.field-hint`
- [ ] AC2: `ResetPasswordModal.tsx` manual mode — `maxLength={128}` and `minLength={8}` on the password input
- [x] AC3: `ResetPasswordModal.tsx` generate mode — copy button resets after 2 000 ms — **already implemented** (`setTimeout(() => setCopied(false), 2000)` at ResetPasswordModal.tsx:71); verify visual feedback only
- [ ] AC4: `AssignGroupModal.tsx` — Save button is disabled (`disabled` attribute) when `selectedGroupIds.length === 0`
- [ ] AC5: `AssignGroupModal.tsx` — If user deselects all groups, show inline message: _"Chọn ít nhất 1 group"_ (via i18n key `hint.assign_group_min`) using `.field-error` class
- [ ] AC6: `AssignGroupModal.tsx` — Inline message clears when at least 1 group is (re)selected
- [ ] AC7: No backend changes required for any item in this story

**Auth Requirement**
- [x] OIDC Bearer (admin session)

**Non-functional**
- Latency: N/A
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
Files: `frontend/admin-spa/src/components/ResetPasswordModal.tsx`, `frontend/admin-spa/src/components/AssignGroupModal.tsx`. AC3 already done — copy button setTimeout confirmed at line 71. For AC1: i18n key goes under `auth.reset_password.hint.password` in admin-spa locales (en/vi/ja/ko). Also add `.btn-eye` to admin-spa `index.css` (`.password-field-row` already exists at line 922, only `.btn-eye` missing).

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC4 | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | CSS class definitions verbatim from backlog | 2026-04-22 |
| AC5 | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | "Thêm vào index.css (frontend-spa) và admin-spa/src/index.css" | 2026-04-22 |
| AC6 | Decision D6 | CLAUDE.md / HOT.md Session #079 | "chỉ dùng index.css, không inline style, không CSS module, không Tailwind" | 2026-04-17 |
| AC7 | Business logic | Standard Vite build gate | Both SPAs must pass build to verify no CSS parse errors | 2026-04-24 |

### S002 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2 | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 | "Parse Pydantic 422 detail array → map loc[1]" | 2026-04-22 |
| AC3–AC5 | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 | Hint text strings specified verbatim | 2026-04-22 |
| AC6 | Decision D6 | CLAUDE.md | No inline styles | 2026-04-17 |
| AC7–AC8 | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 | "Hiện error inline ngay dưới field khi blur" | 2026-04-22 |
| AC9 | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Gaps | "test1@test.local bị backend reject 422 nhưng frontend chỉ hiện unexpected error" | 2026-04-22 |
| AC10 | Backlog | `docs/ux-form-validation/backlog.md` §Notes | "Không thay đổi backend validation logic" | 2026-04-22 |

### S003 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2 | Backlog | `docs/ux-form-validation/backlog.md` §BK-002 | "Thêm nút toggle show/hide password (icon eye)" | 2026-04-22 |
| AC3–AC4 | Business logic | WCAG 2.1 AA / accessibility standard | Keyboard accessibility + aria-label for interactive controls | 2026-04-24 |
| AC5 | Decision D6 | CLAUDE.md | No inline styles | 2026-04-17 |
| AC6 | Backlog | `docs/ux-form-validation/backlog.md` §BK-002 Gaps | "Lỗi generic… intentional per spec? — giữ nguyên generic vì security" | 2026-04-22 |

### S004 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC3 | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 | "confirmPassword không validate real-time" | 2026-04-22 |
| AC4 | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 | "Không có max length UX (backend cho phép tối đa 128)" | 2026-04-22 |
| AC5 | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 | Hint "8–128 ký tự" | 2026-04-22 |
| AC6 | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 | "Strength indicator… optional, có thể defer" | 2026-04-22 |
| AC7 | Business logic | Backend is authoritative validator | Client mismatch check is UX only; do not block submit | 2026-04-24 |

### S005 Sources
| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC2 | Backlog | `docs/ux-form-validation/backlog.md` §BK-004 | "Thêm hint text… Tối thiểu 8 ký tự; maxLength={128} + minLength={8}" | 2026-04-22 |
| AC3 | Backlog | `docs/ux-form-validation/backlog.md` §BK-004 | "Copy button: sau 2s reset về text gốc" | 2026-04-22 |
| AC4–AC6 | Backlog | `docs/ux-form-validation/backlog.md` §BK-005 | "Disable nút Save khi selectedGroupIds.length === 0; inline message" | 2026-04-22 |
| AC7 | Backlog | `docs/ux-form-validation/backlog.md` §Notes | "Không thay đổi backend validation logic" | 2026-04-22 |

# Sources Traceability: ux-form-validation
Created: 2026-04-24 | Feature spec: `docs/ux-form-validation/spec/ux-form-validation.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, backlog item, decision, or business logic).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: CSS Foundation — field-error, field-hint, password-field-row

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: `.field-error` in frontend-spa index.css | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | `font-size: 12px; color: var(--red); margin-top: 4px` verbatim | 2026-04-22 |
| AC2: `.field-hint` in frontend-spa index.css | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | `font-size: 11.5px; color: var(--text-3); margin-top: 4px` verbatim | 2026-04-22 |
| AC3: `.password-field-row` in frontend-spa index.css | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | `display: flex; gap: 8px; align-items: center` verbatim | 2026-04-22 |
| AC4: `.btn-eye` in frontend-spa index.css | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | `background: none; border: none; cursor: pointer; color: var(--text-3); padding: 4px` verbatim | 2026-04-22 |
| AC5: Same 4 classes in admin-spa index.css | Backlog | `docs/ux-form-validation/backlog.md` §CSS additions | "Thêm vào index.css (frontend-spa) và admin-spa/src/index.css" | 2026-04-22 |
| AC6: No inline styles / modules / Tailwind | Decision D6 | HOT.md Session #079; CLAUDE.md | Global Decision — CSS only via index.css | 2026-04-17 |
| AC7: Both SPAs build cleanly | Business logic | Vite build gate | Standard verification after CSS additions | 2026-04-24 |

### Story S002: UserFormModal — inline 422 parsing + field hints (Admin SPA)

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Parse 422 detail → inline field error | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Tasks | "Parse Pydantic 422 detail array → map loc[1]" | 2026-04-22 |
| AC2: Unmatched 422 → form-level error | Business logic | BrSE analysis | Graceful degradation; never show "unexpected error" for known HTTP 422 | 2026-04-24 |
| AC3: hint.sub under `sub` field | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Tasks | "3–200 ký tự, chỉ dùng a-z A-Z 0-9 _ . @ -" | 2026-04-22 |
| AC4: hint.email under `email` field | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Tasks | "Email phải là domain hợp lệ (vd: user@company.com)" | 2026-04-22 |
| AC5: hint.password_admin under `password` field | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Tasks | "Tối thiểu 12 ký tự" | 2026-04-22 |
| AC6: hints use `.field-hint` | Decision D6 | CLAUDE.md | CSS class constraint | 2026-04-17 |
| AC7: Blur triggers client-side validation | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Tasks | "Hiện error inline ngay dưới field khi blur (không chờ submit)" | 2026-04-22 |
| AC8: Inline errors clear on valid value | Business logic | Standard UX pattern | Inline error lifecycle | 2026-04-24 |
| AC9: test1@test.local → email field error | Backlog | `docs/ux-form-validation/backlog.md` §BK-001 Gaps | Specific regression scenario from gap analysis | 2026-04-22 |
| AC10: No backend changes | Backlog | `docs/ux-form-validation/backlog.md` §Notes | "Không thay đổi backend validation logic" | 2026-04-22 |

### Story S003: LoginForm — password show/hide toggle (Frontend SPA)

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: Eye toggle button with correct classes | Backlog | `docs/ux-form-validation/backlog.md` §BK-002 Tasks | "Thêm nút toggle show/hide password (icon eye)" | 2026-04-22 |
| AC2: Toggle switches input type | Backlog | `docs/ux-form-validation/backlog.md` §BK-002 Tasks | Standard show/hide behavior | 2026-04-22 |
| AC3: Keyboard accessible | Business logic | WCAG 2.1 AA | Interactive controls must be keyboard operable | 2026-04-24 |
| AC4: aria-label toggled | Business logic | WCAG 2.1 AA | Screen reader must announce current state | 2026-04-24 |
| AC5: No inline style | Decision D6 | CLAUDE.md | CSS class constraint | 2026-04-17 |
| AC6: Generic error unchanged | Backlog | `docs/ux-form-validation/backlog.md` §BK-002 Gaps | "intentional per spec — giữ nguyên generic vì security" | 2026-04-22 |

### Story S004: ChangePasswordModal + ChangePasswordPage — real-time confirm match (Frontend SPA)

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: ChangePasswordModal real-time mismatch error | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 Tasks | "confirmPassword không validate real-time" | 2026-04-22 |
| AC2: ChangePasswordPage same behavior | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 Files | Both files listed explicitly | 2026-04-22 |
| AC3: Error clears on match | Business logic | Standard UX pattern | Inline error lifecycle | 2026-04-24 |
| AC4: maxLength={128} on all password inputs | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 Tasks | "Không có max length UX (backend cho phép tối đa 128)" | 2026-04-22 |
| AC5: hint.password_user "8–128 ký tự" | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 Tasks | Verbatim hint string | 2026-04-22 |
| AC6: Strength indicator deferred | Backlog | `docs/ux-form-validation/backlog.md` §BK-003 Tasks | "optional, có thể defer" | 2026-04-22 |
| AC7: Submit not blocked by mismatch | Business logic | BrSE analysis | Backend is authoritative; blocking submit is over-constraint | 2026-04-24 |

### Story S005: ResetPasswordModal + AssignGroupModal (Admin SPA)

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: hint.password_reset "Tối thiểu 8 ký tự" | Backlog | `docs/ux-form-validation/backlog.md` §BK-004 Tasks | Verbatim hint + i18n direction | 2026-04-22 |
| AC2: maxLength={128} + minLength={8} on manual input | Backlog | `docs/ux-form-validation/backlog.md` §BK-004 Tasks | "Thêm maxLength={128} + minLength={8} trên input manual" | 2026-04-22 |
| AC3: Copy button resets after 2 000 ms | Backlog | `docs/ux-form-validation/backlog.md` §BK-004 Tasks | "sau 2s reset về text gốc (đã có logic copied state)" | 2026-04-22 |
| AC4: Save disabled when 0 groups selected | Backlog | `docs/ux-form-validation/backlog.md` §BK-005 Tasks | "Disable nút Save khi selectedGroupIds.length === 0" | 2026-04-22 |
| AC5: Inline empty-selection message | Backlog | `docs/ux-form-validation/backlog.md` §BK-005 Tasks | "Chọn ít nhất 1 group" | 2026-04-22 |
| AC6: Inline message clears on re-selection | Business logic | Standard UX pattern | Inline error lifecycle | 2026-04-24 |
| AC7: No backend changes | Backlog | `docs/ux-form-validation/backlog.md` §Notes | "Không thay đổi backend validation logic" | 2026-04-22 |

---

## Summary

**Total ACs:** 30
**Fully traced:** 30/30 ✓
**Pending sources:** 0

---

## Source Type Reference

| Type | Examples used in this feature |
|------|-------------------------------|
| **Backlog** | `docs/ux-form-validation/backlog.md` (primary source — created 2026-04-22) |
| **Decision D6** | Global CSS rule: index.css only, no inline/module/Tailwind |
| **Business logic** | BrSE analysis, WCAG 2.1 AA, standard UX patterns |

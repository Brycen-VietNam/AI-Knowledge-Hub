# UX Form Validation — Backlog
> Created: 2026-04-22 | Priority: Medium | Scope: frontend-spa + admin-spa

---

## Context
Tất cả CSS theo Decision D6: chỉ dùng `index.css`, không inline style, không CSS module, không Tailwind.
Backend constraint chính: password min 8 (users), min 12 (admin create), email phải là valid domain (Pydantic EmailStr reject `.local`, `.test`, `.example`).

---

## BK-001 — UserFormModal: inline field error + email hint (Admin SPA)
**File:** `frontend/admin-spa/src/components/UserFormModal.tsx`

### Gaps
- Email `test1@test.local` bị backend reject 422 nhưng frontend chỉ hiện "unexpected error" — user không biết lý do
- `sub` field chỉ dùng HTML5 `pattern` — browser tooltip không consistent cross-browser, không có hint text
- Password min 12 nhưng không có hint; error chỉ hiện sau submit
- 422 từ backend trả `detail[].loc + msg` nhưng frontend không parse field-level

### Tasks
- [ ] Parse Pydantic 422 `detail` array → map `loc[1]` (field name) → hiện inline dưới field tương ứng
- [ ] Thêm hint text dưới `sub` field: _"3–200 ký tự, chỉ dùng a-z A-Z 0-9 _ . @ -"_
- [ ] Thêm hint text dưới `email` field: _"Email phải là domain hợp lệ (vd: user@company.com)"_
- [ ] Thêm hint text dưới `password` field: _"Tối thiểu 12 ký tự"_
- [ ] Hiện error inline ngay dưới field khi blur (không chờ submit)

---

## BK-002 — LoginForm: password visibility toggle (Frontend SPA)
**File:** `frontend/src/components/auth/LoginForm.tsx`

### Gaps
- Không có nút show/hide password
- Lỗi generic, không phân biệt "sai mật khẩu" vs "user không tồn tại" (intentional per spec?) — giữ nguyên generic vì security

### Tasks
- [ ] Thêm nút toggle show/hide password (icon eye) trên field password
- [ ] CSS class `.password-field-row` đã có ở admin-spa — port sang `index.css` frontend-spa

---

## BK-003 — ChangePasswordModal + ChangePasswordPage: real-time confirm match (Frontend SPA)
**Files:** `frontend/src/components/auth/ChangePasswordModal.tsx`, `frontend/src/pages/ChangePasswordPage.tsx`

### Gaps
- `confirmPassword` không validate real-time — user nhập xong mới biết không khớp
- Không có max length UX (backend cho phép tối đa 128)
- Không có password strength indicator

### Tasks
- [ ] Real-time match check: khi `confirmPassword` onChange → hiện inline error ngay nếu không khớp
- [ ] Thêm `maxLength={128}` trên các input password + hint "8–128 ký tự"
- [ ] Strength indicator đơn giản: weak / medium / strong dựa trên length + complexity (optional, có thể defer)

---

## BK-004 — ResetPasswordModal: manual mode UX (Admin SPA)
**File:** `frontend/admin-spa/src/components/ResetPasswordModal.tsx`

### Gaps
- Manual mode: không có hint min 8 ký tự trước khi submit
- Generate mode: copy button chỉ đổi text thành "✓" — không có visual timeout reset
- Không có `maxLength` trên input

### Tasks
- [ ] Thêm hint text dưới password field (manual mode): _"Tối thiểu 8 ký tự"_
- [ ] Thêm `maxLength={128}` + `minLength={8}` trên input manual
- [ ] Copy button: sau 2s reset về text gốc (đã có logic `copied` state — chỉ cần style feedback rõ hơn)

---

## BK-005 — AssignGroupModal: prevent empty submission (Admin SPA)
**File:** `frontend/admin-spa/src/components/AssignGroupModal.tsx`

### Gaps
- Submit với 0 group được chọn → backend 422, frontend hiện generic error
- Không có pre-submit client-side check

### Tasks
- [ ] Disable nút Save khi `selectedGroupIds.length === 0`
- [ ] Thêm inline message: _"Chọn ít nhất 1 group"_ nếu user bỏ chọn tất cả

---

## CSS additions cần thiết (dùng chung)
Thêm vào `index.css` (frontend-spa) và `admin-spa/src/index.css`:

```css
/* Field-level inline error */
.field-error   { font-size: 12px; color: var(--red); margin-top: 4px; }

/* Field hint text */
.field-hint    { font-size: 11.5px; color: var(--text-3); margin-top: 4px; }

/* Password row with toggle button */
.password-field-row { display: flex; gap: 8px; align-items: center; }
.btn-eye { background: none; border: none; cursor: pointer; color: var(--text-3); padding: 4px; }
```

---

## Priority order
1. **BK-001** — gây bug thực tế (user không tạo được user vì email hint sai)
2. **BK-003** — ảnh hưởng UX hàng ngày (force-change + change password)
3. **BK-002** — quick win (password toggle)
4. **BK-005** — prevent silent 422
5. **BK-004** — polish

---

## Notes
- Không thay đổi backend validation logic — chỉ cải thiện frontend feedback
- Tất cả error message dùng i18n key (không hardcode tiếng Việt/Anh trực tiếp trong JSX)
- Test thủ công sau mỗi BK bằng docker build + up

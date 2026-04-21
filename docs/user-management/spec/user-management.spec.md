# Spec: user-management
Created: 2026-04-20 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | admin |
| Priority | P1 |
| Story count | 8 |
| Token budget est. | ~8k |
| Critical path | S001 → S003 → S004 → S005 → S006 → S007 → S008 |
| Parallel-safe stories | S001 + S002 (backend, parallel); S006 + S007 (frontend, parallel) |
| Blocking specs | — |
| Blocked by | admin-spa (DONE — `require_admin`, `/v1/admin/*` pattern, `api_keys` table) |
| Agents needed | api-agent (S001–S004), frontend-agent (S005–S008) |

### Problem Statement
Admin SPA không thể tạo hoặc xoá user. User hiện chỉ được seed qua migration.
Ngoài ra không có UI để quản lý API key cho service account / bot.
Cần CRUD đầy đủ: create/delete user + generate/revoke API key — tất cả qua admin UI.

### Solution Summary
- `POST /v1/admin/users` — tạo user với password (bcrypt), optional initial groups
- `DELETE /v1/admin/users/{id}` — xoá user + cascade memberships + api_keys
- `POST/GET/DELETE /v1/admin/users/{id}/api-keys` — generate (SHA-256 stored, plaintext one-time) + revoke
- Frontend: `UserFormModal` (create user), `ApiKeyPanel` (per-user key management)
- Frontend: `UsersTab` wired với Create button + Delete per-row + expand ApiKeyPanel

### Design Decisions
| # | Quyết định |
|---|------------|
| D1 | `sub` = admin tự nhập (username). Không auto-generate — admin kiểm soát rõ ràng. |
| D2 | `password` — admin nhập hoặc click "Generate" → 16-char secure string hiện 1 lần |
| D3 | API key tạo riêng per user — flow độc lập với create-user |
| D4 | Service account dùng group convention (group "Service Accounts") — không thêm column |
| D5 | API key format: `kh_<random_32_hex>` — stored as SHA-256 hash |

### OIDC Future-Proofing (ghi nhận, không implement)
- Khi SSO ready: `sub` = OIDC subject ID từ provider (vd: `azure|abc123`)
- `password_hash` = NULL cho OIDC users (column đã nullable từ migration 008)
- Không cần schema change — chỉ thêm "create without password" mode vào `UserFormModal`

### Out of Scope
- OIDC/SSO login flow (→ deferred)
- Email verification / password reset flow
- User self-registration (admin-only create)
- Audit log viewer UI
- API key cho human user (chỉ service account)

---

## LAYER 2 — Story Detail

---

### S001: Backend — POST /v1/admin/users (Create User)

**Role / Want / Value**
- As a: api-agent
- I want: endpoint tạo user mới với password
- So that: admin không cần seed user qua migration

**Acceptance Criteria**
- [ ] AC1: Endpoint protected by `require_admin`; non-admin → 403 (A005 shape)
- [ ] AC2: `UserCreate` Pydantic model: `sub` (str, required, 3–200 chars, pattern: `^[a-zA-Z0-9_.@-]+$`), `email` (optional, email format), `display_name` (optional, max 200 chars), `password` (str, required, min 12 chars), `group_ids` (list[int], optional, default=[])
- [ ] AC3: Duplicate `sub` → 409 `SUB_CONFLICT` (A005)
- [ ] AC4: `password` hashed bcrypt rounds=12; plaintext không bao giờ vào DB (S005)
- [ ] AC5: Strip whitespace + control chars từ tất cả string fields trước INSERT (S003)
- [ ] AC6: `email` validation RFC 5322-compatible; invalid → 422 (S003)
- [ ] AC7: SQL dùng `text().bindparams()` only — không có f-string với user value (S001)
- [ ] AC8: `group_ids` nếu có → INSERT memberships cùng transaction, `ON CONFLICT DO NOTHING` (P004)
- [ ] AC9: Success → HTTP 201 `{id, sub, email, display_name, is_active, groups}`
- [ ] AC10: DB error → rollback; response 500 A005 shape

**API Contract**
```
POST /v1/admin/users
Headers: Authorization: Bearer <admin_jwt>
Body: {
  "sub": "alice",
  "email": "alice@example.com",      // optional
  "display_name": "Alice",           // optional
  "password": "securepassword123",
  "group_ids": [1, 2]                // optional
}
Response 201: {
  "id": "<uuid>",
  "sub": "alice",
  "email": "alice@example.com",
  "display_name": "Alice",
  "is_active": true,
  "groups": [{"id": 1, "name": "...", "is_admin": false}]
}
Response 409: {"error": {"code": "SUB_CONFLICT", "message": "...", "request_id": "..."}}
Response 422: {"error": {"code": "INVALID_INPUT", "message": "...", "request_id": "..."}}
Response 403: {"error": {"code": "FORBIDDEN", "message": "...", "request_id": "..."}}
```

**Auth Requirement**
- [x] OIDC Bearer (human admin)  [ ] API-Key (bot)  [ ] Both

**Non-functional**
- Latency: < 500ms p95 (bcrypt rounds=12 ~200ms)
- Audit log: not required (admin action)
- CJK support: not applicable

**Implementation notes**
- File: `backend/api/routes/admin.py` — thêm sau `admin_list_users`
- Reuse `_error()` helper và `require_admin` dependency đã có
- `passlib[bcrypt]` — confirm trong `requirements.txt` (đã dùng ở `auth.py`)

---

### S002: Backend — DELETE /v1/admin/users/{user_id} (Delete User)

**Role / Want / Value**
- As a: api-agent
- I want: endpoint xoá user và toàn bộ dữ liệu liên quan
- So that: admin có thể dọn sạch account không còn dùng

**Acceptance Criteria**
- [ ] AC1: Protected by `require_admin`; non-admin → 403 (A005)
- [ ] AC2: Unknown `user_id` → 404 (A005)
- [ ] AC3: Xoá rows trong `api_keys` WHERE `user_id` trước
- [ ] AC4: Xoá rows trong `user_group_memberships` WHERE `user_id` trước
- [ ] AC5: Xoá user row — tất cả trong cùng transaction; rollback nếu lỗi
- [ ] AC6: SQL dùng `text().bindparams()` (S001)
- [ ] AC7: Success → 200 `{"deleted": "<user_id>"}`

**API Contract**
```
DELETE /v1/admin/users/{user_id}
Headers: Authorization: Bearer <admin_jwt>
Response 200: {"deleted": "<uuid>"}
Response 404: {"error": {"code": "NOT_FOUND", "message": "...", "request_id": "..."}}
Response 403: {"error": {"code": "FORBIDDEN", ...}}
```

**Auth Requirement**
- [x] OIDC Bearer (human admin)  [ ] API-Key  [ ] Both

**Non-functional**
- Latency: < 500ms p95
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
- File: `backend/api/routes/admin.py`
- Thứ tự DELETE: api_keys → user_group_memberships → users (tránh FK violation)
- Kiểm tra FK constraints trên `audit_logs.user_id` — nếu có RESTRICT thì cần xoá trước

---

### S003: Backend — POST /v1/admin/users/{user_id}/api-keys (Generate API Key)

**Role / Want / Value**
- As a: api-agent
- I want: endpoint generate API key cho service account user
- So that: bot/app có thể gọi `/v1/query` bằng API key

**Acceptance Criteria**
- [ ] AC1: Protected by `require_admin`; non-admin → 403 (A005)
- [ ] AC2: Unknown `user_id` → 404 (A005)
- [ ] AC3: Generate key: `kh_` + `secrets.token_hex(16)` (36 chars total)
- [ ] AC4: Store SHA-256 hash của key trong `api_keys` table (`key_hash` column)
- [ ] AC5: Store `key_prefix` = 8 ký tự đầu của plaintext key (để admin nhận diện)
- [ ] AC6: `name` optional label từ request body (max 100 chars)
- [ ] AC7: **Trả về plaintext key 1 lần duy nhất** trong response — không lưu plaintext (S005)
- [ ] AC8: Response: `{key_id, key: "kh_...", key_prefix, name, created_at}`
- [ ] AC9: SQL parameterized (S001)

**API Contract**
```
POST /v1/admin/users/{user_id}/api-keys
Headers: Authorization: Bearer <admin_jwt>
Body: {"name": "teams-bot"}   // optional
Response 201: {
  "key_id": "<uuid>",
  "key": "kh_abcdef1234567890abcdef1234567890",  // plaintext — shown ONCE
  "key_prefix": "kh_abcdef",
  "name": "teams-bot",
  "created_at": "2026-04-20T..."
}
Response 404: {"error": {"code": "NOT_FOUND", ...}}
Response 403: {"error": {"code": "FORBIDDEN", ...}}
```

**Auth Requirement**
- [x] OIDC Bearer (human admin)  [ ] API-Key  [ ] Both

**Non-functional**
- Latency: < 200ms p95
- Audit log: not required
- CJK support: not applicable

**Implementation notes**
- File: `backend/api/routes/admin.py`
- `api_keys` table đã có (migration 004) — kiểm tra schema: cần `key_hash`, `key_prefix`, `name`, `user_id`, `created_at`
- `hashlib.sha256(key.encode()).hexdigest()` để tạo hash

---

### S004: Backend — GET + DELETE /v1/admin/users/{user_id}/api-keys

**Role / Want / Value**
- As a: api-agent
- I want: list và revoke API keys của user
- So that: admin có thể quản lý vòng đời key

**Acceptance Criteria**
- [ ] AC1: `GET /v1/admin/users/{user_id}/api-keys` → `{"items": [{key_id, key_prefix, name, created_at}]}` — không bao giờ trả về plaintext key hay hash
- [ ] AC2: Unknown `user_id` trong GET → 404 (A005)
- [ ] AC3: `DELETE /v1/admin/users/{user_id}/api-keys/{key_id}` → revoke (xoá row)
- [ ] AC4: Unknown `key_id` trong DELETE → 404 (A005)
- [ ] AC5: Cả 2 protected by `require_admin`
- [ ] AC6: SQL parameterized (S001)
- [ ] AC7: DELETE success → 200 `{"revoked": "<key_id>"}`

**API Contract**
```
GET /v1/admin/users/{user_id}/api-keys
Response 200: {"items": [{"key_id": "...", "key_prefix": "kh_abcdef", "name": "teams-bot", "created_at": "..."}]}

DELETE /v1/admin/users/{user_id}/api-keys/{key_id}
Response 200: {"revoked": "<key_id>"}
Response 404: {"error": {"code": "NOT_FOUND", ...}}
```

**Auth Requirement**
- [x] OIDC Bearer (human admin)  [ ] API-Key  [ ] Both

**Non-functional**
- Latency: < 200ms p95
- Audit log: not required
- CJK support: not applicable

---

### S005: Frontend — adminApi.ts additions

**Role / Want / Value**
- As a: frontend-agent
- I want: API client functions cho user CRUD và key management
- So that: UI components có typed interface để gọi backend

**Acceptance Criteria**
- [ ] AC1: `createUser(payload: UserCreatePayload): Promise<UserItem>` — POST `/v1/admin/users`
- [ ] AC2: `deleteUser(userId: string): Promise<void>` — DELETE `/v1/admin/users/{userId}`
- [ ] AC3: `generateApiKey(userId: string, name?: string): Promise<ApiKeyCreated>` — POST api-keys
- [ ] AC4: `listApiKeys(userId: string): Promise<ApiKeyItem[]>` — GET api-keys
- [ ] AC5: `revokeApiKey(userId: string, keyId: string): Promise<void>` — DELETE api-keys/{keyId}
- [ ] AC6: Interfaces exported: `UserCreatePayload`, `ApiKeyCreated`, `ApiKeyItem`
- [ ] AC7: Lỗi HTTP từ server được re-throw với status code để caller xử lý (pattern hiện tại)

**Implementation notes**
- File: `frontend/admin-spa/src/api/adminApi.ts`
- Reuse `apiClient` (axios instance đã có)
- `UserCreatePayload`: `{sub, email?, display_name?, password, group_ids?}`
- `ApiKeyCreated`: `{key_id, key, key_prefix, name, created_at}` — `key` chỉ có khi vừa tạo
- `ApiKeyItem`: `{key_id, key_prefix, name, created_at}` — không có `key`

---

### S006: Frontend — UserFormModal (Create User)

**Role / Want / Value**
- As a: frontend-agent
- I want: modal form để tạo user mới
- So that: admin có UI rõ ràng thay vì gọi API thủ công

**Acceptance Criteria**
- [ ] AC1: Component file: `frontend/admin-spa/src/components/UserFormModal.tsx` (NEW)
- [ ] AC2: Fields: `sub` (text, required, pattern validate), `email` (email input, optional), `display_name` (text, optional), `password` (type="password", required, min 12), Groups (checkbox list từ `listGroups()`)
- [ ] AC3: "Generate password" button → `crypto.getRandomValues` 16-char alphanumeric → điền vào field + tạm thời hiện plaintext để user copy
- [ ] AC4: Submit disabled khi in-flight; spinner/loading state
- [ ] AC5: 409 từ server → inline error "Username already taken" — modal không đóng
- [ ] AC6: 422 từ server → inline error với message từ server — modal không đóng
- [ ] AC7: Success → `onSave(createdUser)` callback → modal đóng
- [ ] AC8: Props: `onSave: (user: UserItem) => void`, `onClose: () => void`, `groups: GroupItem[]`
- [ ] AC9: Strings i18n qua `t()` — không hardcode English trong JSX

**Implementation notes**
- Pattern: copy từ `frontend/admin-spa/src/components/GroupFormModal.tsx`
- Password field: NEVER `type="text"` — luôn `type="password"` trừ khi user click "show"
- Groups: reuse `GroupItem` type từ `adminApi.ts`; fetch groups từ caller (`UsersTab`) rồi pass qua props

---

### S007: Frontend — ApiKeyPanel (per-user key management)

**Role / Want / Value**
- As a: frontend-agent
- I want: UI quản lý API keys của một user
- So that: admin có thể generate và revoke keys không cần dùng API trực tiếp

**Acceptance Criteria**
- [ ] AC1: Component file: `frontend/admin-spa/src/components/ApiKeyPanel.tsx` (NEW)
- [ ] AC2: List API keys của user: hiện `key_prefix`, `name`, `created_at` — không hiện hash
- [ ] AC3: "Generate Key" button → optional name input → call `generateApiKey()` → hiện plaintext key trong one-time dialog với message "Copy this key now — it won't be shown again"
- [ ] AC4: One-time key dialog: copy-to-clipboard button + "I've copied it" dismiss button
- [ ] AC5: Revoke button per key → confirm dialog (reuse `DeleteConfirmDialog`) → call `revokeApiKey()`
- [ ] AC6: After revoke → key biến khỏi list
- [ ] AC7: Props: `userId: string`
- [ ] AC8: Strings i18n qua `t()`

**Implementation notes**
- File: `frontend/admin-spa/src/components/ApiKeyPanel.tsx`
- Reuse `DeleteConfirmDialog` component (đã có)
- Panel embed trong `UsersTab` như expanded row hoặc collapsible section per user

---

### S008: Frontend — UsersTab.tsx wiring

**Role / Want / Value**
- As a: frontend-agent
- I want: UsersTab có đầy đủ Create, Delete, API key management
- So that: admin workflow hoàn chỉnh không cần rời khỏi tab

**Acceptance Criteria**
- [ ] AC1: "Create User" button trong `tab-toolbar` div, class `btn-primary`, matching GroupsTab pattern
- [ ] AC2: Click Create → mở `UserFormModal`; sau `onSave` → refresh list
- [ ] AC3: Delete button per-row (class `btn-danger`) → `DeleteConfirmDialog` → `deleteUser()` → refresh list
- [ ] AC4: Delete 404 từ server → error toast; row không bị remove ngay lập tức
- [ ] AC5: Expand per-row → hiện `ApiKeyPanel` cho user đó (collapsible)
- [ ] AC6: Toggle-active không bị regression sau refactor
- [ ] AC7: `modalMode` state thêm vào: `null | 'create'`
- [ ] AC8: Groups fetched 1 lần khi tab load → pass vào `UserFormModal` qua props

**Implementation notes**
- File: `frontend/admin-spa/src/components/UsersTab.tsx`
- Reuse `DeleteConfirmDialog` (đã có)
- Reuse `listGroups()` (đã có trong `adminApi.ts`)
- Pattern: xem `GroupsTab.tsx` cho `modalMode`, toolbar button, modal wiring

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Conversation | Plan session — user approved | 2026-04-20 |
| AC2–AC9 | Conversation | Backlog planning — create user flow | 2026-04-20 |
| AC4 | Rule | HARD.md S005 — no secrets in DB | — |
| AC5 | Rule | SECURITY.md S003 — input sanitization | — |
| AC7 | Rule | SECURITY.md S001 — no SQL injection | — |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC7 | Conversation | Backlog planning — delete user | 2026-04-20 |

### S003–S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| All | Conversation | Backlog planning — API key cho service account | 2026-04-20 |
| AC7 (S003) | Rule | HARD.md S005 — plaintext không persist | — |
| D5 | Decision | SHA-256 hash stored, `kh_` prefix format | 2026-04-20 |

### S005–S008 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| All | Conversation | Backlog planning — frontend wiring | 2026-04-20 |
| Pattern | Existing code | `GroupFormModal.tsx`, `GroupsTab.tsx`, `DeleteConfirmDialog.tsx` | — |

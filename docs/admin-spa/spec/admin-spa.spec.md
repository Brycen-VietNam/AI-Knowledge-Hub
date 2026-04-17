# Spec: admin-spa
Created: 2026-04-17 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | frontend |
| Priority | P1 |
| Story count | 6 |
| Token budget est. | ~7k |
| Critical path | S000 → S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S002, S003, S004 (after S001) |
| Blocking specs | — |
| Blocked by | frontend-spa (DONE — auth endpoint reused), document-ingestion (DONE) |
| Agents needed | db-agent (S000), api-agent (S000), frontend-agent (S001–S005) |

### Problem Statement
Admin users không có giao diện để quản lý documents, users, và groups trong hệ thống.
Hiện tại document upload chỉ qua API/script (api_key), không có UI cho quản trị.
Admin-SPA là internal tool — deploy riêng, chỉ admin group mới truy cập được.

### Solution Summary
- React/Vite SPA — internal deploy, chỉ dành cho admin users
- Admin gate: user thuộc `user_group` có `is_admin=true` flag mới được vào
- Document management: list / upload / delete (JWT admin được write — mở rộng D09)
- User & Group management: CRUD groups (với is_admin flag), assign user→group
- Metrics dashboard: query volume, document count, system health
- Build artifact + Dockerfile — deploy độc lập với frontend-spa

### Out of Scope
- End-user query interface (→ frontend-spa)
- Conflict detection UI (→ sau khi conflict-detection feature done)
- OIDC/SSO (→ deferred)
- Real-time / websocket
- Bot management (Teams/Slack config)
- Audit log viewer UI (→ future feature)

---

## LAYER 2 — Story Detail

---

### S000: Backend — Admin Group Flag + Admin Endpoints (prerequisite)

**Role / Want / Value**
- As a: db-agent + api-agent
- I want: `is_admin` flag trên `user_groups` + `/v1/admin/*` endpoints
- So that: admin-SPA có thể phân quyền admin và gọi các endpoint quản trị

**Acceptance Criteria**
- [ ] AC1: Migration `009_add_admin_group_flag.sql` — `ALTER TABLE user_groups ADD COLUMN is_admin BOOL NOT NULL DEFAULT FALSE`
- [ ] AC2: `AuthenticatedUser` dataclass thêm field `is_admin: bool` (computed từ group membership khi verify_token)
- [ ] AC3: `verify_token` dependency update — set `is_admin=True` nếu user thuộc ≥1 group có `is_admin=true`
- [ ] AC4: `GET /v1/admin/documents` — trả về tất cả documents (không RBAC filter), paginated (limit/offset), yêu cầu is_admin
- [ ] AC5: `DELETE /v1/admin/documents/{doc_id}` — xóa document + embeddings, yêu cầu is_admin
- [ ] AC6: `GET /v1/admin/groups` — list tất cả user_groups (id, name, is_admin, user_count)
- [ ] AC7: `POST /v1/admin/groups` — tạo group mới (name, is_admin flag)
- [ ] AC8: `PUT /v1/admin/groups/{id}` — cập nhật group (name, is_admin)
- [ ] AC9: `DELETE /v1/admin/groups/{id}` — xóa group (không xóa nếu có users)
- [ ] AC10: `GET /v1/admin/users` — list tất cả users (id, sub, email, display_name, is_active, groups)
- [ ] AC11: `POST /v1/admin/users/{user_id}/groups` — assign user vào group(s)
- [ ] AC12: `DELETE /v1/admin/users/{user_id}/groups/{group_id}` — remove user khỏi group
- [ ] AC13: Document write gate mở rộng: `api_key` OR (`jwt` AND `user.is_admin`) được phép POST/DELETE documents
- [ ] AC14: `/v1/auth/token` response thêm field `is_admin: bool` (từ group membership)
- [ ] AC15: Non-admin user gọi `/v1/admin/*` → 403 `{"error": {"code": "FORBIDDEN", "message": "Admin access required"}}`

**API Contract**
```
GET /v1/admin/documents?limit=20&offset=0
Headers: Authorization: Bearer <admin-jwt>
Response 200: {
  "items": [{"id": "...", "title": "...", "lang": "...", "user_group_id": N, "status": "...", "created_at": "...", "chunk_count": N}],
  "total": N,
  "limit": 20,
  "offset": 0
}
Response 403: {"error": {"code": "FORBIDDEN", "message": "Admin access required", "request_id": "..."}}

POST /v1/admin/groups
Body: {"name": "...", "is_admin": false}
Response 201: {"id": N, "name": "...", "is_admin": false, "created_at": "..."}

POST /v1/admin/users/{user_id}/groups
Body: {"group_ids": [1, 2]}
Response 200: {"user_id": "...", "group_ids": [1, 2]}

POST /v1/auth/token  (updated response)
Response 200: {"access_token": "...", "token_type": "bearer", "expires_in": 3600, "is_admin": true}
```

**Auth Requirement**
- [x] JWT Bearer — is_admin=true required for /v1/admin/* routes
- [x] API-Key retains existing write access

**Non-functional**
- Latency: < 500ms per admin endpoint
- Audit log: required for document delete, group delete (admin actions)
- Migration: C010 — numbered file 009 required before model update

**Implementation notes**
- File mới: `backend/api/routes/admin.py` (tất cả /v1/admin/* routes)
- Migration: `backend/db/migrations/009_add_admin_group_flag.sql`
- `UserGroup` model: add `is_admin: Mapped[bool]`
- `AuthenticatedUser`: add `is_admin: bool = False`
- Cần join `users → user_group_memberships → user_groups` để compute is_admin khi verify_token

> **Assumption**: Hiện tại chưa có `user_group_memberships` junction table — cần kiểm tra và có thể cần migration thêm. Confirm tại /clarify.

---

### S001: Admin Login + Admin Gate

**Role / Want / Value**
- As a: admin user
- I want: đăng nhập bằng username + password và hệ thống kiểm tra quyền admin
- So that: chỉ admin mới vào được Admin-SPA

**Acceptance Criteria**
- [ ] AC1: Login form: username + password + nút Submit (giống frontend-spa)
- [ ] AC2: Submit gọi `POST /v1/auth/token`, nhận JWT + `is_admin` flag
- [ ] AC3: JWT lưu trong memory (không localStorage — D02 from frontend-spa)
- [ ] AC4: Nếu `is_admin=false` sau login → hiển thị "Access denied. Admin privileges required." Không cho vào dashboard.
- [ ] AC5: Nếu `is_admin=true` → redirect sang `/dashboard`
- [ ] AC6: Token hết hạn → redirect về login, thông báo "Session expired"
- [ ] AC7: Logout xóa token khỏi memory, redirect về login
- [ ] AC8: Khi chưa login, mọi route → redirect sang `/login`
- [ ] AC9: Login error (401) hiển thị message rõ ràng, không expose backend detail
- [ ] AC10: UI language selector: ja / en / vi / ko (persist localStorage — D03 from frontend-spa)

**API Contract**
```
POST /v1/auth/token
Body: {"username": "...", "password": "..."}
Response 200: {"access_token": "...", "token_type": "bearer", "expires_in": 3600, "is_admin": true}
Response 401: {"error": {"code": "AUTH_FAILED", "message": "Invalid credentials"}}
```

**Auth Requirement**
- [x] JWT Bearer (admin gate — is_admin=true required)

**Non-functional**
- Latency: < 500ms login response
- CJK support: i18n ja / en / vi / ko (react-i18next — D03)

**Implementation notes**
- Reuse auth flow pattern từ frontend-spa S001
- Token store: React context / Zustand (in-memory only — D02)
- `is_admin` từ token response dùng để gate route access
- Axios interceptor: tự động attach Bearer + handle 401

---

### S002: Document Management

**Role / Want / Value**
- As a: admin user
- I want: xem, upload, và xóa documents trong hệ thống
- So that: tôi quản lý knowledge base mà không cần gọi API thủ công

**Acceptance Criteria**
- [ ] AC1: Document list table: columns — Title, Language, Group, Status, Created At, Chunk Count, Actions
- [ ] AC2: Pagination: 20 items/page, prev/next controls
- [ ] AC3: Filter by: status (pending/processing/ready/error), language, user_group
- [ ] AC4: Upload modal: nhập Title + paste/type Content + chọn Language + chọn Group (optional)
- [ ] AC5: Upload gọi `POST /v1/documents` với JWT admin Bearer (write gate mở rộng từ S000 AC13)
- [ ] AC6: Upload success → refresh list, hiển thị toast "Document uploaded successfully"
- [ ] AC7: Delete button với confirm dialog: "Delete document '{title}'? This cannot be undone."
- [ ] AC8: Delete gọi `DELETE /v1/admin/documents/{id}`, success → remove khỏi list
- [ ] AC9: Status badge màu: ready=green, processing=yellow, pending=gray, error=red
- [ ] AC10: Document list không RBAC filter — admin thấy tất cả documents

**API Contract**
```
GET /v1/admin/documents?limit=20&offset=0&status=ready&lang=ja
Headers: Authorization: Bearer <admin-jwt>
Response 200: {"items": [...], "total": N, "limit": 20, "offset": 0}

POST /v1/documents
Headers: Authorization: Bearer <admin-jwt>
Body: {"title": "...", "content": "...", "lang": "ja", "user_group_id": 1}
Response 202: {"id": "...", "status": "pending"}

DELETE /v1/admin/documents/{doc_id}
Response 204: (no body)
Response 404: {"error": {"code": "NOT_FOUND", "message": "..."}}
```

**Auth Requirement**
- [x] JWT Bearer — is_admin=true required

**Non-functional**
- Latency: list < 500ms, upload < 2s
- Audit log: required for delete (AC8)
- CJK support: ja / vi / ko — title display + language filter

**Implementation notes**
- Reuse `POST /v1/documents` từ document-ingestion (write gate mở rộng)
- Delete dùng endpoint mới `/v1/admin/documents/{id}` từ S000
- Content input: textarea (không file upload trong scope này — raw text only)

> **Assumption**: Upload là raw text content (không phải file upload binary). File upload (PDF, DOCX) là out of scope cho admin-spa v1. Confirm tại /clarify.

---

### S003: User & Group Management

**Role / Want / Value**
- As a: admin user
- I want: quản lý users và groups — tạo/sửa/xóa groups, assign user vào group
- So that: tôi kiểm soát RBAC cho toàn hệ thống

**Acceptance Criteria**
- [ ] AC1: Groups tab: list tất cả groups (Name, Is Admin, User Count, Actions)
- [ ] AC2: Tạo group: modal với Name + Is Admin toggle
- [ ] AC3: Edit group: sửa name, toggle is_admin
- [ ] AC4: Delete group: confirm dialog + không xóa được nếu group còn users (backend 409 → hiển thị lỗi)
- [ ] AC5: Users tab: list tất cả users (Sub/Email, Display Name, Active, Groups, Actions)
- [ ] AC6: Assign user→group: multi-select dropdown, gọi `POST /v1/admin/users/{id}/groups`
- [ ] AC7: Remove user khỏi group: nút X trên group badge, gọi `DELETE /v1/admin/users/{id}/groups/{group_id}`
- [ ] AC8: Toggle user active/inactive: `PUT /v1/admin/users/{id}` (update is_active)
- [ ] AC9: Search/filter users by email hoặc sub (client-side filter trên loaded list)

**API Contract**
```
GET /v1/admin/groups
Response 200: [{"id": 1, "name": "hr-japan", "is_admin": false, "user_count": 5}]

POST /v1/admin/groups
Body: {"name": "...", "is_admin": false}
Response 201: {"id": N, "name": "...", "is_admin": false}

DELETE /v1/admin/groups/{id}
Response 204
Response 409: {"error": {"code": "CONFLICT", "message": "Cannot delete group with active users"}}

GET /v1/admin/users
Response 200: [{"id": "...", "sub": "...", "email": "...", "display_name": "...", "is_active": true, "groups": [...]}]
```

**Auth Requirement**
- [x] JWT Bearer — is_admin=true required

**Non-functional**
- Latency: < 500ms per endpoint
- Audit log: required cho group create/delete, user group assignment
- CJK support: display_name có thể chứa CJK chars — render đúng

**Implementation notes**
- `PUT /v1/admin/users/{id}` cần endpoint mới (update is_active) — add vào S000 nếu không đủ scope → flag tại /clarify
- Client-side search ổn cho internal tool (user count typically < 1000)

---

### S004: Metrics Dashboard

**Role / Want / Value**
- As a: admin user
- I want: xem metrics hệ thống — query volume, documents, users, health
- So that: tôi monitor hoạt động của knowledge platform

**Acceptance Criteria**
- [ ] AC1: Dashboard page là landing page sau login (`/dashboard`)
- [ ] AC2: Cards hiển thị: Total Documents, Total Users, Total Groups, Active Documents (status=ready)
- [ ] AC3: Query volume chart: số queries theo ngày (7 ngày gần nhất) — từ audit_logs
- [ ] AC4: System health indicators: Database (green/red), Backend API (green/red)
- [ ] AC5: `GET /v1/metrics` trả về aggregate data — admin only
- [ ] AC6: Dashboard auto-refresh mỗi 60 giây
- [ ] AC7: Nếu `/v1/metrics` fail → hiển thị "Metrics unavailable" (không crash)

**API Contract**
```
GET /v1/metrics
Headers: Authorization: Bearer <admin-jwt>
Response 200: {
  "documents": {"total": N, "ready": N, "processing": N, "error": N},
  "users": {"total": N, "active": N},
  "groups": {"total": N},
  "queries": {"last_7_days": [{"date": "2026-04-17", "count": N}, ...]}
}
Response 403: {"error": {"code": "FORBIDDEN", ...}}
```

**Auth Requirement**
- [x] JWT Bearer — is_admin=true required

**Non-functional**
- Latency: < 1s (aggregate query)
- CJK support: not applicable
- Audit log: not required (read-only metrics)

**Implementation notes**
- `/v1/metrics` endpoint: kiểm tra xem đã có chưa, nếu chưa → api-agent implement trong S000
- Chart library: recharts (lightweight, đã common trong React ecosystem)
- Auto-refresh: `setInterval` 60s, clear on unmount

> **Assumption**: `/v1/metrics` endpoint chưa implement (chỉ mention trong CLAUDE.md stack). Cần backend story trong S000. Confirm tại /clarify.

---

### S005: Build & Docker Packaging

**Role / Want / Value**
- As a: DevOps / developer
- I want: build static artifact và Docker image cho admin-SPA
- So that: deploy internal admin tool độc lập với frontend-spa

**Acceptance Criteria**
- [ ] AC1: `npm run build` tạo `dist/` — static files sẵn sàng serve
- [ ] AC2: Dockerfile multi-stage: `node:20-alpine` build → `nginx:alpine` serve (D07 from frontend-spa)
- [ ] AC3: Nginx config serve `index.html` cho mọi route (SPA fallback)
- [ ] AC4: API base URL cấu hình qua `VITE_API_BASE_URL` env var (không hardcode)
- [ ] AC5: Docker port: `8081:80` (tránh conflict: backend=8000, frontend-spa=8080, dev=3000)
- [ ] AC6: Build thành công với `npm run build` không có error/warning
- [ ] AC7: `.env.example` có đầy đủ env vars: `VITE_API_BASE_URL`
- [ ] AC8: Docker image chạy được với `docker run -p 8081:80 -e VITE_API_BASE_URL=http://... admin-spa`

**Non-functional**
- Docker image size < 50MB (nginx:alpine base)
- Build time < 60s

**Implementation notes**
- Tạo `frontend/admin-spa/` directory (tách khỏi `frontend/` của public-spa)
- Hoặc monorepo trong `frontend/` với subdirectory — confirm tại /clarify
- nginx.conf: `try_files $uri $uri/ /index.html;` (same as frontend-spa)
- Multi-stage build: copy `dist/` từ builder stage vào nginx stage

> **Assumption**: admin-spa nằm ở `frontend/admin-spa/` (separate Vite project từ `frontend/` của public-spa). Confirm structure tại /clarify.

---

## LAYER 3 — Sources Traceability

### S000 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Conversation | lb_mui 2026-04-17 — chọn is_admin flag trên user_groups | 2026-04-17 |
| AC2–AC3 | Business logic | AuthenticatedUser phải carry admin context — computed at verify_token | 2026-04-17 |
| AC4–AC5 | Conversation | Admin doc list cần bypass RBAC (admin privilege) | 2026-04-17 |
| AC6–AC12 | Conversation | lb_mui: "full CRUD groups + assign user→group" | 2026-04-17 |
| AC13 | Conversation | lb_mui: "Mở rộng: JWT admin được write" | 2026-04-17 |
| AC14 | Business logic | Frontend cần biết is_admin ngay sau login — thêm vào token response | 2026-04-17 |
| AC15 | Existing behavior | HARD.md R003 pattern — auth required, 403 for unauthorized admin | 2026-04-17 |

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC9 | Existing behavior | frontend-spa S001 pattern — reuse login flow (D02, D03, D05) | 2026-04-17 |
| AC4 | Conversation | Admin gate: is_admin từ token response → block non-admin | 2026-04-17 |
| AC10 | Existing behavior | frontend-spa D03 — UI language selector ja/en/vi/ko | 2026-04-17 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC10 | Conversation | lb_mui 2026-04-16 — "Document upload / management → admin-spa" (frontend-spa Out of Scope) | 2026-04-16 |
| AC5 | Conversation | lb_mui 2026-04-17 — "JWT admin được write" (write gate mở rộng) | 2026-04-17 |
| AC7 | Business logic | Destructive action cần confirm dialog — UX safety pattern | 2026-04-17 |
| AC10 | Business logic | Admin bypass RBAC filter — admin thấy tất cả documents | 2026-04-17 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC9 | Conversation | lb_mui 2026-04-17 — "full CRUD groups, assign user→group" | 2026-04-17 |
| AC4 | Business logic | RBAC integrity — không xóa group còn users (data integrity) | 2026-04-17 |
| AC8 | Business logic | Admin cần deactivate user mà không xóa (audit trail preservation) | 2026-04-17 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC7 | Existing behavior | CLAUDE.md — /v1/metrics listed trong stack; admin dashboard UX standard | 2026-04-17 |
| AC3 | Business logic | audit_logs table đã có (migration 001) — query count aggregation | 2026-04-17 |

### S005 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC8 | Existing behavior | frontend-spa S005 — reuse D07 Docker pattern, same structure | 2026-04-17 |
| AC5 | Business logic | Port 8081:80 tránh conflict với frontend-spa (8080:80) — D13 pattern | 2026-04-17 |

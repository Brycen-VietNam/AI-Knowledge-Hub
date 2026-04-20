# Clarify: admin-spa
Generated: 2026-04-17 | Spec: DRAFT | Feature: admin-spa

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | `user_group_memberships` junction table — tồn tại chưa? Hay users dùng mảng khác? | ✅ **RESOLVED: junction table.** Migration 009 cần tạo `user_group_memberships(user_id UUID FK users, group_id INT FK user_groups, PRIMARY KEY (user_id, group_id))`. `verify_token` dùng JOIN để compute `is_admin`. | lb_mui | ✅ |
| Q2 | `/v1/metrics` endpoint đã implement chưa? | ✅ **RESOLVED: NOT found — thêm vào S000 scope.** api-agent implement `GET /v1/metrics` trong S000. Admin-only endpoint. | lb_mui | ✅ |
| Q3 | Upload scope: raw text content (textarea) hay file upload (PDF/DOCX) cho admin-spa v1? | ✅ **RESOLVED: file upload — đáp ứng tất cả formats backend hỗ trợ.** Backend có `POST /v1/documents/upload` (multipart/form-data) hỗ trợ: PDF, DOCX, HTML, TXT, MD (qua `ParserFactory`). Admin-SPA dùng file input + gọi endpoint này (không phải textarea `POST /v1/documents`). | lb_mui | ✅ |
| Q4 | `PUT /v1/admin/users/{id}` (toggle is_active) — thuộc S000 hay story riêng? | ✅ **RESOLVED: thêm vào S000.** Endpoint đơn giản (`UPDATE users SET is_active=:val WHERE id=:id`), cùng file `admin.py`, cùng api-agent scope. Tách story chỉ kéo dài critical path của S003. | lb_mui | ✅ |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q5 | admin-spa directory structure: `frontend/admin-spa/` hay monorepo trong `frontend/`? | **Assume**: `frontend/admin-spa/` — separate Vite project (D07). Monorepo chỉ khi user confirm muốn shared deps/config. |
| Q6 | `user_groups` bảng hiện tại có cột nào khác ngoài id + name không? | **Assume**: chỉ có `id, name` (migration 001). Migration 009 sẽ `ADD COLUMN is_admin BOOL NOT NULL DEFAULT FALSE`. |
| Q7 | Chart library cho S004 metrics dashboard: recharts hay thư viện khác? | **Assume**: recharts (lightweight, React-native, không cần D3 knowledge). Override nếu frontend-spa đã dùng thư viện khác. |
| Q8 | S004 auto-refresh 60s — dùng `setInterval` hay react-query `refetchInterval`? | **Assume**: `setInterval` + `useEffect` cleanup (đơn giản, không cần react-query). Nếu frontend-spa đã dùng react-query thì override. |
| Q9 | Admin-SPA có cần dark mode không? | **Assume**: không (internal tool, v1 scope minimal). |
| Q10 | Group delete 409 (còn users) — frontend có cần show danh sách users cụ thể không? | **Assume**: chỉ cần toast "Cannot delete: group has active users" (không list chi tiết). |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q11 | UI animation/transition khi chuyển tab (Documents / Users / Groups)? |
| Q12 | Export CSV cho document list hoặc user list? |
| Q13 | Admin activity log viewer (xem ai xóa document nào, khi nào)? |
| Q14 | Pagination cho user list (S003 AC9 dùng client-side search — server-side nếu user count > 1000)? |

---

## Auto-answered from existing files

| Q | Answer | Source |
|---|--------|--------|
| ARCH A002 | Dependency: `frontend → api → rag → db`. Admin-SPA vẫn phải đi qua `/v1/admin/*` — không direct DB access. | ARCH.md A002 |
| HARD R003 | Tất cả `/v1/admin/*` endpoints phải có `Depends(verify_token)` — không anonymous access. | HARD.md R003 |
| HARD R001 | Admin doc list bypasses RBAC filter — nhưng vẫn cần is_admin guard TRƯỚC khi return. | HARD.md R001 |
| Auth: JWT in-memory | D02 (từ frontend-spa) — không localStorage. Admin-SPA kế thừa pattern. | WARM/admin-spa.mem.md D02 |
| Auth: UI language | D03 (từ frontend-spa) — ja/en/vi/ko, persist localStorage. | WARM/admin-spa.mem.md D03 |
| Docker port | D05: 8081:80 — confirmed, tránh conflict với backend (8000), frontend-spa (8080), dev (3000). | WARM/admin-spa.mem.md D05 |
| Write gate | D04: `api_key` OR (`jwt` AND `is_admin`) cho POST/DELETE documents. | WARM/admin-spa.mem.md D04 |
| S000 migration number | 009 — tiếp theo sau 008_add_password_hash.sql (confirmed from migrations/ directory). | Migration files 001–008 |
| `/v1/metrics` NOT existing | Không tìm thấy trong backend/api/routes/ — phải implement trong S000. | Code scan |
| `user_group_memberships` NOT existing | Không có junction table — api_keys dùng `user_group_ids INTEGER[]`, users không có group field. | Migration 004 |

---

## Resolution Summary

**4 BLOCKERs — ALL RESOLVED ✅**
- **Q1**: Junction table `user_group_memberships` — migration 009 creates it. `verify_token` JOIN-based `is_admin` compute.
- **Q2**: `/v1/metrics` NOT implemented → add to S000 scope (api-agent).
- **Q3**: File upload (multipart) — dùng `POST /v1/documents/upload` (PDF/DOCX/HTML/TXT/MD). S002 AC4 phải update: file input thay vì textarea.
- **Q4**: `PUT /v1/admin/users/{id}` → S000 scope. Không tách story.

**Spec impact từ Q3 (cần update trước /plan):**
- S002 AC4: "Upload modal: chọn file (PDF/DOCX/HTML/TXT/MD) + Title (optional, default=filename stem) + Language (optional, auto-detect) + Group (optional)" — thay vì textarea content.
- S002 AC5: Gọi `POST /v1/documents/upload` (multipart/form-data) thay vì `POST /v1/documents` (JSON).
- S000 AC13: Write gate mở rộng cần áp dụng cho cả `POST /v1/documents/upload` (không chỉ `POST /v1/documents`).

**S000 scope mở rộng (từ Q1, Q2, Q4):**
- Migration 009: `is_admin` column + `user_group_memberships` junction table.
- `verify_token`: JOIN `users → user_group_memberships → user_groups` để compute `is_admin`.
- `GET /v1/metrics`: admin-only aggregate endpoint (mới).
- `PUT /v1/admin/users/{id}`: toggle `is_active` (mới).

**6 SHOULDs** auto-assume (Q5–Q10).
**4 NICEs** deferred to v2.
**10 auto-answered** from ARCH.md, HARD.md, WARM, and code scan.

**→ READY for /checklist then /plan.**

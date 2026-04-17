# Spec: frontend-spa
Created: 2026-04-16 | Author: lb_mui | Status: DRAFT

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | frontend |
| Priority | P1 |
| Story count | 6 |
| Token budget est. | ~6k |
| Critical path | S000 → S001 → S002 → S003 → S004 → S005 |
| Parallel-safe stories | S003, S004 (after S002) |
| Blocking specs | — |
| Blocked by | query-endpoint (DONE), answer-citation (DONE) |
| Agents needed | api-agent (S000), frontend-agent (S001–S005) |

### Problem Statement
End-users (employees) có không có giao diện để tương tác với hệ thống RAG.
Họ cần tìm kiếm tài liệu nội bộ bằng ngôn ngữ bất kỳ (ja/en/vi/ko) và nhận câu trả lời có trích dẫn nguồn.
Public SPA là thin client — toàn bộ business logic nằm ở backend `/v1/query`.

### Solution Summary
- React/Vite SPA — public-facing, external deploy (cloud/CDN)
- Một trang query duy nhất: nhập câu hỏi → xem AI answer + citations + confidence
- Đăng nhập bằng username/password (JWT, chưa cần SSO)
- UI language: user tự chọn (ja / en / vi / ko)
- Build artifact + Dockerfile — deploy độc lập với admin-spa

### Out of Scope
- Document upload / management (→ admin-spa, feature riêng)
- Admin user/group management (→ admin-spa)
- Conflict detection UI (→ sau khi conflict-detection feature done)
- OIDC/SSO (→ deferred)
- Real-time / websocket streaming answer
- Mobile native app

---

## LAYER 2 — Story Detail

---

### S000: Backend — Username/Password Auth Endpoint (prerequisite)

**Role / Want / Value**
- As a: api-agent
- I want: `POST /v1/auth/token` endpoint nhận username + password
- So that: frontend SPA có thể authenticate user và nhận JWT để gọi các endpoint khác

**Acceptance Criteria**
- [ ] AC1: `POST /v1/auth/token` nhận `{"username": "...", "password": "..."}`, trả về JWT access token
- [ ] AC2: `users` table có column `password_hash` (bcrypt) — migration file `NNN_add_password_hash.sql`
- [ ] AC3: Password verify bằng bcrypt (`passlib[bcrypt]`) — không plain text, không MD5/SHA1
- [ ] AC4: JWT issued bằng `AUTH_SECRET_KEY` env var (HS256), payload: `sub`, `user_id`, `exp`
- [ ] AC5: JWT expiry configurable qua `AUTH_TOKEN_EXPIRE_MINUTES` env var (default: 60)
- [ ] AC6: Sai username hoặc password → 401 `{"error": {"code": "AUTH_FAILED", "message": "Invalid credentials"}}` — không phân biệt lỗi nào sai (prevent username enumeration)
- [ ] AC7: Endpoint không yêu cầu auth (public route — ngoại lệ của R003)
- [ ] AC8: `POST /v1/auth/token` có rate limit riêng: 10 req/min per IP (brute force protection)
- [ ] AC9: `verify_token` dependency cập nhật để accept cả JWT từ endpoint này (HS256) lẫn OIDC JWT (RS256/ES256)

**API Contract**
```
POST /v1/auth/token
Headers: (none required)
Body: {"username": "string", "password": "string"}
Response 200: {
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
Response 401: {"error": {"code": "AUTH_FAILED", "message": "Invalid credentials", "request_id": "..."}}
Response 422: {"error": {"code": "VALIDATION_ERROR", "message": "..."}}
Response 429: {"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "..."}}
```

**Auth Requirement**
- [ ] Public endpoint (no auth required)

**Non-functional**
- Latency: < 500ms (bcrypt hash check ~100–200ms expected)
- Audit log: log failed attempts (user_id=null, event=AUTH_FAILED) — không log password
- Migration: numbered file required (C010)

**Implementation notes**
- File mới: `backend/api/routes/auth.py`
- Migration: `backend/db/migrations/NNN_add_password_hash.sql`
- `verify_token` trong `backend/auth/dependencies.py` cần handle cả HS256 (local JWT) và RS256/ES256 (OIDC)
- `AUTH_SECRET_KEY` phải ≥ 32 bytes random — add vào `.env.example`
- passlib: `from passlib.context import CryptContext; pwd_context = CryptContext(schemes=["bcrypt"])`

---

### S001: Authentication — Login / Logout

**Role / Want / Value**
- As a: employee (end-user)
- I want: đăng nhập bằng username + password
- So that: tôi có thể truy cập query page và hệ thống biết tôi là ai (RBAC)

**Acceptance Criteria**
- [ ] AC1: Login form có 2 field: username, password + nút Submit
- [ ] AC2: Submit gọi `POST /v1/auth/token` (hoặc endpoint auth hiện có), nhận JWT access token
- [ ] AC3: JWT lưu trong memory (không lưu localStorage/sessionStorage để tránh XSS)
- [ ] AC4: Request tiếp theo tự động gắn `Authorization: Bearer <token>` header
- [ ] AC5: Token hết hạn → redirect về login page, hiển thị thông báo "Session expired"
- [ ] AC6: Logout xóa token khỏi memory, redirect về login page
- [ ] AC7: Khi chưa login, truy cập `/` redirect sang `/login`
- [ ] AC8: Login error (401) hiển thị message rõ ràng, không expose detail lỗi backend

**API Contract**
```
POST /v1/auth/token
Body: {"username": "...", "password": "..."}
Response 200: {"access_token": "...", "token_type": "bearer", "expires_in": 3600}
Response 401: {"error": {"code": "AUTH_FAILED", "message": "Invalid credentials"}}
```

**Auth Requirement**
- [x] JWT Bearer (username/password flow)

**Non-functional**
- Latency: < 500ms login response
- Audit log: not required (auth layer handles)
- CJK support: not applicable

**Implementation notes**
- Token stored in React context / Zustand store (in-memory only)
- Axios interceptor tự động attach Bearer header
- 401 response interceptor → trigger logout + redirect

---

### S002: Query Page — Search Input & Language Selector

**Role / Want / Value**
- As a: employee
- I want: nhập câu hỏi bằng ngôn ngữ bất kỳ và chọn UI language
- So that: tôi tìm kiếm thoải mái bằng tiếng mẹ đẻ

**Acceptance Criteria**
- [ ] AC1: Search input box — placeholder text theo UI language đang chọn
- [ ] AC2: Language selector dropdown: 4 options — 日本語 / English / Tiếng Việt / 한국어
- [ ] AC3: Thay đổi UI language → toàn bộ label/placeholder/button text đổi ngay (i18n)
- [ ] AC4: UI language preference lưu vào localStorage (persist qua refresh)
- [ ] AC5: Submit query bằng Enter hoặc click Search button
- [ ] AC6: Query không được rỗng — disable Submit khi input trống
- [ ] AC7: Query tối đa 512 ký tự — hiển thị character counter, block submit khi vượt
- [ ] AC8: Trong khi đang chờ response — hiển thị loading spinner, disable input + button

**Auth Requirement**
- [x] JWT Bearer (human user)

**Non-functional**
- Latency: UI interaction < 100ms (local state)
- i18n: ja / en / vi / ko
- CJK input: hỗ trợ IME input (Japanese/Korean/Chinese composition)

**Implementation notes**
- i18n library: react-i18next
- Translation files: `src/i18n/locales/{ja,en,vi,ko}.json`
- Language detect order: localStorage → browser navigator.language → fallback "en"

---

### S003: Query Results — Answer + Citations Display

**Role / Want / Value**
- As a: employee
- I want: xem câu trả lời AI kèm nguồn trích dẫn và confidence score
- So that: tôi biết thông tin đến từ đâu và độ tin cậy

**Acceptance Criteria**
- [ ] AC1: Answer text hiển thị rõ ràng, hỗ trợ markdown rendering
- [ ] AC2: Mỗi citation hiển thị: doc title, page/section (nếu có), relevance score
- [ ] AC3: Confidence score hiển thị dưới dạng badge: HIGH (≥0.7) / MEDIUM (0.4–0.69) / LOW (<0.4)
- [ ] AC4: Confidence LOW → hiển thị warning banner: "Low confidence — please verify with source"
- [ ] AC5: Citations có thể expand/collapse (default: collapsed nếu >3 citations)
- [ ] AC6: Không có kết quả phù hợp → hiển thị "No relevant documents found" (không hiện empty answer)
- [ ] AC7: API error → hiển thị error message theo error.code, không crash page
- [ ] AC8: Answer + citations cleared khi user submit query mới

**API Contract**
```
POST /v1/query
Headers: Authorization: Bearer <token>
Body: {"query": "...", "lang": "auto"}
Response 200: {
  "answer": "...",
  "confidence": 0.85,
  "citations": [
    {"doc_id": "...", "title": "...", "chunk": "...", "score": 0.91}
  ],
  "query_id": "..."
}
Response 401: {"error": {"code": "AUTH_REQUIRED", ...}}
Response 429: {"error": {"code": "RATE_LIMIT_EXCEEDED", ...}}
```

**Auth Requirement**
- [x] JWT Bearer (human user)

**Non-functional**
- Latency: render < 100ms sau khi nhận response
- Markdown: react-markdown hoặc tương đương
- CJK support: ja / vi / ko / zh — font hỗ trợ đầy đủ

**Implementation notes**
- Confidence badge color: green/yellow/red theo mức
- Citation score format: "91%" hoặc "0.91" — chọn 1 nhất quán
- lang field gửi lên: "auto" (backend tự detect)

---

### S004: Query History — Session-level

**Role / Want / Value**
- As a: employee
- I want: xem lại các câu hỏi đã hỏi trong session hiện tại
- So that: tôi có thể click lại query cũ mà không cần gõ lại

**Acceptance Criteria**
- [ ] AC1: Sidebar hoặc panel hiển thị danh sách query trong session (tối đa 20 mục)
- [ ] AC2: Click vào query cũ → restore answer + citations vào main panel
- [ ] AC3: History chỉ tồn tại trong session (in-memory) — không persist qua logout/refresh
- [ ] AC4: History cleared khi logout
- [ ] AC5: Mỗi history item hiển thị: query text (truncated 60 chars) + timestamp

**Auth Requirement**
- [x] JWT Bearer (human user)

**Non-functional**
- Storage: in-memory React state only (không gọi API)
- CJK support: truncation phải handle CJK chars đúng (không cắt giữa character)

**Implementation notes**
- State: Zustand store `queryHistory[]`
- CJK truncation: dùng `Intl.Segmenter` hoặc spread `[...str]` thay `.slice()`

---

### S005: Build & Docker Packaging

**Role / Want / Value**
- As a: DevOps / developer
- I want: build static artifact và Docker image cho public SPA
- So that: deploy lên cloud/CDN độc lập với admin-spa

**Acceptance Criteria**
- [ ] AC1: `npm run build` tạo `dist/` — static files sẵn sàng serve
- [ ] AC2: Dockerfile multi-stage: `node:20-alpine` build → `nginx:alpine` serve
- [ ] AC3: Nginx config serve `index.html` cho mọi route (SPA fallback)
- [ ] AC4: API base URL cấu hình qua env var `VITE_API_BASE_URL` (không hardcode)
- [ ] AC5: Build thành công với `npm run build` không có error/warning về missing env
- [ ] AC6: Docker image chạy được với `docker run -p 3000:80 -e VITE_API_BASE_URL=http://... frontend-spa`
- [ ] AC7: `.env.example` có đầy đủ các env vars cần thiết

**Non-functional**
- Docker image size < 50MB (nginx:alpine base)
- Build time < 60s

**Implementation notes**
- Vite env vars phải prefix `VITE_` để expose ra browser bundle
- nginx.conf: `try_files $uri $uri/ /index.html;`
- Multi-stage build tránh include node_modules vào final image

---

## LAYER 3 — Sources Traceability

### S000 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Conversation | lb_mui 2026-04-16 — "chưa có endpoint thôi" | 2026-04-16 |
| AC2–AC3 | Business logic | Password storage best practice — bcrypt via passlib | 2026-04-16 |
| AC4–AC5 | Business logic | JWT HS256 for internal issuer — AUTH_SECRET_KEY env var | 2026-04-16 |
| AC6 | Business logic | OWASP: prevent username enumeration via consistent error message | 2026-04-16 |
| AC7 | Existing behavior | HARD.md R003 — /v1/health exception pattern applied to /v1/auth/token | 2026-04-16 |
| AC8 | Business logic | Brute force protection — login endpoints must be rate limited | 2026-04-16 |
| AC9 | Existing behavior | backend/auth/oidc.py — verify_oidc_token already handles RS256/ES256 | 2026-04-16 |

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC8 | Business logic | Login flow standard cho internal tool, JWT in-memory pattern | 2026-04-16 |
| AC3 | Security | OWASP: avoid localStorage for JWT to prevent XSS | 2026-04-16 |
| AC8 | Conversation | lb_mui: Q2 — "đăng nhập bình thường, chưa cần SSO" | 2026-04-16 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC5 | Conversation | lb_mui: Q3 — "(b) user tự chọn UI language" | 2026-04-16 |
| AC7 | Existing behavior | SECURITY.md S003: query limit 512 tokens | 2026-04-16 |
| AC3 | Requirement | CONSTITUTION.md P003: multilingual by design — ja/en/vi/ko equal | 2026-04-16 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC8 | Existing behavior | answer-citation feature: citation + confidence score already in /v1/query response | 2026-04-16 |
| AC3–AC4 | Existing behavior | confidence-scoring feature: HIGH/MEDIUM/LOW thresholds, <0.4 warning | 2026-04-16 |
| AC4 | Requirement | CONSTITUTION.md C014: confidence < 0.4 triggers low-confidence warning | 2026-04-16 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC5 | Business logic | UX pattern: session history for search tools — reduce retyping friction | 2026-04-16 |
| AC3 | Conversation | lb_mui: Q5 — không cần persist, session only | 2026-04-16 |

### S005 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC7 | Conversation | lb_mui: Q5 — "(c) cả hai: build artifact + Dockerfile" | 2026-04-16 |
| AC2 | Business logic | 2 app riêng: public-spa external, admin-spa internal — independent deploy | 2026-04-16 |
| AC4 | Requirement | CONSTITUTION.md: zero hardcoded secrets/config | 2026-04-16 |

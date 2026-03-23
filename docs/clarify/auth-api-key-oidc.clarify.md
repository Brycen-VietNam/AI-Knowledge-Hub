# Clarify: auth-api-key-oidc
Generated: 2026-03-23 | Spec: docs/specs/auth-api-key-oidc.spec.md | Status: DRAFT

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | S003: Nếu OIDC token hợp lệ nhưng `groups` claim **không tồn tại** hoặc **rỗng**, `verify_oidc_token` có cho phép login không? Hay trả về 403? | **Permissive**: `user_group_ids=[]` → login OK, RBAC trả empty. Không 403 tại auth layer. | ✅ resolved | 2026-03-23 |
| Q2 | S003: `users.email` và `users.display_name` có được lấy từ JWT claims không? Tên claims? | **Configurable via env var**: `OIDC_EMAIL_CLAIM` (default `"email"`) và `OIDC_NAME_CLAIM` (default `"name"`). Không hardcode claim names. | ✅ resolved | 2026-03-23 |
| Q3 | S001: `audit_logs` hiện tại có rows thực nào không? → Ảnh hưởng chiến lược migrate | **Trống hoàn toàn** — dev environment. Migration đơn giản: INSERT sentinel → ALTER COLUMN → ADD FK. Không cần UPDATE existing rows. | ✅ resolved | 2026-03-23 |
| Q4 | S002: API key được tạo ra ở đâu trong sprint này? | **Manual seed** — dev/IT admin tạo key thủ công bằng SQL (SHA-256 hash → INSERT). Admin endpoint làm sprint sau. Scope giữ nhỏ. | ✅ resolved | 2026-03-23 |

---

## SHOULD — Assume nếu không trả lời trước sprint start

| # | Question | Default assumption | Story |
|---|----------|--------------------|-------|
| Q5 | S003: Nếu `user_groups.name` trong DB không match bất kỳ tên nào trong JWT `groups` claim, user có `user_group_ids = []` (empty) hay 403? | **Assumption**: `user_group_ids = []` — user vẫn login được, nhưng không access được tài liệu nào (RBAC WHERE filter trả empty). Không throw 403 tại auth layer. | S003 |
| Q6 | S003: Token type hỗ trợ: RS256 only, hay cả ES256? | **Assumption**: Cả RS256 và ES256 đều được accept (PyJWT hỗ trợ cả hai; `algorithms=["RS256", "ES256"]`) | S003 |
| Q7 | S002: API key encoding: raw random string (URL-safe base64), hay có format prefix như `kb_live_<random>`? | **Assumption**: URL-safe base64 random (32 bytes → 43 chars), không có prefix. Format prefix có thể thêm sau khi có admin endpoint. | S002 |
| Q8 | S001: `users.email` và `users.display_name` — có thể NULL không? (Một số OIDC providers không include email claim) | **Assumption**: Cả hai đều NULLABLE — không phải NOT NULL constraint. `sub` là unique identifier bắt buộc. | S001 |
| Q9 | S004: `AUTH_FORBIDDEN` (403) được dùng trong trường hợp nào cụ thể? Spec khai báo error code nhưng chưa có story nào trigger 403. | **Assumption**: 403 reserved cho future use (vd: suspended account `is_active=FALSE` ở user level, khác với API key `is_active=FALSE` → 401). Hiện tại chưa implement trong sprint này. | S004 |

---

## NICE — Không block /plan

| # | Question | Story |
|---|----------|-------|
| Q10 | S003: Có muốn log OIDC login event riêng (first login vs. return login) không? Hiện tại JIT chỉ UPSERT silently. | S003 |
| Q11 | S002/S003: `request_id` trong error response — có muốn dùng middleware để inject vào `request.state` trước khi đến auth layer không? Hay để mỗi function tự generate `uuid4()`? | S002, S003, S004 |
| Q12 | S001: `api_keys.description` có ràng buộc length không (vd: max 255 chars)? | S001 |
| Q13 | S003: JWKS fetch failure (network error, timeout) — có fallback hay trả về 503 ngay? | S003 |

---

## Auto-answered từ CONSTITUTION.md và existing files

| # | Question | Answer | Source |
|---|----------|--------|--------|
| A1 | Error response shape cho tất cả auth errors? | `{"error": {"code": "...", "message": "...", "request_id": "..."}}` | ARCH.md A005 ✅ auto |
| A2 | /v1/health có cần auth không? | Không — sole exception theo C003 | CONSTITUTION.md C003 ✅ auto |
| A3 | Secrets có thể hardcode không? | Không bao giờ — tất cả qua env vars | CONSTITUTION.md Non-Negotiables + S005 ✅ auto |
| A4 | JWT validation cần check gì? | Signature + expiry + issuer + audience (4 checks bắt buộc) | SECURITY.md S002 ✅ auto |
| A5 | JWKS public keys cache strategy? | Cache với TTL, không cache forever | SECURITY.md S002 ✅ auto |
| A6 | SQL queries phải dùng gì? | Parameterized queries only — zero string interpolation | CONSTITUTION.md Non-Negotiables + S001 ✅ auto |
| A7 | Auth module được import bởi ai? | api-agent chỉ, via `from backend.auth import verify_token, AuthenticatedUser` | ARCH.md A001, A002 ✅ auto |
| A8 | Migration rollback bắt buộc không? | Có — mỗi migration PHẢI có rollback section | ARCH.md A006 + C010 ✅ auto |
| A9 | Test coverage yêu cầu? | ≥ 80% cho new code; integration tests cho critical user journeys | CONSTITUTION.md Team Conventions ✅ auto |
| A10 | ORM update timing? | Sau khi migration file được tạo và reviewed — không trước | CONSTITUTION.md C010 ✅ auto |
| A11 | Groups claim = names hay IDs? | Names (strings) → DB lookup (D01) | Q&A 2026-03-23 ✅ resolved |
| A12 | User provisioning strategy? | JIT UPSERT khi OIDC login lần đầu (D02) | Q&A 2026-03-23 ✅ resolved |
| A13 | JWT library? | PyJWT >= 2.8 + cryptography extra (D03) | Q&A 2026-03-23 ✅ resolved |
| A14 | Migration sentinel value? | `sub='__migration_placeholder__'` (D04) | Q&A 2026-03-23 ✅ resolved |
| A15 | Header precedence khi cả hai present? | X-API-Key takes precedence (D05) | Q&A 2026-03-23 ✅ resolved |

---

## Summary

**BLOCKER**: 4 câu hỏi — ✅ TẤT CẢ ĐÃ RESOLVED
**SHOULD**: 5 câu hỏi — có default assumption, không block /plan nếu không trả lời
**NICE**: 4 câu hỏi — không ảnh hưởng implementation sprint này
**Auto-answered**: 15 câu hỏi từ CONSTITUTION.md, ARCH.md, SECURITY.md và Q&A /specify

---

## Blockers Detail

### Q1 — Empty groups claim behavior (BLOCKER)
**Vấn đề**: Spec S003 AC1 chỉ nói "Groups claim (list of strings) → DB lookup" nhưng không define behavior khi `groups` claim absent hoặc empty array.

**Hai lựa chọn**:
- **Option A** (permissive): Login thành công với `user_group_ids = []`. User không access được tài liệu nào (RBAC filter trả empty set) nhưng không bị block ở auth layer. Phù hợp nếu có tài liệu public hoặc user có thể xem metadata.
- **Option B** (strict): Nếu `groups` claim absent hoặc empty → 403 `AUTH_FORBIDDEN`. Không cho phép login không có group membership.

**Ảnh hưởng**: Option B cần thêm AC vào S003, thay đổi error code cho S004.

---

### Q2 — JWT claim mapping cho users table (BLOCKER)
**Vấn đề**: S001 AC1 định nghĩa `users(sub, email, display_name)` và S003 AC1 nói "JIT UPSERT vào users table theo sub claim" nhưng không chỉ rõ claim nào map sang `email` và `display_name`.

**Keycloak standard claims**:
- `email` → thường là `email` claim
- `display_name` → có thể là `name`, `preferred_username`, hoặc `given_name + family_name`

**Cần confirm**: Keycloak realm config để biết chính xác claim names.

---

### Q3 — audit_logs migration safety (BLOCKER)
**Vấn đề**: Migration 004 ALTER `audit_logs.user_id` TEXT → UUID FK. Nếu có rows thực trong `audit_logs`, cần:
1. INSERT sentinel user
2. UPDATE existing rows: `UPDATE audit_logs SET user_id = <sentinel_uuid>`
3. ALTER COLUMN type (TEXT → UUID requires CAST)
4. ADD FK constraint

Nếu `audit_logs` hoàn toàn trống (dev only), migration đơn giản hơn nhiều.

---

### Q4 — API key creation endpoint (BLOCKER)
**Vấn đề**: S002 implement validation nhưng không rõ luồng tạo API key. Nếu không có endpoint tạo key:
- Tests không thể seed realistic data
- Bots không thể lấy key
- `api_keys.user_id` FK cần có `users` record trước

**Hai lựa chọn**:
- **Option A**: Tạm thời manual seed trong dev (SQL INSERT) — bots nhận key qua IT admin. Admin endpoint trong sprint sau.
- **Option B**: Thêm internal `POST /v1/admin/api-keys` endpoint vào sprint này (tăng scope).

---

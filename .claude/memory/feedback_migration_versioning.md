---
name: Migration versioning — add Alembic
description: User wants to add Alembic for proper DB migration version tracking; current setup has no version tracking
type: feedback
---

Current migrations dùng `docker-entrypoint-initdb.d` — chỉ chạy một lần khi volume chưa tồn tại. Không có bảng version tracking, không có Flyway/Alembic.

User muốn setup **Alembic** để có proper version tracking.

**Why:** Khi volume đã tồn tại, migrations mới (vd. 006) không tự chạy — phải chạy thủ công hoặc `down -v`. Rủi ro cao khi deploy lên môi trường staging/prod.

**How to apply:** Khi được yêu cầu, setup Alembic với `alembic init`, kết nối `DATABASE_URL` từ env, migrate các file SQL hiện tại thành Alembic versions. Giữ backward compat với volume cũ bằng `alembic stamp head`.

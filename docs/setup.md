# Knowledge-Hub — Setup Guide

## Prerequisites
- Docker Desktop
- Git

---

## 1. Clone & cấu hình

```bash
git clone <repo> && cd knowledge-hub

# Copy và điền giá trị vào .env
cp .env.example .env
```

Các biến bắt buộc trong `.env`:

```env
POSTGRES_USER=kh_user
POSTGRES_PASSWORD=<your-password>

# OIDC (bắt buộc để app khởi động — dùng placeholder nếu chưa có SSO)
OIDC_ISSUER=https://placeholder.example.com
OIDC_AUDIENCE=knowledge-hub
OIDC_JWKS_URI=https://placeholder.example.com/.well-known/jwks.json
```

---

## 2. Build & Start

```bash
# Start toàn bộ services (postgres, valkey, ollama, app)
docker compose up -d --build
```

---

## 3. Pull Embedding Model (1 lần duy nhất, ~500MB)

```bash
docker exec knowledge-hub-ollama ollama pull mxbai-embed-large
```

> Model được lưu trong Docker volume `ollama_data` — không cần pull lại sau khi đã có.

---

## 4. Restart app sau khi model sẵn sàng

```bash
docker compose restart app
```

---

## 5. Tạo dev API key (1 lần duy nhất)

```bash
docker exec knowledge-hub-postgres psql -U kh_user -d knowledge_hub -c "
WITH new_user AS (
  INSERT INTO users (sub, email, display_name, is_active)
  VALUES ('dev-local', 'dev@example.com', 'Dev User', true)
  RETURNING id
)
INSERT INTO api_keys (user_id, key_hash, user_group_ids)
SELECT id, encode(sha256('test-api-key-dev'::bytea), 'hex'), '{}'
FROM new_user;"
```

**API key:** `test-api-key-dev`

---

## 6. Kiểm tra

```bash
# App healthy
curl http://localhost:8000/v1/documents -H "X-API-Key: test-api-key-dev"

# Upload document
curl -X POST http://localhost:8000/v1/documents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-dev" \
  -d '{"title":"Test","content":"Hello world","lang":"en","user_group_id":null}'

# Query
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-dev" \
  -d '{"query":"Hello world"}'
```

---

## Notes

- **Migrations:** Chạy tự động khi volume postgres chưa tồn tại. Nếu volume cũ, chạy thủ công: `docker exec -i knowledge-hub-postgres psql -U kh_user -d knowledge_hub < backend/db/migrations/<file>.sql`
- **LLM model:** Chưa setup — query trả `sources` trực tiếp, `answer: null`. Để enable: pull model + set `LLM_MODEL` trong `.env`.
- **Volume wipe:** Nếu cần reset DB sạch: `docker compose down -v && docker compose up -d --build` (mất toàn bộ data)
- **Ollama CPU-only:** Máy không có discrete GPU — embedding/inference chạy trên CPU, hơi chậm nhưng hoạt động bình thường.

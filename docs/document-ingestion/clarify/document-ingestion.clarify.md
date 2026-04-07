# Clarify: document-ingestion
Generated: 2026-04-06 | Spec: v1 DRAFT | Stories: S001–S005

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | `bm25_indexer.py` không tồn tại trong `backend/rag/`. WARM mem nói "EXTEND (exists from cjk-tokenizer)" nhưng file không có. BM25 indexer cần được tạo mới trong document-ingestion, hay đây là file sót cần được tạo từ cjk-tokenizer? | ❓ | lb_mui | trước /plan |
| Q2 | S001 AC5: "caller must have `write` permission on target `user_group_id`". `AuthenticatedUser` chỉ có `user_group_ids: list[int]` — không có permission level. RBAC hiện tại chỉ kiểm tra group membership, không có write/read permission. Implement write check như thế nào? (a) bất kỳ member của group đều có write; (b) cần thêm permission field vào `AuthenticatedUser`; (c) chỉ admin (superuser) mới write? | ❓ | lb_mui | trước /plan |
| Q3 | S003: embedding model `multilingual-e5-large` được load ở đâu? Hiện `backend/rag/` không có `embedder.py`. Load via Ollama (đã có llm-provider)? Hay via `sentence-transformers` trực tiếp? Cần xác định interface trước khi implement S003. | ❓ | lb_mui | trước /plan |

---

## SHOULD — Assume nếu chưa trả lời trước sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q4 | `title` có max length không? | Max 500 ký tự — nếu vượt → 422. Align với DB `VARCHAR` default. |
| Q5 | Khi document có `user_group_id=null` (public), ai có thể DELETE nó? Chỉ admin, hay mọi authenticated user? | Chỉ user thuộc `user_group_id IS NULL` hoặc superuser. Nếu không thể xác định → 403. |
| Q6 | Background task failure (embedding/BM25) có cần notify caller không? | Không — caller đã nhận 202. Status `failed` visible qua GET /v1/documents/{id}. Không có webhook/push. |
| Q7 | GET /v1/documents list — default sort order? | `created_at DESC` (mới nhất trước). |
| Q8 | GET /v1/documents — `limit` max bao nhiêu? | Max 100 per page. Vượt → 422. |

---

## NICE — Không block

| # | Question |
|---|----------|
| Q9 | Có cần trả về estimated completion time trong 202 response không? |
| Q10 | Có cần endpoint GET /v1/documents/{id}/status riêng để poll progress không, hay GET /v1/documents/{id} là đủ? |
| Q11 | Khi DELETE document đang `status=processing`, có cancel background task không? |

---

## Auto-answered từ existing files

| Q | Source | Answer |
|---|--------|--------|
| Rate limit 20 req/min | CONSTITUTION C013 | Enforced per caller (user_id/API-key). |
| Error shape | CONSTITUTION A005 / ARCH.md A005 | `{"error": {"code": "...", "message": "...", "request_id": "..."}}` — already in query.py. |
| Embedding dims = 1024 | `backend/db/models/embedding.py` — `Vector(1024)` | multilingual-e5-large 1024-dim confirmed. |
| Cascade delete embeddings | `backend/db/models/embedding.py` — `ondelete="CASCADE"` | Already in schema. No migration needed for this. |
| Tokenizer interface | `backend/rag/tokenizers/factory.py` — `TokenizerFactory.get(lang)` | S004 gọi `TokenizerFactory.get(lang).tokenize(text)`. |
| Tokenizer fallback for unknown lang | `TokenizerFactory._create()` — raises `UnsupportedLanguageError` | S004 AC3: catch `UnsupportedLanguageError` → fallback to `simple` pg config + log warning. |
| Auth dependency | `backend/auth/dependencies.py` — `verify_token` | S001, S005 dùng `Depends(verify_token)` → `AuthenticatedUser`. |
| user_group_id IS NULL = public | `backend/db/migrations/005_nullable_user_group_id.sql` — D01 | Confirmed. RBAC filter: `WHERE user_group_id = ANY(:group_ids) OR user_group_id IS NULL`. |
| BM25 query pattern | `backend/rag/retriever.py` `_bm25_search()` | Dùng `to_tsquery('simple', :query)` + `content_fts @@` — S004 update phải match format này. |
| lang auto-detect | `backend/rag/tokenizers/detection.py` — `detect_language()` | S002 AC2: gọi `detect_language(content)` nếu lang không cung cấp. |

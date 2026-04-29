# Clarify: embed-model-migration
Generated: 2026-04-27 | Updated: 2026-04-27 (all blockers resolved) | Spec: v1 DRAFT | Stories: 5 | ACs: 30

---

## ~~BLOCKER~~ — RESOLVED ✅

| # | Question | Answer | Source | Date |
|---|----------|--------|--------|------|
| Q1 | **S005/AC1,7:** Ai curate 120-query fixture set + golden `expected_doc_ids`? | ✅ **Claude tự generate synthetic fixtures** dựa trên test docs được ingest trong S002. Mỗi fixture query được derive từ nội dung 1 đoạn trong doc → `expected_doc_ids` traceable tự động. lb_mui review pass/fail cuối S005. | Quyết định session 2026-04-27 | 2026-04-27 |
| Q2 | **S004/AC3,5:** HF GGUF repo tồn tại sẵn không? | ✅ **Không.** `intfloat/multilingual-e5-large-gguf` không tồn tại. Repo chính chỉ có `.safetensors`. → **Phải tự convert qua llama.cpp** (XLMRoberta GGUF supported từ Aug 2024). Community repo `soichisumi/multilingual-e5-large-Q8_0-GGUF` tồn tại nhưng không dùng (license + SLA risk). S004 ops doc hướng dẫn llama.cpp convert path. | Web verify 2026-04-27 | 2026-04-27 |
| Q3 | **S005/AC4,5:** Đo baseline mxbai hay bỏ qua? | ✅ **Bỏ qua baseline mxbai.** Fixture set mới hoàn toàn (synthetic từ test docs) → không có apples-to-apples với data cũ. Thay delta +15%, dùng **absolute threshold: E5 recall@10 ≥ 0.6** làm pass bar. Lý do: 0.6 recall@10 là mức "production-viable" theo IR literature với top_k=10. | Quyết định session 2026-04-27 | 2026-04-27 |

---

## SHOULD — Assume nếu chưa trả lời trước sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q4 | **S001/AC6:** Prefix `"query: "` (7 chars) + `"passage: "` (9 chars) có làm truncation limit thực tế còn 1391/1393 chars. Có cần nới `OLLAMA_MAX_EMBED_CHARS` lên 1450? | **Giữ 1400 default.** Prefix ngắn, không đáng kể. Nới nếu test thực tế cho thấy 500-error. |
| Q5 | **S003/AC4:** Smoke test cross-lingual dùng doc gì? Doc "search guide" tiếng Anh phải thực sự tồn tại trong test ingest set. | **Assume:** S002 ingest ≥4 fixture docs (JA/EN/VI/KO) trước S003. Doc EN về "search" là 1 trong 4 fixture docs đó. |
| Q6 | **S004/AC1:** `truncate_and_reset.py` dùng async SQLAlchemy (asyncpg) hay sync (psycopg2)? Script chạy standalone, không qua FastAPI app context. | **Assume sync** (psycopg2 direct) để tránh event loop boilerplate trong CLI script. Import `DATABASE_URL` từ env. |
| Q7 | **S005/AC1:** Category `multi-intent` trong fixture có bắt buộc không, hay chỉ `mono` + `cross-lingual`? Plan mention cross-lingual là ưu tiên. | **Assume:** `multi-intent` là optional enrichment. Bắt buộc: `mono` + `cross-lingual`. Nếu thời gian cho phép mới thêm `multi-intent`. |
| Q8 | **S004/AC4:** Checksum của GGUF distributed — dùng SHA256 hay MD5? | **SHA256** — industry standard, đủ cho internal integrity check. |

---

## NICE — Không block

| # | Question |
|---|----------|
| Q9 | S005 eval harness có cần tích hợp vào CI (pytest) hay chỉ run manually? |
| Q10 | Ops doc S004 có cần hướng dẫn EC2 Security Group (port 11434 internal-only) hay để infra team tự handle? |
| Q11 | Sau khi E5 stable, có muốn bỏ Ollama `/api/embeddings` và dùng thẳng `sentence-transformers` Python library (loại bỏ Ollama dependency) không? |

---

## Auto-answered từ existing files

| Q | Source | Answer |
|---|--------|--------|
| Hybrid weights (S003/AC2) | `ARCH.md` A004 | `RAG_DENSE_WEIGHT=0.7`, `RAG_BM25_WEIGHT=0.3` — env-configurable, không hardcode. ✅ |
| HNSW params (S003/AC3) | `backend/db/migrations/002_add_pgvector_hnsw.sql:23-26` | `m=16, ef_construction=64, vector_cosine_ops` — không đổi. ✅ |
| Batch size minimum (S001/AC4) | `PERF.md` P002 | `batch_size=32` minimum — asyncio.gather pattern. ✅ |
| SQL injection prevention (S004/AC1) | `SECURITY.md` S001 | `text()` + named params. No f-string SQL. ✅ |
| No PII in embedding metadata (S002/AC4) | `HARD.md` R002 | `user_group_id` from doc only; no email/name in metadata. ✅ |
| Latency SLA (S003/AC5) | `HARD.md` R007 + `PERF.md` P001 | p95 < 2000ms end-to-end. Embed budget ~400ms. ✅ |
| License free/OSS (S004/AC4) | `docs/backlog.md:7-11` (Decision 2026-03-18) | MIT model, self-hosted Ollama = free. ✅ |
| Dependency direction (S001–S003) | `ARCH.md` A002 | `api → rag → db` — không reverse. `OllamaEmbedder` ở `backend/rag/`, caller ở `backend/api/`. ✅ |

---

## Summary

**Blockers:** ~~3~~ → **0** ✅ (Q1/Q2/Q3 resolved 2026-04-27)
**SHOULD assumptions:** 5 (Q4–Q8) — safe to proceed.
**Auto-answered:** 8 — không cần PO input.
**NICE:** 3 — bỏ qua trong sprint này.

> **Ready for /checklist → /plan.** Không còn blocker nào.

### Quyết định chốt từ resolved blockers

| ID | Quyết định |
|----|------------|
| D07 | Fixture generation: Claude synthetic từ test docs; lb_mui review kết quả |
| D08 | GGUF path: llama.cpp convert từ `intfloat/multilingual-e5-large` safetensors (Q4_K_M) |
| D09 | Pass bar S005: absolute recall@10 ≥ 0.6 (thay delta +15% so mxbai) |

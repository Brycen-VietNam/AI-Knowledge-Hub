# Feature Backlog — Knowledge-Hub
> Generated: 2026-03-17 | Updated: 2026-04-27
> Source: /specify session + CONSTITUTION.md v1.2 + license review

---

## Quyết định license (2026-03-18)
- Toàn bộ stack free/OSS, ngoại trừ LLM provider (cho phép cả free và paid)
- Korean tokenizer: **kiwipiepy** (MIT) thay KoNLPy (tránh Java dependency)
- Rate limiting: **Valkey** (BSD-3) thay Redis ≥7.4
- LLM: Multi-provider architecture — Ollama/Llama (free) + OpenAI/Claude (paid) qua adapter pattern

---

## P0 — Nền tảng bắt buộc

| # | Feature | Epic | Mô tả |
|---|---------|------|-------|
| 1 | `db-schema-embeddings` | db | PostgreSQL schema + pgvector HNSW index + migrations |
| 2 | `auth-api-key-oidc` | auth | API-key + OIDC/SSO Bearer authentication middleware |
| 3 | `rbac-document-filter` | auth | RBAC hard-filter tại pgvector WHERE clause (C001) |
| 4 | `cjk-tokenizer` | rag | MeCab (ja), kiwipiepy (ko), jieba (zh), underthesea (vi) |
| 5 | `document-ingestion` | api | POST /v1/documents — upload, batch embed, index |
| 6 | `multilingual-rag-pipeline` | rag | Hybrid search: dense embeddings + BM25, auto lang detect |
| 7 | `llm-provider` | rag | Multi-provider LLM adapter: Ollama/Llama (free) + OpenAI/Claude (paid) |
| 8 | `query-endpoint` | api | POST /v1/query với audit log, latency SLA <2000ms |
| 29 | `embed-model-migration` | rag | **IN PROGRESS (SPECCING 2026-04-27)** — Chuyển dense embedder `mxbai-embed-large` (English-centric) → `intfloat/multilingual-e5-large` (MIT, self-build từ HF, q4_k_m quantized). Schema 1024-dim giữ nguyên (HNSW cosine). Truncate test data + re-ingest (Strategy A). Bổ sung E5 prefix `query: ` / `passage: `. Eval set 120 query (30 × JA/EN/VI/KO, ≥25% cross-lingual) đo recall@10 ≥ baseline +15%. Demo AWS `t3.medium` (~$30/tháng). Spec: `docs/embed-model-migration/spec/`. |

## P1 — Core MVP

| # | Feature | Epic | Mô tả |
|---|---------|------|-------|
| 9 | `document-parser` | api | PDF/DOCX/HTML → text extraction trước khi chunk + embed |
| 10 | `answer-citation` | rag | AI answer cite ≥1 source; confidence < 0.4 → warning (C014) |
| 11 | `conflict-detection` | rag | Phát hiện tài liệu mâu thuẫn nhau |
| 12 | `frontend-spa` | frontend | React/Vite SPA — search UI, multilingual |

## P2 — Mở rộng sau MVP

| # | Feature | Epic | Mô tả |
|---|---------|------|-------|
| 13 | `teams-bot-adapter` | bots | Microsoft Teams bot → /v1/query |
| 14 | `slack-bot-query-handler` | bots | Slack bot → /v1/query |
| 15 | `rate-limiting` | api | Valkey sliding window — 60/min query, 20/min docs (C013) |
| 16 | `metrics-endpoint` | api | GET /v1/metrics — latency, throughput, error rates |
| 12 | `change-password` | frontend | React/Vite SPA — Change password, require on first login |
| 17 | `file-storage` | api | Lưu file gốc sau khi ingest — pluggable backend: local disk hoặc S3-compatible (MinIO/AWS S3) qua env `FILE_STORAGE_BACKEND=local\|s3`. GET /v1/documents/{id}/download trả presigned URL (S3) hoặc stream (local). Embedding là one-way — không thể recover file từ vector. |
| 18 | `confidence-retrieval-score` | rag | Thay cited_ratio bằng retrieval-score-based confidence: dùng score của top docs từ pgvector thay vì đếm [N] trong LLM answer. Lý do: model free (gpt-oss-120b, qwen) không follow citation instruction đủ tốt → cited_ratio thường = 1/9 → LOW dù retrieval tốt. Approach: `confidence = weighted_avg(top_k_scores)` hoặc `score[0] * 0.6 + mean(scores) * 0.4`. Giữ top_k không đổi, chỉ thay nguồn tính confidence trong `query.py`. |
| 19 | `multi-chunk-per-doc` | rag | Retriever hiện dedup theo doc_id → nhiều chunks khớp từ cùng 1 doc bị collapse thành 1 chunk (mất context). Fix: dedup theo `(doc_id, chunk_index)`, giới hạn max 2 chunks/doc. Score vẫn cộng dồn (boost doc có nhiều chunks khớp). Config qua env `RAG_MAX_CHUNKS_PER_DOC=2`. Với top_k=10: worst case 5 docs × 2 chunks — đủ đa dạng nguồn cho LLM. |
| 30 | `query-rewriting` | rag | **DEFERRED — giải quyết sau khi #29 ship + đo baseline E5.** Layer trước embedding: gọi LLM (qua `llm-provider` adapter) rewrite/expand query → (a) chuẩn hoá thuật ngữ nội bộ ("KH" → "Knowledge Hub"), (b) sinh synonym, (c) sinh translation 1–2 ngôn ngữ khác (EN ↔ JA/VI/KO). Multi-vector retrieval: embed bản gốc + rewritten + translated → dense_search song song → merge max-score → dedupe. Feature flag `RAG_QUERY_REWRITE_ENABLED=false` mặc định. Cache TTL 1h theo `hash(query)`. Mục tiêu: recall@10 ON ≥ OFF +5% trên top E5 baseline. Lý do defer: (1) cần đo recall E5 trước để biết rewriting có còn cần thiết hay không; (2) thêm 1 LLM call/query — phải đánh giá trade-off latency + chi phí Ollama load sau khi #29 stable; (3) rủi ro LLM hallucinate translation/synonym → false positive, cần guardrails (S003 input sanitization). Estimate: 5 stories, ~3.25 ngày. Plan tham khảo: `.claude/plans/xem-x-t-c-c-feature-streamed-kazoo.md` §4 feature #30. |

---

## P3 — SDD-AI Platform (Vision)

> Mở rộng Knowledge Hub thành nền tảng hỗ trợ phát triển phần mềm theo SDD spec-first với AI.
> Ba vai trò đồng thời: documentation hub + AI agent backend + AI pair programmer.

### Concept

```
Team upload spec/ADR/decisions
        ↓
  Knowledge Hub (RAG + RBAC)
        ↓
  AI agent query context       ←→   Dev viết spec tự nhiên
  thay vì đọc file local             AI suggest implementation
  (CLAUDE.md/WARM)                   grounded vào internal docs
```

Mỗi project có RBAC group riêng → AI agent của project chỉ thấy docs của mình. Nhiều project dùng chung 1 KH instance.

### Features cần thêm

| # | Feature | Mô tả |
|---|---------|-------|
| 20 | `project-namespace` | Thêm `project_id` vào RBAC model — mỗi project là 1 namespace độc lập. AI agent nhận `project_id` khi query → chỉ retrieve docs thuộc project đó. |
| 21 | `sdd-doc-types` | Metadata `doc_type` cho documents: `spec`, `adr`, `decision`, `rule`, `task`, `meeting-note`. Cho phép filter theo type khi query (vd: agent chỉ query `rules` khi /reviewcode). |
| 22 | `agent-api-endpoint` | `POST /v1/agent/context` — endpoint tối ưu cho AI agent: nhận `task_type` + `query` → trả chunks có rank theo relevance cho task đó. Khác `/v1/query` (dùng cho end-user). |
| 23 | `spec-ingestion-pipeline` | Auto-parse và ingest SDD artifacts: spec.md, tasks.md, plan.md → tự động detect `doc_type`, extract metadata (story ID, AC list, decisions). |
| 24 | `decision-search` | Query tìm kiếm decisions/ADR: "tại sao chọn X?" → retrieve các decision records liên quan. Hỗ trợ workflow /clarify và /plan của AI agent. |
| 25 | `pattern-suggestion` | AI pair programmer mode: dev commit code → KH index patterns → agent suggest implementation dựa trên patterns cũ của cùng project. |
| 26 | `sdd-phase-memory` | Auto-ingest SDD artifacts sau mỗi phase hoàn thành (/report trigger ingest). Tag theo `phase` + `project_id` + `doc_type`. Orchestrator agent query KH trước khi bắt đầu phase mới để load institutional memory thay vì WARM files — mỗi phase sau thông minh hơn phase trước nhờ accumulated context. |
| 27 | `visibility-flag` | Thêm `visibility=private\|shared\|public` vào documents table. `private` = chỉ project đó thấy (business logic, internal data). `shared` = tất cả projects trong org (security patterns, architecture decisions, lessons learned). `public` = không giới hạn. RBAC hiện tại chỉ control `user_group_id` — cần layer visibility on top. |
| 28 | `cross-project-search` | `POST /v1/agent/context` query đồng thời: `private` docs của project hiện tại + `shared` docs của toàn org trong 1 request. Cho phép cross-project learning — Project B tự động nhận patterns/decisions từ Project A mà không cần copy manual. Depends on #27 visibility-flag. |

---

## Dependency Graph
```
db-schema-embeddings
  ├── auth-api-key-oidc
  │     └── rbac-document-filter
  ├── cjk-tokenizer ──┐
  ├── document-parser ─┤
  ├── document-ingestion ──┤
  │                        ├── multilingual-rag-pipeline
  │                        │     └── query-endpoint
  └── llm-provider ────────┘           ├── answer-citation
                                       ├── conflict-detection
                                       ├── frontend-spa
                                       ├── teams-bot-adapter
                                       └── slack-bot-query-handler
```

## Tool / License Matrix

| Tool | Dùng cho | License | Free? |
|------|----------|---------|-------|
| PostgreSQL | DB | PostgreSQL License | Yes |
| pgvector | Vector search | PostgreSQL License | Yes |
| SQLAlchemy + asyncpg | ORM + driver | MIT / Apache 2.0 | Yes |
| FastAPI | Backend | MIT | Yes |
| React + Vite | Frontend | MIT | Yes |
| multilingual-e5-large | Embeddings | MIT | Yes (self-hosted) |
| MeCab + ipadic | ja tokenizer | BSD / NAIST | Yes |
| kiwipiepy | ko tokenizer | MIT | Yes |
| jieba | zh tokenizer | MIT | Yes |
| underthesea | vi tokenizer | GPL-3.0 | Yes (internal use OK) |
| Valkey | Rate limiting | BSD-3 | Yes |
| Keycloak | OIDC provider | Apache 2.0 | Yes |
| Ollama + Llama 3 | LLM (free tier) | Meta Community / MIT | Yes |
| OpenAI API | LLM (paid tier) | Proprietary | Paid |
| Claude API | LLM (paid tier) | Proprietary | Paid |

## Gợi ý thứ tự triển khai
1. `db-schema-embeddings` — schema trước, mọi thứ phụ thuộc vào đây
2. `auth-api-key-oidc` — auth middleware
3. `rbac-document-filter` — RBAC filter
4. `cjk-tokenizer` — tokenizer cho BM25 (trước RAG pipeline)
5. `llm-provider` — multi-provider LLM adapter
6. `document-ingestion` — /v1/documents endpoint
7. `multilingual-rag-pipeline` — RAG pipeline (cần tokenizer + llm-provider)
8. `query-endpoint` — /v1/query endpoint
9. `document-parser` — PDF/DOCX/HTML parser (trước document-ingestion nếu cần file upload)
10. `answer-citation` — citation + confidence
11. `conflict-detection` — conflict detection
12. `frontend-spa` — SPA
13. `teams-bot-adapter` + `slack-bot-query-handler` — bots
14. `rate-limiting` + `metrics-endpoint` — observability

## SDD Flow (thứ tự bắt buộc cho mỗi feature)
```
/specify → /clarify → /checklist → /plan → /tasks → /analyze → /implement → /reviewcode → /report
```

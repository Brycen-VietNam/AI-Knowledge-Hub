# Feature Backlog — Knowledge-Hub
> Generated: 2026-03-17 | Updated: 2026-04-29
> Source: /specify session + CONSTITUTION.md v1.2 + license review

---

## Quyết định license (2026-03-18)
- Toàn bộ stack free/OSS, ngoại trừ LLM provider (cho phép cả free và paid)
- Korean tokenizer: **kiwipiepy** (MIT) thay KoNLPy (tránh Java dependency)
- Rate limiting: **Valkey** (BSD-3) thay Redis ≥7.4
- LLM: Multi-provider architecture — Ollama/Llama (free) + OpenAI/Claude (paid) qua adapter pattern

---

## P0 — Nền tảng bắt buộc

| # | Feature | Epic | Status | Mô tả |
|---|---------|------|--------|-------|
| 1 | `db-schema-embeddings` | db | ✅ DONE (2026-03-19) | PostgreSQL schema + pgvector HNSW index + migrations |
| 2 | `auth-api-key-oidc` | auth | ✅ DONE (2026-03-24) | API-key + OIDC/SSO Bearer authentication middleware |
| 3 | `rbac-document-filter` | auth | ✅ DONE (2026-04-06) | RBAC hard-filter tại pgvector WHERE clause (C001) |
| 4 | `cjk-tokenizer` | rag | ✅ DONE (2026-04-06) | MeCab (ja), kiwipiepy (ko), jieba (zh), underthesea (vi) |
| 5 | `document-ingestion` | api | ✅ DONE (2026-04-08) | POST /v1/documents — upload, batch embed, index |
| 6 | `multilingual-rag-pipeline` | rag | ✅ DONE (2026-04-13) | Hybrid search: dense embeddings + BM25, auto lang detect |
| 7 | `llm-provider` | rag | ✅ DONE (2026-04-06) | Multi-provider LLM adapter: Ollama/Llama (free) + OpenAI/Claude (paid) |
| 8 | `query-endpoint` | api | ✅ DONE (2026-04-13) | POST /v1/query với audit log, latency SLA <2000ms |
| 29 | `embed-model-migration` | rag | ✅ DONE (2026-04-29) | Chuyển dense embedder `mxbai-embed-large` → `zylonai/multilingual-e5-large` (MIT, F16, 1024-dim). E5 prefix contract (`query: ` / `passage: `). Cosine bug fix `<->` → `<=>`. Live eval recall@10=1.000, MRR=0.964. 28/28 AC PASS. D11 carry-over: sourcing review trước production. |

## P1 — Core MVP

| # | Feature | Epic | Status | Mô tả |
|---|---------|------|--------|-------|
| 9 | `document-parser` | api | ✅ DONE (2026-04-13) | PDF/DOCX/HTML → text extraction trước khi chunk + embed |
| 10 | `answer-citation` | rag | ✅ DONE (2026-04-15) | AI answer cite ≥1 source; confidence < 0.4 → warning (C014) |
| 11 | `conflict-detection` | rag | ⬜ TODO | Phát hiện tài liệu mâu thuẫn nhau |
| 12 | `frontend-spa` | frontend | ✅ DONE (2026-04-20) | React/Vite SPA — search UI (User SPA :8080) + Admin SPA (:8081); admin-spa + user-management + change-password + ux-form-validation |
| 31 | `security-audit` | api+frontend | ✅ DONE (2026-04-29) | OWASP top-10 audit; DEFERRED-SEC-001 (password hygiene) + DEFERRED-SEC-002 (JWT token_version invalidation) trước production. 20/20 AC PASS. |

## P2 — Mở rộng sau MVP

| # | Feature | Epic | Status | Mô tả |
|---|---------|------|--------|-------|
| 13 | `teams-bot-adapter` | bots | ⬜ TODO | Microsoft Teams bot → /v1/query |
| 14 | `slack-bot-query-handler` | bots | ⬜ TODO | Slack bot → /v1/query |
| 15 | `rate-limiting` | api | ✅ DONE (in query-endpoint) | Valkey sliding window — 60/min query, 20/min docs (C013) |
| 16 | `metrics-endpoint` | api | ⬜ TODO | GET /v1/metrics — latency, throughput, error rates |
| 17 | `file-storage` | api | ⬜ TODO | Lưu file gốc sau khi ingest — pluggable backend: local disk hoặc S3-compatible (MinIO/AWS S3) qua env `FILE_STORAGE_BACKEND=local\|s3`. GET /v1/documents/{id}/download trả presigned URL (S3) hoặc stream (local). |
| 18 | `confidence-retrieval-score` | rag | ✅ SUPERSEDED (D13, 2026-04-29) | D13 đã thay bằng presence-based formula (`cited_count > 0 → 0.9`). Approach retrieval-score-based vẫn khả thi nếu E5 recall xuống thấp — để trong backlog như option. |
| 19 | `multi-chunk-per-doc` | rag | ⬜ TODO | Retriever hiện dedup theo doc_id → nhiều chunks khớp từ cùng 1 doc bị collapse thành 1 chunk (mất context). Fix: dedup theo `(doc_id, chunk_index)`, giới hạn max 2 chunks/doc. Config qua env `RAG_MAX_CHUNKS_PER_DOC=2`. |
| 30 | `query-rewriting` | rag | ⬜ DEFERRED | **Trigger: E5 recall@10 < 0.6 in production, hoặc user demand.** Layer trước embedding: LLM rewrite/expand query → synonym + cross-lingual translation. Feature flag `RAG_QUERY_REWRITE_ENABLED=false`. Estimate: 5 stories, ~3.25 ngày. E5 baseline đã đo: recall@10=1.000 (fixture set) — không cần triển khai ngay. |

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

# Feature Backlog — Knowledge-Hub
> Generated: 2026-03-17 | Updated: 2026-04-08
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

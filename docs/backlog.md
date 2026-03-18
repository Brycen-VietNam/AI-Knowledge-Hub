# Feature Backlog — Knowledge-Hub
> Generated: 2026-03-17 | Source: /specify session + CONSTITUTION.md v1.2

---

## P0 — Nền tảng bắt buộc

| # | Feature | Epic | Mô tả |
|---|---------|------|-------|
| 1 | `auth-api-key-oidc` | auth | API-key + OIDC/SSO Bearer authentication middleware |
| 2 | `rbac-document-filter` | auth | RBAC hard-filter tại pgvector WHERE clause (C001) |
| 3 | `db-schema-embeddings` | db | PostgreSQL schema + pgvector HNSW index + migrations |
| 4 | `multilingual-rag-pipeline` | rag | Hybrid search: dense embeddings + BM25, auto lang detect |
| 5 | `query-endpoint` | api | POST /v1/query với audit log, latency SLA <2000ms |

## P1 — Core MVP

| # | Feature | Epic | Mô tả |
|---|---------|------|-------|
| 6 | `document-ingestion` | api | POST /v1/documents — upload, batch embed, index |
| 7 | `cjk-tokenizer` | rag | MeCab (ja), KoNLPy (ko), jieba (zh), underthesea (vi) |
| 8 | `conflict-detection` | rag | Phát hiện tài liệu mâu thuẫn nhau |
| 9 | `answer-citation` | rag | AI answer cite ≥1 source; confidence < 0.4 → warning |
| 10 | `frontend-spa` | frontend | React/Vite SPA — search UI, multilingual |

## P2 — Mở rộng sau MVP

| # | Feature | Epic | Mô tả |
|---|---------|------|-------|
| 11 | `teams-bot-adapter` | bots | Microsoft Teams bot → /v1/query |
| 12 | `slack-bot-query-handler` | bots | Slack bot → /v1/query |
| 13 | `rate-limiting` | api | Redis sliding window — 60/min query, 20/min docs |
| 14 | `metrics-endpoint` | api | GET /v1/metrics — latency, throughput, error rates |

---

## SDD Flow (thứ tự bắt buộc)
```
/constitution → /specify → /clarify → /checklist
     → /plan → /tasks → /analyze → /implement → /reviewcode
          ↓
     → /report
```

## Gợi ý thứ tự triển khai
1. `db-schema-embeddings` — schema trước, mọi thứ phụ thuộc vào đây
2. `auth-api-key-oidc` — auth middleware
3. `rbac-document-filter` — RBAC filter
4. `cjk-tokenizer` — tokenizer cho BM25
5. `multilingual-rag-pipeline` — RAG pipeline
6. `query-endpoint` — /v1/query endpoint
7. `document-ingestion` — /v1/documents endpoint
8. `answer-citation` — citation + confidence
9. `conflict-detection` — conflict detection
10. `frontend-spa` — SPA
11. `teams-bot-adapter` + `slack-bot-query-handler` — bots
12. `rate-limiting` + `metrics-endpoint` — observability

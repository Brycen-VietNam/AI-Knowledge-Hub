# Spec: db-schema-embeddings
Created: 2026-03-17 | Author: /specify | Status: DRAFT

---

## LAYER 1 — Summary

| Field | Value |
|-------|-------|
| Epic | db |
| Priority | P0 |
| Story count | 4 |
| Token budget est. | ~3k |
| Critical path | S001 → S002 → S003 → S004 |
| Parallel-safe stories | S003, S004 (after S001) |
| Blocking specs | none |
| Blocked by | none |
| Agents needed | db-agent |

### Problem Statement
Knowledge-Hub cần lưu trữ embeddings đa ngôn ngữ và thực hiện vector search với RBAC filter.
Chưa có schema, migration, hay index nào được tạo — mọi feature khác đều blocked cho đến khi có DB layer.
Giải quyết ngay ở P0 để unblock rag-agent, auth-agent, api-agent.

### Solution Summary
- Tạo PostgreSQL schema: bảng `documents`, `embeddings`, `user_groups`, `audit_logs`
- pgvector extension + HNSW index trên cột `embedding` (cosine, m=16, ef_construction=64)
- CJK-aware full-text search config cho ja/ko/zh/vi (tách riêng FTS column)
- Migration files đánh số `001_` → `004_` với rollback section
- Connection pool config: min=5, max=20 tại app startup

### Out of Scope
- BM25 index (rag-agent scope — `cjk-tokenizer` spec)
- OIDC/API-key auth logic (auth-agent scope)
- Ingestion pipeline (document-ingestion spec)
- Conflict detection logic (conflict-detection spec)

---

## LAYER 2 — Story Detail

### S001: Create core database schema

**Role / Want / Value**
- As a: db-agent
- I want: PostgreSQL tables với đúng column types và constraints
- So that: mọi agent có schema ổn định để build on

**Acceptance Criteria**
- [ ] AC1: Bảng `user_groups(id, name, created_at)` tồn tại
- [ ] AC2: Bảng `documents(id UUID PK, title, lang CHAR(2), user_group_id FK, created_at, updated_at)` tồn tại
- [ ] AC3: Bảng `embeddings(id UUID PK, doc_id FK, chunk_index INT, embedding vector(1024), lang CHAR(2), user_group_id INT, created_at)` tồn tại — metadata chỉ gồm doc_id, lang, user_group_id, created_at (C002)
- [ ] AC4: Bảng `audit_logs(id UUID PK, user_id, doc_id FK, query_hash, accessed_at)` tồn tại (C008)
- [ ] AC5: Migration file `001_create_core_schema.sql` với rollback section ở cuối (C010)

**API Contract** — N/A (DB schema only)

**Auth Requirement**
- [ ] N/A — schema level

**Non-functional**
- Audit log: schema required (populated by query-endpoint)
- CJK support: lang column CHAR(2) đủ để store ja/ko/zh/vi/en

**Implementation notes**
- Dùng UUID v4 cho tất cả PK (gen_random_uuid())
- lang dùng ISO 639-1: "ja", "en", "vi", "ko", "zh"
- user_group_id INT (FK) — không phải UUID (keeps joins simple)

---

### S002: Add pgvector extension and HNSW index

**Role / Want / Value**
- As a: rag-agent
- I want: pgvector HNSW index trên `embeddings.embedding`
- So that: vector search không dùng sequential scan (P003)

**Acceptance Criteria**
- [ ] AC1: Extension `pgvector` được enable: `CREATE EXTENSION IF NOT EXISTS vector`
- [ ] AC2: Column `embedding vector(1024)` trên bảng `embeddings` (multilingual-e5-large = 1024 dims)
- [ ] AC3: HNSW index: `CREATE INDEX idx_embeddings_hnsw ON embeddings USING hnsw(embedding vector_cosine_ops) WITH (m=16, ef_construction=64)`
- [ ] AC4: Index tồn tại khi verify: `\d embeddings` hiển thị hnsw index
- [ ] AC5: Migration file `002_add_pgvector_hnsw.sql` với rollback section (P003, C010)

**Non-functional**
- Latency: HNSW index bắt buộc — không được sequential scan
- Cosine similarity (`<->` operator với vector_cosine_ops)

**Implementation notes**
- Rollback: `DROP INDEX idx_embeddings_hnsw; DROP EXTENSION vector CASCADE;`

---

### S003: Configure CJK-aware full-text search

**Role / Want / Value**
- As a: rag-agent
- I want: FTS column cho CJK content
- So that: BM25 indexer có column tokenized sẵn để index (C005, C006)

**Acceptance Criteria**
- [ ] AC1: Column `content_fts tsvector` trên bảng `documents`
- [ ] AC2: Trigger hoặc migration note: `content_fts` được populate bởi application layer (rag-agent xử lý tokenization — không dùng pg built-in parser cho CJK)
- [ ] AC3: GIN index trên `content_fts`: `CREATE INDEX idx_documents_fts ON documents USING gin(content_fts)`
- [ ] AC4: Migration file `003_add_fts_column.sql` với rollback section

> **Assumption**: Application layer (rag-agent, BM25 indexer) chịu trách nhiệm tokenize CJK text trước khi ghi vào `content_fts`. PostgreSQL built-in parser không hỗ trợ CJK đúng cách.
> Confirm hoặc /clarify trước /plan.

**Non-functional**
- CJK support: ja (MeCab), ko (kiwipiepy), zh (jieba), vi (underthesea) — tokenization ở application layer

---

### S004: Configure connection pool and session factory

**Role / Want / Value**
- As a: api-agent / all agents
- I want: async SQLAlchemy connection pool tại app startup
- So that: không có per-request connection creation (C011)

**Acceptance Criteria**
- [ ] AC1: `create_async_engine` với `pool_size=5, max_overflow=15` (= effective max 20) (C011)
- [ ] AC2: Engine khởi tạo tại `backend/db/session.py` — không gọi trong request handler
- [ ] AC3: `AsyncSession` factory export từ `session.py` để các agent import
- [ ] AC4: Health check query: `SELECT 1` chạy thành công qua pool khi startup

> **Assumption**: Dùng asyncpg driver (`postgresql+asyncpg://`).
> Confirm hoặc /clarify trước /plan.

**Implementation notes**
- File: `backend/db/session.py`
- Export: `async_session_factory`, `engine`
- Pool: `pool_size=5, max_overflow=15, pool_pre_ping=True` (asyncpg driver)

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC4 | CONSTITUTION.md | C002 (PII restriction), C008 (audit log) | 2026-03-12 |
| AC5 | CONSTITUTION.md | C010 (migration files) | 2026-03-12 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC5 | CONSTITUTION.md | C001 (RBAC at DB layer), PERF.md P003 (HNSW required) | 2026-03-12 |
| AC2 (1024 dims) | Conversation | /specify session 2026-03-17 — confirmed multilingual-e5-large | 2026-03-17 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC4 | CONSTITUTION.md | C005 (CJK tokenizer), C006 (underthesea for vi) | 2026-03-12 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC4 | CONSTITUTION.md | C011 (connection pool min=5, max=20) | 2026-03-12 |

---

# Sources Traceability: db-schema-embeddings
Created: 2026-03-17 | Feature spec: `docs/specs/db-schema-embeddings.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source.
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Create core database schema

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: user_groups table | Business logic | CONSTITUTION.md — C002, C001 | RBAC requires user_group_id on embeddings; groups table is FK target | 2026-03-12 |
| AC2: documents table | Business logic | CONSTITUTION.md — C002 | lang field required for auto-detect (C009); user_group_id for RBAC (C001) | 2026-03-12 |
| AC3: embeddings table — metadata only | Requirement doc | CONSTITUTION.md — C002 | "PII must never appear in vector metadata — doc_id, lang, user_group_id, created_at only" | 2026-03-12 |
| AC4: audit_logs table | Requirement doc | CONSTITUTION.md — C008 | "Audit log required for every document retrieval: user_id, doc_id, timestamp, query_hash" | 2026-03-12 |
| AC5: migration file 001_ | Requirement doc | CONSTITUTION.md — C010 | "All schema changes via numbered migration files" | 2026-03-12 |

### Story S002: Add pgvector extension and HNSW index

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: pgvector extension | Business logic | CONSTITUTION.md — tech stack | "PostgreSQL + pgvector (HNSW index required)" | 2026-03-12 |
| AC2: vector(1024) dimension | Conversation | /specify session — stakeholder confirmed multilingual-e5-large | multilingual-e5-large output dim = 1024 | 2026-03-17 |
| AC3: HNSW index params | Requirement doc | PERF.md — P003 | "CREATE INDEX ... USING hnsw ... WITH (m=16, ef_construction=64)" | 2026-03-12 |
| AC4: index verification | Business logic | PERF.md — P003 | Sequential scan on embeddings table forbidden | 2026-03-12 |
| AC5: migration file 002_ | Requirement doc | CONSTITUTION.md — C010 | Numbered migration files mandatory | 2026-03-12 |

### Story S003: Configure CJK-aware full-text search

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: content_fts column | Requirement doc | CONSTITUTION.md — C005, C006 | CJK + vi require language-aware tokenizer; FTS column stores result | 2026-03-12 |
| AC2: app-layer tokenization | Business logic | HARD.md — R005 | "MeCab/Sudachi for ja, underthesea for vi, jieba for zh" | 2026-03-12 |
| AC3: GIN index | Business logic | Standard PostgreSQL FTS pattern | GIN index required for tsvector BM25 queries | 2026-03-12 |
| AC4: migration file 003_ | Requirement doc | CONSTITUTION.md — C010 | Numbered migration files mandatory | 2026-03-12 |

### Story S004: Configure connection pool and session factory

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: pool_size=10, max_overflow=10 | Requirement doc | CONSTITUTION.md — C011 | "PostgreSQL connection pool min=5 max=20. Never open per-request connection." | 2026-03-12 |
| AC2: engine at startup | Requirement doc | PERF.md — P005 | "pool configured at app startup via create_async_engine" | 2026-03-12 |
| AC3: AsyncSession factory | Business logic | ARCH.md — A001 | db-agent boundary — other agents import session factory, not engine | 2026-03-12 |
| AC4: health check query | Business logic | CONSTITUTION.md — C003, HARD.md | /v1/health uses pool; startup validation prevents silent failures | 2026-03-12 |

---

## Summary

**Total ACs:** 18
**Fully traced:** 18/18 ✓
**Pending sources:** 0

---

## Source Type Reference

| Type | Examples |
|------|---------|
| **Requirement doc** | CONSTITUTION.md, HARD.md, PERF.md, ARCH.md |
| **Business logic** | BrSE analysis, architectural pattern, compliance rule |
| **Conversation** | /specify session decision, design discussion |
| **Existing behavior** | Current system code, API response |
| **Ticket** | JIRA ticket, GitHub issue |

---

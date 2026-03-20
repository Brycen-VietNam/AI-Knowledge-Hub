# COLD Archive: db-schema-embeddings — Full Feature
Archived: 2026-03-19 | Status: DONE ✅

## Summary
PostgreSQL DB foundation for Knowledge-Hub. 4 stories, 10 tasks, 21 tests, 3 migrations.

## Stories
- S001: Core schema — 4 tables (user_groups, documents, embeddings, audit_logs)
- S002: pgvector + HNSW index — vector(1024), m=16, ef_construction=64, cosine
- S003: CJK FTS — content_fts tsvector + GIN index (app-layer tokenization, D02)
- S004: Session factory — asyncpg, pool_size=5, max_overflow=15

## Key Decisions
- D01: multilingual-e5-large, 1024 dims
- D02: CJK tokenization in app layer (rag-agent), NOT pg trigger
- D03: asyncpg driver (postgresql+asyncpg://)
- D04: pool_size=5, max_overflow=15 (effective max=20)
- D05: UserGroup.id uses Identity() (SQL standard)
- D06: TDD mandatory — test in same task TOUCH list
- D07: .venv/ pinned requirements

## Test Results
21/21 PASSED | 3 migrations applied to Docker PostgreSQL 17 + pgvector 0.8.2

## Report
`docs/reports/db-schema-embeddings.report.md` — APPROVED 2026-03-19

## Unblocks
rag-pipeline, api-core, auth

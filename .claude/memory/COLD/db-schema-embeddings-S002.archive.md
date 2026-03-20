# COLD Archive: db-schema-embeddings / S002
Archived: 2026-03-18 | Status: DONE ✅

## Summary
Added pgvector extension + HNSW index to embeddings table.
- Migration 002: `CREATE EXTENSION vector` + `ALTER TABLE embeddings ADD COLUMN embedding vector(1024)` + HNSW index (m=16, ef_construction=64, vector_cosine_ops)
- ORM: `embedding.py` updated with `Vector(1024)` column from `pgvector.sqlalchemy`
- Test: `test_embeddings_has_vector_column` added to `tests/db/test_models.py`

## Key Decisions
- D01: multilingual-e5-large, 1024 dims (stakeholder confirmed)
- HNSW params: m=16, ef_construction=64 per PERF.md P003
- Column nullable=True: rag-agent populates post-ingestion

## Test Results
14/14 PASSED (pytest tests/db/test_models.py)
Docker DB integration: `idx_embeddings_hnsw hnsw (embedding vector_cosine_ops)` confirmed

## Files Changed
- `backend/db/migrations/002_add_pgvector_hnsw.sql` (CREATE)
- `backend/db/models/embedding.py` (MODIFY — Vector column added)
- `tests/db/test_models.py` (MODIFY — test_embeddings_has_vector_column)

## Report
`docs/reports/db-schema-embeddings-S002.report.md` — APPROVED 2026-03-18

## Deferred to S003+
- `content_fts tsvector` column → S003
- Connection pool session.py → S004

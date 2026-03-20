# COLD Archive: db-schema-embeddings / S003
Archived: 2026-03-19 | Status: DONE ✅

## Summary
Added CJK-aware FTS column to documents table.
- Migration 003: `content_fts tsvector` + `idx_documents_fts GIN index`
- ORM: `document.py` updated with `Text().with_variant(TSVECTOR, "postgresql")`
- Test: `test_documents_has_content_fts_column` added

## Key Decisions
- D02: CJK tokenization in app layer (rag-agent), NOT pg trigger
- SQLite compat: `Text().with_variant(TSVECTOR, "postgresql")` pattern

## Test Results
21/21 PASSED (pytest tests/db/)
Docker DB: `content_fts | tsvector | nullable` + `idx_documents_fts gin` confirmed

## Files Changed
- `backend/db/migrations/003_add_fts_column.sql` (CREATE)
- `backend/db/models/document.py` (MODIFY — content_fts column)
- `tests/db/test_models.py` (MODIFY — test_documents_has_content_fts_column)

## Report
`docs/reports/db-schema-embeddings-S003.report.md` — APPROVED 2026-03-19

## Deferred
- CJK tokenization + content_fts population → rag-pipeline feature (rag-agent)

-- Migration: 005_nullable_user_group_id.sql
-- Spec: docs/rbac-document-filter/spec/rbac-document-filter.spec.md#S001
-- Task: T001 — relax NOT NULL on documents.user_group_id and embeddings.user_group_id
-- Requires: migrations 001, 002, 003, 004 applied
-- Decision: D01 — user_group_id IS NULL = public document (no is_public column needed)
-- Decision: D02 — embeddings.user_group_id is denormalized (no FK); documents.user_group_id retains FK
-- Note: DROP NOT NULL does not affect existing rows or the FK constraint on documents
-- Note: ALTER COLUMN DROP NOT NULL is not idempotent — do not re-run on an already-nullable column

-- ============================================================
-- FORWARD
-- ============================================================

-- Allow NULL on documents.user_group_id — NULL = public (visible to all authenticated users)
ALTER TABLE documents ALTER COLUMN user_group_id DROP NOT NULL;

-- Allow NULL on embeddings.user_group_id — denormalized mirror; NULL = same public semantics
ALTER TABLE embeddings ALTER COLUMN user_group_id DROP NOT NULL;

-- Partial index for fast IS NULL branch of RBAC WHERE filter on BM25 path
-- (BM25 queries start from documents.content_fts — filter on documents.user_group_id)
CREATE INDEX IF NOT EXISTS idx_documents_public ON documents(id) WHERE user_group_id IS NULL;

-- Partial index for fast IS NULL branch of RBAC WHERE filter on dense path
-- Index on doc_id (not id) — useful for retrieval joins back to documents table (clarify Q7)
CREATE INDEX IF NOT EXISTS idx_embeddings_public ON embeddings(doc_id) WHERE user_group_id IS NULL;

-- ============================================================
-- ROLLBACK
-- Run statements in reverse order to respect NOT NULL re-addition
-- Fill NULLs with a valid group BEFORE restoring the NOT NULL constraint
-- ============================================================
-- DROP INDEX IF EXISTS idx_embeddings_public;
-- DROP INDEX IF EXISTS idx_documents_public;
-- UPDATE embeddings SET user_group_id = (SELECT MIN(id) FROM user_groups) WHERE user_group_id IS NULL;
-- UPDATE documents  SET user_group_id = (SELECT MIN(id) FROM user_groups) WHERE user_group_id IS NULL;
-- ALTER TABLE embeddings ALTER COLUMN user_group_id SET NOT NULL;
-- ALTER TABLE documents  ALTER COLUMN user_group_id SET NOT NULL;

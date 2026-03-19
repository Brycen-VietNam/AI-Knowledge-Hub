-- Migration: 003_add_fts_column.sql
-- Spec: docs/specs/db-schema-embeddings.spec.md#S003
-- Task: T001 — Add content_fts tsvector column + GIN index
-- Decision: D02 — CJK tokenization in app layer (rag-agent via MeCab/kiwipiepy/jieba/underthesea)
--            PostgreSQL built-in parser does not support CJK.
-- Requires: migration 001 applied (documents table must exist)

-- ============================================================
-- FORWARD
-- ============================================================

-- Populated by application layer (rag-agent). PostgreSQL built-in parser does not support CJK.
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_fts tsvector;

-- GIN index for fast full-text search (B-tree cannot index tsvector)
CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents USING gin(content_fts);

-- ============================================================
-- ROLLBACK
-- ============================================================
-- DROP INDEX IF EXISTS idx_documents_fts;
-- ALTER TABLE documents DROP COLUMN IF EXISTS content_fts;

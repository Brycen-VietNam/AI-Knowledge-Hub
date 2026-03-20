-- Migration: 002_add_pgvector_hnsw.sql
-- Spec: docs/specs/db-schema-embeddings.spec.md#S002
-- Task: T001 — pgvector extension + HNSW index on embeddings.embedding
-- Requires: 001_create_core_schema.sql applied first
-- Decision: D01 — multilingual-e5-large, 1024 dims (confirmed by stakeholder)
-- Rule: P003 — HNSW index required, no sequential scan on embeddings

-- ============================================================
-- FORWARD
-- ============================================================

-- Step 1: Enable pgvector extension (idempotent — safe to re-run)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add embedding column to embeddings table
-- nullable intentional: rag-agent populates after ingestion (separate scope)
ALTER TABLE embeddings
    ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Step 3: HNSW index for cosine similarity search
-- m=16, ef_construction=64 per PERF.md P003 — correct for <10M vectors
-- vector_cosine_ops: cosine distance for multilingual-e5-large (normalized embeddings)
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- ROLLBACK
-- Run in reverse order: index → column → extension
-- ============================================================
-- DROP INDEX IF EXISTS idx_embeddings_hnsw;
-- ALTER TABLE embeddings DROP COLUMN IF EXISTS embedding;
-- DROP EXTENSION IF EXISTS vector CASCADE;

-- Migration: 006_add_document_status_and_chunk_text.sql
-- Spec: docs/document-ingestion/spec/document-ingestion.spec.md#S005
-- Task: S005-db-T001 — add status to documents + text to embeddings
-- Decision: D07 — status column required for async ingestion lifecycle
-- Decision: D11 — chunk text stored in embeddings.text, NOT raw content in documents
-- Requires: migrations 001–005 applied

-- ============================================================
-- FORWARD
-- ============================================================

-- documents.status: tracks async ingestion lifecycle (processing → ready | failed)
ALTER TABLE documents ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'processing';
ALTER TABLE documents ADD CONSTRAINT documents_status_check
    CHECK (status IN ('processing', 'ready', 'failed'));

-- embeddings.text: stores chunk text for RAG retrieval (D11 — avoids storing raw content in documents)
ALTER TABLE embeddings ADD COLUMN text TEXT NOT NULL DEFAULT '';
ALTER TABLE embeddings ALTER COLUMN text DROP DEFAULT;

-- ============================================================
-- ROLLBACK
-- ============================================================
-- ALTER TABLE embeddings DROP COLUMN text;
-- ALTER TABLE documents DROP CONSTRAINT documents_status_check;
-- ALTER TABLE documents DROP COLUMN status;

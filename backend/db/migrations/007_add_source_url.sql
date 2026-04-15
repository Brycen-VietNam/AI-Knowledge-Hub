-- Migration: 007_add_source_url.sql
-- Feature: answer-citation
-- Decision: D-CIT-02 — source_url column; D-CIT-06 — nullable, no backfill required

-- PRE-CHECK: Run the query below BEFORE applying this migration.
-- Expected result: count = 0 (lang is NOT NULL in ORM; clean installs always return 0).
-- If count > 0 on a legacy install, the d.lang or "und" fallback in retriever.py applies.
--
--   SELECT COUNT(*) FROM documents WHERE lang IS NULL;

-- ---------------------------------------------------------------------------
-- UP
-- ---------------------------------------------------------------------------

ALTER TABLE documents ADD COLUMN source_url TEXT;

-- No DEFAULT, no NOT NULL constraint — nullable, zero-downtime safe in PostgreSQL.
-- No index: source_url is display-only and never used as a query filter.

-- ---------------------------------------------------------------------------
-- ROLLBACK
-- ---------------------------------------------------------------------------

-- ALTER TABLE documents DROP COLUMN source_url;

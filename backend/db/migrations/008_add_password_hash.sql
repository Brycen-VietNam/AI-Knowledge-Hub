-- Migration: 008_add_password_hash.sql
-- Feature: frontend-spa / S000 — Username/Password Auth Endpoint
-- Task: T001 — add password_hash column to users table
-- Decision: D009 — migration number 008 (follows 007_add_source_url.sql)
-- Decision: D005 — username/password local auth (bcrypt + HS256 JWT)
-- Requires: migration 004 applied (users table exists)

-- ---------------------------------------------------------------------------
-- UP
-- ---------------------------------------------------------------------------

ALTER TABLE users ADD COLUMN password_hash TEXT;

-- Nullable: OIDC users have no local password (NULL is correct, not an error).
-- TEXT matches existing column types (email TEXT, display_name TEXT) in this table.
-- bcrypt output is ~60 chars; TEXT has no length restriction — no truncation risk.
-- No index: password_hash is never used as a query filter (auth uses username lookup only).

-- ---------------------------------------------------------------------------
-- ROLLBACK
-- ---------------------------------------------------------------------------

-- ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

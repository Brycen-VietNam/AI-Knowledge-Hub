-- Migration: 001_create_core_schema.sql
-- Spec: docs/specs/db-schema-embeddings.spec.md#S001
-- Task: T001 — Core schema (4 tables)
-- Requires: PostgreSQL >= 13 (gen_random_uuid() built-in)
-- Note: embedding vector(1024) column added in migration 002 after pgvector extension

-- ============================================================
-- FORWARD
-- ============================================================

-- user_groups: RBAC groups (department/team level)
-- id is INT (not UUID) — FK target kept simple for join performance
CREATE TABLE IF NOT EXISTS user_groups (
    id          INT         GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- documents: source documents uploaded by users
-- updated_at: set by application layer on UPDATE (no trigger)
CREATE TABLE IF NOT EXISTS documents (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title           TEXT        NOT NULL,
    lang            CHAR(2)     NOT NULL,   -- ISO 639-1: en/ja/ko/zh/vi
    user_group_id   INT         NOT NULL REFERENCES user_groups(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- embeddings: vector chunks from documents
-- user_group_id denormalized (no FK) for direct RBAC WHERE clause without JOIN (R001)
-- embedding vector(1024) added in migration 002
CREATE TABLE IF NOT EXISTS embeddings (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id          UUID        NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index     INT         NOT NULL,
    lang            CHAR(2)     NOT NULL,   -- ISO 639-1
    user_group_id   INT         NOT NULL,   -- denormalized for RBAC filter (R001, C002)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- audit_logs: document access log for compliance (C008)
-- user_id is TEXT placeholder — replaced with FK when auth schema is defined (auth-agent scope)
CREATE TABLE IF NOT EXISTS audit_logs (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT        NOT NULL,   -- placeholder; FK added by auth-agent (auth-api-key-oidc spec)
    doc_id      UUID        NOT NULL REFERENCES documents(id),
    query_hash  TEXT        NOT NULL,
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- ROLLBACK
-- Run in reverse order to respect FK dependencies
-- ============================================================
-- DROP TABLE IF EXISTS audit_logs CASCADE;
-- DROP TABLE IF EXISTS embeddings CASCADE;
-- DROP TABLE IF EXISTS documents CASCADE;
-- DROP TABLE IF EXISTS user_groups CASCADE;

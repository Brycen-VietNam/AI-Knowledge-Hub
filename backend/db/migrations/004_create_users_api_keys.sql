-- Migration: 004_create_users_api_keys.sql
-- Spec: docs/specs/auth-api-key-oidc.spec.md#S001
-- Task: T001 — users + api_keys tables + audit_logs FK migration
-- Requires: migrations 001, 002, 003 applied
-- Decision: D08 — audit_logs is empty in dev; no UPDATE step needed for user_id cast
-- Decision: D04 — NOT VALID + VALIDATE pattern avoids table lock on FK add

-- ============================================================
-- FORWARD
-- ============================================================

-- users: identity records for OIDC and API-key principals
-- email and display_name nullable (D07 — configurable claim mapping; absent claim = NULL)
CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    sub             TEXT        NOT NULL UNIQUE,   -- OIDC subject identifier (e.g. Keycloak sub)
    email           TEXT,                          -- nullable: OIDC_EMAIL_CLAIM may be absent
    display_name    TEXT,                          -- nullable: OIDC_NAME_CLAIM may be absent
    is_active       BOOL        NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index on sub for fast JIT UPSERT lookup (D02 — JIT provisioning on first OIDC login)
CREATE INDEX IF NOT EXISTS idx_users_sub ON users(sub);

-- api_keys: hashed API keys for bot/service-account principals
-- key_plaintext is never stored (S005, R002) — only SHA-256 hash
-- user_group_ids: INTEGER[] — group memberships baked in at key creation (no DB lookup at auth time)
-- last_used_at: updated on each successful auth for monitoring; nullable at creation
CREATE TABLE IF NOT EXISTS api_keys (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash        TEXT        NOT NULL UNIQUE,   -- SHA-256 of raw key; no plaintext stored (R002)
    user_group_ids  INTEGER[]   NOT NULL DEFAULT '{}',
    last_used_at    TIMESTAMPTZ,                   -- nullable; set on first use
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migrate audit_logs.user_id: TEXT placeholder → UUID FK to users(id)
-- D08: audit_logs is empty in dev — no UPDATE step required before type cast
ALTER TABLE audit_logs
    ALTER COLUMN user_id TYPE UUID USING user_id::uuid;

-- Add FK as NOT VALID first (avoids full table scan lock; table is empty so VALIDATE is instant)
ALTER TABLE audit_logs
    ADD CONSTRAINT fk_audit_logs_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    NOT VALID;

ALTER TABLE audit_logs
    VALIDATE CONSTRAINT fk_audit_logs_user;

-- ============================================================
-- ROLLBACK
-- Run statements in reverse order to respect FK dependencies
-- ============================================================
-- ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS fk_audit_logs_user;
-- ALTER TABLE audit_logs ALTER COLUMN user_id TYPE TEXT USING user_id::text;
-- DROP TABLE IF EXISTS api_keys CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP INDEX IF EXISTS idx_users_sub;

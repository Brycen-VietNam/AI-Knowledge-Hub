-- Migration: 011_api_keys_key_prefix_name.sql
-- Feature: user-management
-- Spec: docs/user-management/spec/user-management.spec.md#S003–S004
-- Resolves clarify blockers Q1 + Q2 (Q3 already resolved by migration 008)
-- Requires: migrations 004 (api_keys + audit_logs FK), 008 (password_hash) applied

-- ============================================================
-- UP
-- ============================================================

-- Q1a: key_prefix — first 8 chars of plaintext key (e.g. "kh_abcde")
--      Stored for admin identification only; never the full key or hash.
--      Nullable for backward-compat with existing rows (none in prod yet).
ALTER TABLE api_keys ADD COLUMN key_prefix TEXT;

-- Q1b: name — optional human label set at key creation (e.g. "teams-bot")
--      Max 100 chars enforced at application layer (Pydantic), not DB constraint.
ALTER TABLE api_keys ADD COLUMN name TEXT;

-- Q2: audit_logs.user_id FK — change RESTRICT → SET NULL
--     Rationale: deleting a user must not block if audit rows exist.
--     SET NULL preserves the audit trail (compliance C008) while allowing the DELETE.
--     NULL user_id = "deleted user" — interpretable, not a data-loss scenario.
ALTER TABLE audit_logs
    DROP CONSTRAINT IF EXISTS fk_audit_logs_user;

ALTER TABLE audit_logs
    ALTER COLUMN user_id DROP NOT NULL;

ALTER TABLE audit_logs
    ADD CONSTRAINT fk_audit_logs_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE SET NULL
    NOT VALID;

ALTER TABLE audit_logs
    VALIDATE CONSTRAINT fk_audit_logs_user;

-- ============================================================
-- ROLLBACK
-- ============================================================

-- ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS fk_audit_logs_user;
-- ALTER TABLE audit_logs ALTER COLUMN user_id SET NOT NULL;
-- ALTER TABLE audit_logs
--     ADD CONSTRAINT fk_audit_logs_user
--     FOREIGN KEY (user_id) REFERENCES users(id)
--     NOT VALID;
-- ALTER TABLE audit_logs VALIDATE CONSTRAINT fk_audit_logs_user;
-- ALTER TABLE api_keys DROP COLUMN IF EXISTS name;
-- ALTER TABLE api_keys DROP COLUMN IF EXISTS key_prefix;

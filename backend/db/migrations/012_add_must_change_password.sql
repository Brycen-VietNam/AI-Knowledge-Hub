-- Migration 012: add must_change_password column to users
-- Spec: docs/change-password/spec/change-password.spec.md
-- Task: S001/T001

ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT TRUE;

-- rollback
-- ALTER TABLE users DROP COLUMN IF EXISTS must_change_password;

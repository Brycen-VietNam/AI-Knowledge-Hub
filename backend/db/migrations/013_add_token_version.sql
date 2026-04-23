-- Migration: 013_add_token_version
-- Spec: docs/security-audit/spec/security-audit.spec.md#S002
-- Task: S002/T001
-- Rule: A006 — migration before ORM update

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS token_version INT NOT NULL DEFAULT 1;

-- ROLLBACK: ALTER TABLE users DROP COLUMN token_version;

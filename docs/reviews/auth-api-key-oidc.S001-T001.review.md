# Code Review: S001-T001 — Migration 004: users + api_keys tables + audit_logs FK
Feature: auth-api-key-oidc | Level: full | Date: 2026-03-23 | Reviewer: Claude (opus)

---

## Task Review Criteria
- [x] `users` table: UUID PK via `gen_random_uuid()`, `sub TEXT UNIQUE NOT NULL`, `email`/`display_name` nullable, `is_active BOOL DEFAULT TRUE`, `created_at TIMESTAMPTZ DEFAULT now()`
- [x] `api_keys` table: UUID PK, `user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE`, `key_hash TEXT NOT NULL UNIQUE`, `user_group_ids INTEGER[] NOT NULL DEFAULT '{}'`, `last_used_at TIMESTAMPTZ` nullable
- [x] `CREATE INDEX idx_users_sub ON users(sub)` present
- [x] `ALTER TABLE audit_logs ALTER COLUMN user_id TYPE UUID USING user_id::uuid` before FK add
- [x] FK added as `NOT VALID` then `VALIDATE CONSTRAINT` (two statements)
- [x] Rollback section present (commented, reverse order)
- [x] Header: `-- Requires: migrations 001, 002, 003 applied`
- [x] Rule satisfied: A006 (numbered migration with rollback)
- [x] Rule satisfied: S001 (no string interpolation — pure DDL, no dynamic SQL)

## Full Checks
- [x] No files outside TOUCH list modified
- [x] No magic numbers — defaults are spec-driven
- [x] No commented-out dead code (rollback section is intentional per migration convention)
- [x] Migration header references spec, task, decisions (D04, D08)
- [x] Pattern consistent with `001_create_core_schema.sql`

## Issues Found

### ⚠️ WARNING — Minor
- Rollback section lists `DROP INDEX IF EXISTS idx_users_sub` after `DROP TABLE IF EXISTS users CASCADE`. The index is automatically dropped by CASCADE, making this line redundant. Harmless — keeps rollback explicit and readable.

## Verdict
**[x] APPROVED** [ ] CHANGES REQUIRED [ ] BLOCKED

Blockers: 0

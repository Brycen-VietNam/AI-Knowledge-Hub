# Code Review: S001-T003 — ApiKey ORM model
Feature: auth-api-key-oidc | Level: full | Date: 2026-03-23 | Reviewer: Claude (opus)

---

## Task Review Criteria
- [x] `__tablename__ == "api_keys"`
- [x] `user_id: Mapped[uuid.UUID]` with `ForeignKey("users.id", ondelete="CASCADE")`
- [x] `key_hash: Mapped[str]` with `unique=True, nullable=False` — no `key_plaintext` column
- [x] `user_group_ids` uses `ARRAY(Integer)` dialect type, `default=list`
- [x] `last_used_at: Mapped[datetime | None]` nullable
- [x] No imports from `backend/rag/` or `backend/api/` (A001)
- [x] Rule satisfied: R002 (no PII — key_hash only, no plaintext)

## Full Checks
- [x] No files outside TOUCH list modified
- [x] No magic numbers
- [x] No commented-out dead code
- [x] Pattern consistent with existing models

## Rules
- [x] A001: No cross-boundary imports
- [x] R002: No PII columns — `key_hash` only, no `key_plaintext`
- [x] S001: No SQL string interpolation
- [x] S005: No hardcoded secrets

## Issues Found

### ⚠️ WARNING (resolved before REVIEWED)
- `user_group_ids` initially lacked `Mapped[list[int]]` type annotation — fixed inline before review finalized.
  Final state: `user_group_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False, default=list)` ✅

## Verdict
**[x] APPROVED** [ ] CHANGES REQUIRED [ ] BLOCKED

Blockers: 0

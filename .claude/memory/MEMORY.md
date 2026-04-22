# MEMORY INDEX
> Pointers to memory files. Keep under 200 lines.

## Project
- [project_rbac_embedding_sync_rule.md](project_rbac_embedding_sync_rule.md) — RBAC: document-ingestion must write user_group_id to both documents + embeddings atomically; NULL = public
- [project_dev_api_key.md](project_dev_api_key.md) — Dev API key `test-api-key-dev` for local Docker testing (user: dev@example.com, group_ids=[1])
- [project_temp_llm_bypass.md](project_temp_llm_bypass.md) — TEMP: LLM bypassed in query route, returns sources only (revert when ollama LLM model ready)

## Security Debt
- [feedback_deferred_sec001_password_in_store.md](feedback_deferred_sec001_password_in_store.md) — DEFERRED-SEC-001: remove raw password from authStore → implement POST /v1/auth/refresh
- [feedback_deferred_sec002_jwt_invalidation.md](feedback_deferred_sec002_jwt_invalidation.md) — DEFERRED-SEC-002: JWT session invalidation on password reset → token_version column in users table

## Feedback
- [feedback_reviewcode_save_file.md](feedback_reviewcode_save_file.md) — /reviewcode must always save file to docs/reviews/ immediately, not wait for user
- [feedback_migration_versioning.md](feedback_migration_versioning.md) — setup Alembic for migration version tracking (current initdb.d approach has no versioning)
- [feedback_api_additive_consumer_contract.md](feedback_api_additive_consumer_contract.md) — Additive API fields: if consumers not yet built, encode permissive-parsing rule in contract doc (not feature flag)

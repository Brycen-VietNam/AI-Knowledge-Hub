# COLD Memory Archive
# Features moved here when status = DONE.
# Never auto-loaded. Access via: /context <feature> --from-cold

---

## How to archive
Triggered automatically by `/report` when feature is APPROVED. Manual steps:
  1. Move `WARM/<feature>.mem.md` → `COLD/<feature>.archive.md`
  2. Add one row to Archive Index below
  3. Update `HOT.md` — remove from In Progress, clear blockers if applicable

---

## Archive Index

| Feature | Completed | Stories | Tests | Unblocks | Report |
|---------|-----------|---------|-------|----------|--------|
| db-schema-embeddings | 2026-03-19 | S001–S004 | 21/21 | auth-api-key-oidc, rbac-document-filter | docs/reports/db-schema-embeddings.report.md |
| auth-api-key-oidc | 2026-03-24 | S001–S004 | 51/51 | rbac-document-filter, document-ingestion, query-endpoint | docs/reports/auth-api-key-oidc.report.md |

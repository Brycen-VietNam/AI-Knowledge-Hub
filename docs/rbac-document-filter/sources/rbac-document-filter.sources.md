# Sources Traceability: rbac-document-filter
Generated: 2026-04-02 | Status: DRAFT

---

## Master AC → Source Map

| Story | AC | Requirement | Source Type | Reference | Date |
|-------|----|-------------|-------------|-----------|------|
| S001 | AC1–AC7 | Numbered migration files with rollback section | Project rule | ARCH.md A006 | 2026-04-02 |
| S001 | AC2–AC4 | RBAC filter at SQL WHERE level, not Python | Project rule | HARD.md R001 | 2026-04-02 |
| S001 | AC8 | Document ORM location + pattern | Existing code | db-schema-embeddings.report.md | 2026-03-19 |
| S001 | AC2 | documents table has no user_group_id yet | Existing system | db-schema-embeddings.report.md | 2026-03-19 |
| S002 | AC1–AC5 | RBAC applied before retrieval ranking | Project rule | HARD.md R001 | 2026-04-02 |
| S002 | AC6–AC7 | 0-group users → empty results (not 403) | Stakeholder decision | Conversation 2026-04-02 | 2026-04-02 |
| S002 | AC6 | Public documents visible to all authenticated users | Stakeholder decision | Conversation 2026-04-02 | 2026-04-02 |
| S002 | AC8 | No SQL string interpolation | Security rule | SECURITY.md S001 | 2026-04-02 |
| S002 | AC9 | Timeout 1800ms on retrieval call | Performance rule | PERF.md P001 | 2026-04-02 |
| S003 | AC1–AC7 | Filter coverage — group + public access matrix | Project rule | HARD.md R001 | 2026-04-02 |
| S003 | AC10 | Latency SLA < 1800ms p95 | Performance rule | PERF.md P001 | 2026-04-02 |
| S004 | AC1–AC3 | ORM model pattern from existing db feature | Existing code | db-schema-embeddings.report.md | 2026-03-19 |
| S004 | AC4–AC6 | Migration test pattern + rollback verification | Project rule | ARCH.md A006 | 2026-04-02 |
| S005 | AC1–AC2 | AuthenticatedUser interface with groups field | Existing feature | auth-api-key-oidc (DONE) | 2026-03-24 |
| S005 | AC3–AC4 | Group IDs from JWT claim (OIDC) + api_keys DB (API-key) | Stakeholder decision | Conversation 2026-04-02 | 2026-04-02 |
| S005 | AC5 | 0 groups → empty, not 403 | Stakeholder decision | Conversation 2026-04-02 | 2026-04-02 |
| S005 | AC6 | Audit log: user_id, doc_ids, query_hash, timestamp | Project rule | HARD.md R006 | 2026-04-02 |
| S005 | AC7 | request_id in all responses | Project rule | ARCH.md A005 | 2026-04-02 |
| S005 | AC8 | End-to-end latency SLA < 2000ms p95 | Project rule | HARD.md R007 + PERF.md P001 | 2026-04-02 |

---

## Resolved Decisions (confirmed at /clarify 2026-04-02–03)

| # | Question | Decision | Date |
|---|----------|----------|------|
| Q5 | "Public" mechanism | `user_group_id IS NULL` = public — no separate column | 2026-04-02 |
| Q6 | Filter table for dense vs BM25 | Dense: `embeddings.user_group_id` (no JOIN). BM25: `documents.user_group_id` | 2026-04-03 |

---

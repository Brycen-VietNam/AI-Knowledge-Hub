---
name: RBAC embedding sync rule
description: document-ingestion must always write user_group_id to both documents and embeddings tables atomically; embeddings.user_group_id is denormalized for fast RBAC filter without JOIN
type: project
---

## Rule: embeddings.user_group_id must always mirror documents.user_group_id

When ingesting a document, BOTH writes are mandatory in the same transaction:

```python
document.user_group_id = group_id      # documents table — source of truth
embedding.user_group_id = group_id     # embeddings table — denormalized for RBAC speed
```

**Why:** Migration 001 comment explicitly states `embeddings.user_group_id` is "denormalized for RBAC filter (R001, C002)" — the retriever filters on `embeddings.user_group_id` directly (no JOIN) to meet the 1800ms latency SLA. If the two columns diverge, users will see documents they shouldn't, or be denied documents they should see.

**How to apply:**
- Enforce in document-ingestion spec/tasks: atomic write to both tables
- In /reviewcode for any ingestion code: verify both columns are set in the same transaction
- If document group is ever changed, both columns must be updated together (no partial update)

---

## Rule: user_group_id IS NULL = public document

`documents.user_group_id IS NULL` means the document is public — visible to all authenticated users regardless of group membership.

**Why:** Stakeholder decision 2026-04-02. `user_group_id NOT NULL` constraint on documents table must be relaxed to nullable (migration 004) to support public documents.

**How to apply:**
- RBAC filter SQL: `WHERE (e.user_group_id = ANY(:group_ids) OR e.user_group_id IS NULL)`
- Migration 004: `ALTER TABLE documents ALTER COLUMN user_group_id DROP NOT NULL`
- Same for embeddings: `user_group_id IS NULL` = public chunk
- Users with 0 groups see only NULL-group documents (empty list if none)

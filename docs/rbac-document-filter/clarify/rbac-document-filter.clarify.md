# Clarify: rbac-document-filter
Generated: 2026-04-03 | Spec: v2 DRAFT | Status: READY FOR /checklist

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | Migration number conflict: spec says `004_nullable_user_group_id.sql` but `004_create_users_api_keys.sql` already exists (auth feature). Next available = **005**. Confirm rename to `005_nullable_user_group_id.sql`? | ✅ **AUTO-RESOLVED** — rename to 005. Confirmed by filesystem check 2026-04-03. | auto | ✅ |
| Q2 | `AuthenticatedUser.groups` — does it return `list[int]` (group IDs) or `list[str]` (group names)? Spec S005/AC3 says OIDC groups come as names → need DB lookup. Need to confirm type to avoid mismatch at retriever call. | ✅ **AUTO-ANSWERED** — auth archive D01: "JWT groups claim = group names (strings) → DB lookup". So OIDC path returns `list[str]` → lookup needed. API-key path returns `list[int]` directly. Retriever signature takes `list[int]`. | auto (auth-archive) | ✅ |
| Q3 | `api_keys` table — does it have a `group_ids` column (integer array) as assumed in S005/AC4? Auth archive says "API key creation = manual SQL seed" but column details not confirmed. | ✅ **AUTO-ANSWERED** — migration 004 line 34: `user_group_ids INTEGER[] NOT NULL DEFAULT '{}'`. Column name is `user_group_ids` (plural), not `group_ids`. Update S005/AC4 accordingly. | auto (migration 004) | ✅ |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q4 | BM25 search path: where does BM25 filter apply? `documents.content_fts` uses GIN index but RBAC field is on `embeddings`. Does BM25 query join `embeddings` or filter `documents` directly? | ✅ **ANSWERED 2026-04-03** — Option A: BM25 filters on `documents.user_group_id` directly. Dense path filters on `embeddings.user_group_id`. Two separate filter fields, same NULL=public semantics. Applied to spec S002/AC3. |
| Q5 | Rollback default group ID: spec assumes `id=1` exists in `user_groups` for rollback `SET user_group_id = 1`. Is group ID 1 guaranteed to exist in all environments? | Default: use `(SELECT MIN(id) FROM user_groups)` as safe fallback — avoid hardcoding 1. |
| Q6 | `top_k` range: spec uses `top_k=10` default. Is there a max cap to prevent large result sets bypassing latency SLA? | Default: cap at `top_k=50` (configurable via env `RAG_MAX_TOP_K=50`). |
| Q7 | Partial index usefulness: `idx_embeddings_public ON embeddings(id) WHERE user_group_id IS NULL` — index on `id` is redundant (PK already indexed). Should this be on `doc_id` or `chunk_index` instead for query utility? | Default: change to `idx_embeddings_public ON embeddings(doc_id) WHERE user_group_id IS NULL` — more useful for retrieval joins. |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q8 | Should `is_public: bool` be included in `RetrievedDocument` response model (S005 API contract shows it)? Useful for UI to badge public docs. |
| Q9 | Cache key for OIDC group name→ID lookup: by `user_id` or by `frozenset(group_names)`? The latter is more cache-efficient for users sharing groups. |
| Q10 | Should concurrent retrieval (dense ∥ BM25) use `asyncio.gather` with `return_exceptions=True` to prevent one slow path from killing the other? |

---

## Auto-answered from existing files

| Q | Source | Answer |
|---|--------|--------|
| Q1 — migration number | `Glob backend/db/migrations/` (2026-04-03) | 004 taken → rename to 005 |
| Q3 — api_keys column name | migration 004_create_users_api_keys.sql line 34 | Column is `user_group_ids INTEGER[]`, not `group_ids` — update S005/AC4 |
| Q2 — AuthenticatedUser.groups type | auth-api-key-oidc archive D01 | OIDC = group names (str) → DB lookup; API-key = int IDs directly |
| D02 — filter on embeddings directly | migration 001 comment: "denormalized for RBAC filter without JOIN (R001)" | Confirmed: embeddings.user_group_id is the intended filter field |
| D04 — 0 groups → empty, not 403 | auth archive D06: "Empty groups → permissive login (user_group_ids=[])" | Consistent: empty groups = valid state |
| S002/AC8 — named params only | SECURITY.md S001 | SQL injection prevention mandatory |
| S002/AC9 — timeout 1800ms | PERF.md P001 | Confirmed |
| S005/AC7 — request_id in response | ARCH.md A005 | Confirmed |
| S005/AC8 — latency < 2000ms p95 | HARD.md R007 + PERF.md P001 | Confirmed |

---

## Action items before /plan

1. **Fix spec S001/AC1** ✅: rename migration to `005_nullable_user_group_id.sql` — applied to spec
2. **Fix spec S005/AC4** ✅: column is `api_keys.user_group_ids` (not `group_ids`) — applied to spec
3. **Clarify Q4** ❓: BM25 filter table — `documents.user_group_id` or `embeddings.user_group_id`? Needs human answer before /plan
4. **Fix Q7** ✅: update partial index to `idx_embeddings_public ON embeddings(doc_id) WHERE user_group_id IS NULL` — applied to spec
5. **Q4 answered** ✅: BM25 filters on `documents.user_group_id`; dense filters on `embeddings.user_group_id` — applied to spec S002/AC3

---

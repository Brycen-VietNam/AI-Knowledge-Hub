# Sources Traceability: embed-model-migration
Created: 2026-04-27 | Feature spec: `docs/embed-model-migration/spec/embed-model-migration.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (plan decision, rule, existing code, conversation).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: OllamaEmbedder refactor — query/passage prefix + batch variants

| AC | Source Type | Reference | Details | Date |
|----|---|---|---|---|
| AC1 | Plan decision | `.claude/plans/xem-x-t-c-c-feature-streamed-kazoo.md` §2 (D-EM-01) | Locked default model = multilingual-e5-large; rollback via env override | 2026-04-27 |
| AC2 | Existing behavior (external) | HF model card https://huggingface.co/intfloat/multilingual-e5-large | E5 requires `query: ` prefix on query inputs | 2026-04-27 |
| AC3 | Existing behavior (external) | Same HF model card | E5 requires `passage: ` prefix on passage inputs | 2026-04-27 |
| AC4 | Existing rule | `.claude/rules/PERF.md` P002 | Batch ≥32, asyncio.gather pattern | 2026-04-27 |
| AC5 | Conversation | lb_mui 2026-04-27 plan approval | Test data only — truncate path safe, no shim needed | 2026-04-27 |
| AC6 | Existing behavior (code) | [backend/rag/embedder.py:38](backend/rag/embedder.py#L38) | `OLLAMA_MAX_EMBED_CHARS=1400` truncation | 2026-04-27 |
| AC7 | Existing behavior (tests) | `backend/rag/tests/test_embedder.py` pattern | Coverage convention for embedder unit tests | 2026-04-27 |

### Story S002: Wire ingest path to `batch_embed_passage`

| AC | Source Type | Reference | Details | Date |
|----|---|---|---|---|
| AC1 | Plan decision | Plan §6 file modification table | Caller switch to `batch_embed_passage` | 2026-04-27 |
| AC2 | Existing behavior (code) | [backend/rag/embedder.py:62-88](backend/rag/embedder.py#L62-L88) | `insert_embeddings` signature stable | 2026-04-27 |
| AC3 | Plan verification | Plan §8 step 2 | E2E ingest of multilingual fixtures | 2026-04-27 |
| AC4 | Existing rules | `.claude/rules/HARD.md` R002, `.claude/rules/PERF.md` P002 + P004 | RBAC, batch, no N+1 | 2026-04-27 |
| AC5 | Existing schema | [backend/db/models/embedding.py:26](backend/db/models/embedding.py#L26) | `Vector(1024)` invariant | 2026-04-27 |

### Story S003: Wire query path to `embed_query`

| AC | Source Type | Reference | Details | Date |
|----|---|---|---|---|
| AC1 | Plan decision | Plan §6 | `_dense_search` switches to `embed_query` | 2026-04-27 |
| AC2 | Existing rule | `.claude/rules/ARCH.md` A004 | Hybrid weights env-configurable | 2026-04-27 |
| AC3 | Existing migration | [backend/db/migrations/002_add_pgvector_hnsw.sql:23-26](backend/db/migrations/002_add_pgvector_hnsw.sql#L23-L26) | HNSW index unchanged | 2026-04-27 |
| AC4 | Plan verification | Plan §8 step 3 (cross-lingual smoke) | JA query → EN doc retrievable | 2026-04-27 |
| AC5 | Existing rules | `.claude/rules/HARD.md` R007 + `.claude/rules/PERF.md` P001 | Latency SLA p95<2000ms | 2026-04-27 |

### Story S004: Truncate-and-reset script + AWS Ollama Modelfile setup

| AC | Source Type | Reference | Details | Date |
|----|---|---|---|---|
| AC1 | Plan decision | Plan §2 D-EM-01, §6 | Truncate cascade + sequence reset + `--confirm` | 2026-04-27 |
| AC2 | Engineering practice | Convention | Idempotency mandatory for ops scripts | 2026-04-27 |
| AC3 | Plan ops detail | Plan §7 | Full AWS `t3.medium` setup steps | 2026-04-27 |
| AC4 | Plan decision + backlog | Plan D-EM-04, [docs/backlog.md:113](docs/backlog.md#L113) | License = MIT, self-build mandate | 2026-04-27 |
| AC5 | External API contract | https://github.com/ollama/ollama/blob/main/docs/api.md | `/api/embeddings` returns 1024-elem array | 2026-04-27 |
| AC6 | Existing convention | `.env.example` repo pattern | Env var naming + default | 2026-04-27 |

### Story S005: Multilingual recall@10 evaluation harness + 120-query fixtures

| AC | Source Type | Reference | Details | Date |
|----|---|---|---|---|
| AC1 | Plan decision | Plan D-EM-03, conversation 2026-04-27 | 30 × 4 lang = 120 query, schema fields | 2026-04-27 |
| AC2 | Plan problem statement | Plan §1 | Cross-lingual is the headline win for E5 | 2026-04-27 |
| AC3 | Business logic | IR eval standard | recall@10 + MRR per lang + per category | 2026-04-27 |
| AC4 | Plan verification | Plan §8 step 4 | A/B between mxbai (baseline) vs E5 reports | 2026-04-27 |
| AC5 | Plan AC | Plan feature #29 AC8 (≥+15% recall) | Acceptance threshold for the migration | 2026-04-27 |
| AC6 | Engineering practice | Plan §6 | CLI runnable for repeatability | 2026-04-27 |
| AC7 | Engineering practice | Conversation 2026-04-27 | Fixture integrity invariant | 2026-04-27 |

---

## Summary

**Total ACs:** 30 (S001=7, S002=5, S003=5, S004=6, S005=7)
**Fully traced:** 30/30 ✓
**Pending sources:** 0

---

## How to Update

When spec changes or new ACs discovered:
1. Add row to relevant Story table
2. Include source type + reference (must be findable)
3. Add date
4. Update Summary section
5. Commit with message: `docs: update sources traceability for embed-model-migration`

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Plan decision** | `.claude/plans/<plan>.md` §X — locked decision from approved plan |
| **Existing behavior (code)** | Current backend file:line — invariant we must preserve |
| **Existing behavior (external)** | HuggingFace model card, Ollama API doc — contract we must conform to |
| **Existing rule** | `.claude/rules/{HARD,ARCH,PERF,SECURITY}.md` rule ID |
| **Engineering practice** | Convention from existing tests/scripts in this repo |
| **Conversation** | Chat with stakeholder, date + name |
| **Business logic** | IR/ML standard, compliance rule |

---

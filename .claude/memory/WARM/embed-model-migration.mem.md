# Feature Memory: embed-model-migration
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: PLANNED
Updated: 2026-04-28

---

## Summary (5 bullets max — always current)
- Switch dense embedder `mxbai-embed-large` → `intfloat/multilingual-e5-large` (MIT, self-build) for better JA/VI/KO + cross-lingual recall.
- Schema unchanged (vector(1024), HNSW cosine) — only embedder code + ingest/query callers + ops setup.
- Strategy A: truncate test data + re-ingest. No version-tracking column, no maintenance window logic.
- Demo target: AWS `t3.medium` ~$30/month, q4_k_m quantization (~400MB), embed latency 200–300ms.
- Success bar: recall@10 ≥ mxbai + 15% on 120-query eval set (30 × JA/EN/VI/KO, ~25% cross-lingual).

## Key Decisions
| ID  | Decision | Rationale | Date |
|-----|----------|-----------|------|
| D01 | Default `EMBEDDING_MODEL=multilingual-e5-large`, mxbai keeps env-override rollback path | Realign code with original D01 from db-schema-embeddings; keep escape hatch | 2026-04-27 |
| D02 | Strategy A — truncate + re-ingest; no `model_version` column | Test data only per lb_mui; avoid throwaway schema/code | 2026-04-27 |
| D03 | Quantization q4_k_m on `t3.medium` for demo | Cost ~$30/mo; quality drop 1–3% acceptable; well above mxbai for multilingual | 2026-04-27 |
| D04 | Self-build GGUF from HF `intfloat/multilingual-e5-large` (MIT); no community Ollama tag | License clarity + no third-party SLA risk | 2026-04-27 |
| D05 | Build new 120-query eval set (30 × 4 lang, ≥25% cross-lingual) | Fixtures don't cover cross-lingual which is the headline win | 2026-04-27 |
| D06 | Query rewriting/expansion is OUT of scope here — separate feature `query-rewriting` | Keep #29 small/shippable; #30 layered on top | 2026-04-27 |
| D07 | Fixture generation: Claude auto-generates synthetic queries từ test docs (S002 ingest set); lb_mui review pass/fail | No domain expert needed upfront; traceable by construction | 2026-04-27 |
| D08 | GGUF path: llama.cpp convert từ `intfloat/multilingual-e5-large` safetensors → Q4_K_M. Không dùng community GGUF | Official source = MIT clear; community = SLA risk; HF GGUF repo không tồn tại (verified) | 2026-04-27 |
| D09 | S005 pass bar: absolute recall@10 ≥ 0.6 (không đo mxbai baseline — fixture set mới) | Fixture mới → không apples-to-apples; 0.6 recall@10 = production-viable per IR literature | 2026-04-27 |

## Spec
Path: `docs/embed-model-migration/spec/embed-model-migration.spec.md`
Stories: 5 | Priority: P0
Critical path: S001 → S002 → S003 → S004 → S005
Parallel-safe: S004 can proceed alongside S001–S003

## Plan
Path: `docs/embed-model-migration/plan/embed-model-migration.plan.md` (created 2026-04-28)
Pre-SDD plan (superseded): `.claude/plans/xem-x-t-c-c-feature-streamed-kazoo.md`
Critical path: S001 → (S002 ∥ S003) → S005 — with S004 parallel-safe in G1
Parallel groups:
  G1: S001 (rag-agent) + S004 (ops) — start immediately
  G2: S002 (api-agent) + S003 (rag-agent) — after S001
  G3: S005 (rag-agent) — after S002 + S003 + S004
Token budget: ~14k total

## Task Progress
| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| —    | S001  | TODO   | rag-agent | OllamaEmbedder refactor + prefix |
| —    | S002  | TODO   | api-agent | Ingest caller switch |
| —    | S003  | TODO   | rag-agent | Retriever query path |
| —    | S004  | TODO   | ops       | Truncate script + AWS Modelfile + license doc |
| —    | S005  | TODO   | rag-agent | Eval harness + fixtures |

## Files Touched
_None yet — populated by /sync after first /implement._

## Open Questions
_Tất cả đã resolved 2026-04-27_ ✅

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Fixture curation owner? | Claude tự generate synthetic từ test docs → lb_mui review |
| Q2 | HF GGUF tồn tại không? | Không — llama.cpp convert path (verified web) |
| Q3 | Đo mxbai baseline không? | Bỏ qua → pass bar = absolute recall@10 ≥ 0.6 |

## CONSTITUTION Violations Found
_CONSTITUTION.md not present in repo at /specify time — flagged for /checklist to verify with .claude/rules/* instead._

---

## Sync: 2026-04-27 (session #125 — /clarify)
Decisions added: D07, D08, D09
Tasks changed: status SPECCING → CLARIFIED
Files touched:
- `docs/embed-model-migration/clarify/embed-model-migration.clarify.md` (new — all Q resolved)
- `docs/embed-model-migration/spec/embed-model-migration.spec.md` (S005 AC4,5 + S004 AC3 updated)
- `.claude/memory/WARM/embed-model-migration.mem.md` (D07/D08/D09 added, Q1/Q2/Q3 resolved)
- `.claude/memory/HOT.md` (status + decisions updated)
Questions resolved: Q1 ✅ Q2 ✅ Q3 ✅ — 0 blockers remain
New blockers: none
Next phase: /checklist embed-model-migration → /plan

---

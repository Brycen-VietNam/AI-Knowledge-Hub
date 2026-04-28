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
| D10 | **POC scope**: dùng community Ollama tag `zylonai/multilingual-e5-large` (F16, MIT, digest pinned `c1522b1cf095...d76b`) thay vì self-convert. SUPERSEDES D08 cho POC phase. | Spike A 2026-04-28 verified: dim=1024, latency 230–330ms warm, prefix-sensitive, cross-lingual cos=0.94. Self-convert (D08) giữ làm fallback. License MIT clean cho internal-only consumption (không redistribute) | 2026-04-28 |
| D11 | **PRODUCT-PHASE CARRY-OVER**: Trước khi chuyển từ POC → product, phải re-evaluate model sourcing. Options: (a) self-convert từ intfloat (D08 path) cho audit trail clean, (b) verify zylonai = upstream weights via cosine ≥ 0.99 vs HF reference, (c) request approved-vendor process từ Brysen IT/legal nếu policy formal hóa | Risk transition: POC chấp nhận third-party redistributor để demo nhanh; product cần audit trail + supply-chain verification; SOC2/ISO27001 compliance khả năng yêu cầu first-party source | 2026-04-28 |
| D12 | Quantization: F16 (zylonai tag) thay vì Q4_K_M. SUPERSEDES D03 cho POC. RAM ~1.1GB vẫn fit `t3.medium` 4GB | Tag có sẵn ở F16, không cần quantize step; chất lượng cao hơn dự kiến; recall@10 không bị quantize hurt | 2026-04-28 |

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
| T001 | S001  | TODO   | rag-agent | Flip EMBEDDING_MODEL default + .env.example |
| T002 | S001  | TODO   | rag-agent | Add embed_query + prefix/truncation tests |
| T003 | S001  | TODO   | rag-agent | Add embed_passage + tests |
| T004 | S001  | TODO   | rag-agent | Replace batch_embed → batch_embed_passage |
| T005 | S001  | TODO   | rag-agent | Remove old embed_one/batch_embed (gate after S002/S003 ready) |
| —    | S002  | TODO   | api-agent | Ingest caller switch |
| —    | S003  | TODO   | rag-agent | Retriever query path |
| —    | S004  | TODO   | ops       | Truncate script + AWS Modelfile + license doc |
| —    | S005  | TODO   | rag-agent | Eval harness + fixtures |

**S001 tasks file**: `docs/embed-model-migration/tasks/S001.tasks.md` (5 tasks, parallel groups G1[T001] → G2[T002,T003] → G3[T004] → G4[T005], ~3k tokens)
**S001 analysis**: `docs/embed-model-migration/tasks/S001.analysis.md` (5 findings — F1 plan correction applied to S003, F3 dismissed, F2/F4/F5 are reviewer notes)

## Plan Corrections (post-/analyze S001 — 2026-04-28)
- **S003 TOUCH list corrected**: actual query-time call-site is `backend/rag/query_processor.py:49` (`_embedder.embed_one(text)`), NOT `retriever.py` as originally planned. `retriever.py` retained only for AC6 cosine `<->` → `<=>` fix. Plan §S003 + Token Budget table + Update Log all updated. Two-file scope, ~2.5k tokens.

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

## ⚠️ POC → PRODUCT MIGRATION CHECKLIST
> Created 2026-04-28 per D10/D11. **Must be reviewed before any production deployment.**

Current POC sourcing: `ollama pull zylonai/multilingual-e5-large` (community redistributor, F16, MIT-declared, digest `sha256:c1522b1cf095b82080a9b804d86b4aa609e71a48bbdbcde7ea7864bb9b0cd76b` pinned 2026-04-28).

**Acceptable for POC because**:
- Internal-only consumption (no redistribution → MIT obligations not triggered)
- Demo on AWS `t3.medium`, single tenant, no external customers
- Spike A verified: dim=1024, prefix-sensitive, cross-lingual aligned (cos=0.94)
- Brysen Group has no formal AI-model sourcing policy currently

**Must address before product launch** (any of):
- [ ] **Path A — Self-convert** (most defensible): llama.cpp `convert-hf-to-gguf.py` từ `intfloat/multilingual-e5-large` safetensors → fp16 GGUF; host trên Brysen-controlled artifact registry (S3, GHCR private, etc.). Restores D08 original path. Audit trail clean, first-party source.
- [ ] **Path B — Verify zylonai integrity**: sentence-transformers reference compare → require cosine ≥ 0.99 across 50+ probes; document checksum match in license doc. Cheaper than A but still depends on third-party.
- [ ] **Path C — Brysen approved-vendor process**: nếu IT/legal hóa policy "approved AI model sources", chạy process formal cho zylonai HOẶC switch sang Path A.

**Triggers for re-evaluation** (any one → re-open this checklist):
- POC promoted to user-facing product (external customers, paying tenants)
- Brysen Group adopts SOC2 / ISO27001 / similar compliance framework
- zylonai tag removed from Ollama registry, or digest changes from pinned value
- Legal/IT raises supply-chain question
- Multi-tenant or multi-region deployment

**Contingency if zylonai tag disappears mid-POC**:
- Backup GGUF blob saved to: _[TODO: ops to define location in S004]_
- Pinned digest `sha256:c1522b1cf095...d76b` (re-pullable as long as Ollama keeps blob)
- Last resort: fall back to D08 self-convert path (~2h work)

**Open question carry to product phase**: Q4 (new) — Brysen Group có formal AI-model sourcing policy không? (Confirmed informal cho POC; cần verify với IT/legal before product.)

---

## Sync: 2026-04-28 (session #127 — /tasks S001 + /analyze S001)
Decisions added: none (no new D-series; only plan/scope corrections)
Tasks changed: S001 — TODO → BROKEN_DOWN (T001–T005 defined); status board added in WARM
Files created:
- `docs/embed-model-migration/tasks/S001.tasks.md` (5 atomic tasks, AC mapping AC1→T001, AC2/6/7→T002, AC3→T003, AC4/7→T004, AC5→T005)
- `docs/embed-model-migration/tasks/S001.analysis.md` (caller map, mock pattern, 5 findings)
Files modified:
- `docs/embed-model-migration/plan/embed-model-migration.plan.md` — §S003 TOUCH list corrected (query_processor.py primary + retriever.py for AC6); token estimate ~2k → ~2.5k; total ~14k → ~14.5k; Update Log entry added
Findings (from S001 analysis):
- F1 ✅ APPLIED: S003 actual call-site is `backend/rag/query_processor.py:49` (`_embedder.embed_one(text)`), NOT `retriever.py`. Plan §S003 corrected.
- F2 (note): name collision after both stories land — `OllamaEmbedder.embed_query` (S001) + `query_processor.embed_query` (S003 façade). Acceptable, both retained.
- F3 ❌ DISMISSED: `.env.example` exists at repo root (1064 bytes, 2026-04-24); initial Glob miss was tool-permission filter on `.env*`. T001 TOUCH unchanged.
- F4 (T005 cleanup list): obsolete tests at `tests/rag/test_embedder.py` L24, L41, L60, L74, L88 — explicit delete list.
- F5 (test fixture): use `[0.0]*1024` for dim assertions; existing `[0.1, 0.2, 0.3]` is len-3.
Caller map confirmed: `documents.py:95` (S002), `query_processor.py:49` (S003), `retriever.py` (consumes vector, no direct embedder call).
Test file location confirmed: `tests/rag/test_embedder.py` (Docker-safe, outside backend/).
Questions resolved: none new
New blockers: none
Next: /implement T001 (env flip + default-model assertion test)

---

## Sync: 2026-04-28 (session — /plan + Spike A)
Decisions added: D10 (zylonai for POC), D11 (product re-evaluation gate), D12 (F16 over Q4_K_M)
Decisions superseded: D03 (Q4_K_M → F16), D08 (self-convert → community tag for POC)
Spike A executed: `docs/embed-model-migration/spike/spike_e5_compare.py` — PASS
  - dim=1024 ✓
  - latency warm 230–330ms ✓ (P001 budget < 400ms)
  - prefix sensitivity cos(query, passage) ≈ 0.84 — prefix có effect ✓
  - cross-lingual EN↔JA cos = 0.94 ✓
Tag pulled: `zylonai/multilingual-e5-large` digest `sha256:c1522b1c...d76b` (2.2GB F16)
License verified: MIT (HF API + ollama.com tag page)
Bug discovered (out-of-scope): retriever uses `<->` (L2) instead of `<=>` (cosine) — HNSW index bypassed. To be folded into S003 acceptance criteria or filed as separate bug.
New questions: Q4 — Brysen formal AI-sourcing policy? (informal OK for POC per lb_mui)

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

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
| D13 | Confidence: presence-based thay vì cited_ratio. `cited_count > 0 → 0.9 (HIGH)`, no cite → `0.5 (MEDIUM)`, no answer → `0.2 (LOW)`. SUPERSEDES công thức `cited_ratio × 0.8 + 0.2` | Công thức cũ phạt oan LLM vì docs retrieval thừa không được cite — LLM đúng khi chỉ cite docs thực sự relevant cho câu trả lời. Fix kèm: multi-format citation parser hỗ trợ `【N†...】`, `[N†...]`, `(N)` ngoài `[N]` gốc | 2026-04-29 |

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
| T001 | S001  | DONE   | rag-agent | Flip EMBEDDING_MODEL default + docs/env.example |
| T002 | S001  | DONE   | rag-agent | embed_query + prefix/truncation/guard tests |
| T003 | S001  | DONE   | rag-agent | embed_passage + prefix/truncation/guard tests |
| T004 | S001  | DONE   | rag-agent | batch_embed_passage + order/prefix/batch/error tests |
| T005 | S001  | BLOCKED| rag-agent | Remove embed_one/batch_embed — waiting on S002+S003 caller swap |
| T001 | S002  | DONE   | api-agent | Swap batch_embed → batch_embed_passage in documents.py:95 + docstring fix |
| T002 | S002  | DONE   | api-agent | Pipeline-body unit test (prefix routing, dim=1024, single commit) |
| T003 | S002  | DONE   | api-agent | Multilingual ingest smoke test (JA/EN/VI/KO) — embeddings.lang populated |
| —    | S002  | DONE ✅ | api-agent | Story complete — 8 tests (7 PASS + 1 SKIP ja-MeCab) |
| T001 | S003  | TODO   | rag-agent | Swap embed_one → embed_query in query_processor.py:49 |
| T002 | S003  | TODO   | rag-agent | Update test_query_processor.py mocks + dim 768→1024 |
| T003 | S003  | TODO   | rag-agent | Cosine fix retriever.py:51 <-> → <=> + score formula |
| T004 | S003  | TODO   | rag-agent | Update test_retriever_rbac.py score expectations |
| —    | S003  | BROKEN_DOWN | rag-agent | 4 tasks defined — docs/embed-model-migration/tasks/S003.tasks.md |
| T001 | S004  | DONE   | ops       | Truncate-and-reset script (--confirm, SQLAlchemy text()) |
| T002 | S004  | TODO   | ops       | AWS Ollama setup doc (primary path + Appendix B fallback) |
| T003 | S004  | TODO   | ops       | License doc + LICENSE.e5 verbatim MIT copy |
| T004 | S004  | TODO   | ops       | Smoke test + .env.example coordination check |
| —    | S004  | BROKEN_DOWN | ops  | 4 tasks defined — docs/embed-model-migration/tasks/S004.tasks.md |
| T001 | S005  | DONE   | rag-agent | Fixture JSON — 120 queries (30×4 lang, ≥25% cross-lingual) |
| T002 | S005  | DONE   | rag-agent | Test: fixture schema validation + AC7 traceability (9/9 PASS) |
| T003 | S005  | DONE   | rag-agent | Eval harness CLI — recall@10 + MRR computation |
| T004 | S005  | DONE   | rag-agent | Generate recall_e5.md report + pass/fail verdict |
| —    | S005  | BROKEN_DOWN | rag-agent | 4 tasks defined — docs/embed-model-migration/tasks/S005.tasks.md |

**S001 tasks file**: `docs/embed-model-migration/tasks/S001.tasks.md` (5 tasks, parallel groups G1[T001] → G2[T002,T003] → G3[T004] → G4[T005], ~3k tokens)
**S001 analysis**: `docs/embed-model-migration/tasks/S001.analysis.md` (5 findings — F1 plan correction applied to S003, F3 dismissed, F2/F4/F5 are reviewer notes)

## Plan Corrections (post-/analyze S001 — 2026-04-28)
- **S003 TOUCH list corrected**: actual query-time call-site is `backend/rag/query_processor.py:49` (`_embedder.embed_one(text)`), NOT `retriever.py` as originally planned. `retriever.py` retained only for AC6 cosine `<->` → `<=>` fix. Plan §S003 + Token Budget table + Update Log all updated. Two-file scope, ~2.5k tokens.

## Query/Passage Hygiene — Deferred (Option A + flag, 2026-04-28)
Doc: `docs/embed-model-migration/notes/query-passage-hygiene.md` (full catalog + re-open decision tree)

**In #29 (folded into S001 T002/T003 review criteria)**:
- Q3: double-prefix guard — `embed_query`/`embed_passage` raise `ValueError` if input already prefixed
- X3: exact byte-level prefix check in tests (`"query: "` 7 chars, `"passage: "` 9 chars)

**Deferred — re-evaluate after S005**:
- P1 (truncation cuts long EN/VI passage tails) | P2 (CJK token-rejoin may not match raw) | P4 (no title boost) | P5 (parser metadata leak)
- Q1 (no NFKC + whitespace normalize on query) + X1 (must apply symmetric to passage) | X2 (long-doc tail recall miss)

**Out-of-scope — separate features**:
- Q2 + Q5 → `query-input-validation` (api-agent) | Q4 → A003 compliance check on `/v1/query` lang auto-detect | Q6 → `query-rewriting` (D06)

**Re-open trigger**: S005 recall@10 < 0.6 overall OR < 0.5 cross-lingual → run decision tree in notes file.

## Files Touched
- `backend/rag/embedder.py` — default flipped, `_embed` helper, `embed_query`, `embed_passage`, `batch_embed_passage`, `_check_no_prefix`; `embed_one`/`_embed_one`/`batch_embed` retained (T005 cleanup pending)
- `docs/env.example` — `EMBEDDING_MODEL=zylonai/multilingual-e5-large` + rollback comment
- `tests/rag/test_embedder.py` — 22 tests total (2 T001 + 9 T002/T003 + 4 T004 + 7 legacy); 22/22 PASS
- `docs/embed-model-migration/tasks/S001.tasks.md` — status board updated (T001–T004 DONE, T005 BLOCKED)

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

## Sync: 2026-04-29 (session #136 — D13 confidence fix + live eval PASS ✅)
Decisions added: D13 (presence-based confidence — already recorded above)
Tasks changed: none (all stories DONE); additional post-S005 work:
  - Live eval seeded + passed: recall@10=1.0, MRR=0.964
  - Confidence formula fixed + citation parser extended
Files created:
  - `scripts/seed_eval_fixtures.py` — seeds 12 docs from multilingual_recall.fixtures.json into documents+embeddings tables; uses OllamaEmbedder.embed_passage, asyncio.gather (P002 batch), DELETE+INSERT pattern (no unique constraint on chunk_index)
Files modified:
  - `backend/rag/citation_parser.py` — regex extended to support `【N†...】`, `[N†...]`, `(N)` in addition to `[N]`
  - `backend/rag/llm/openai.py` — `inline_markers_present` detection updated to match all 3 new marker formats
  - `backend/api/routes/query.py` — confidence formula replaced: `cited_ratio × 0.8 + 0.2` → D13 presence-based (`cited_count > 0 → 0.9`, else `0.5`, no answer → `0.2`)
Bugs fixed:
  - Citation parser missed `【N†L1-L4】` format (OpenRouter LLM output) → LOW confidence despite correct answers
  - `cited_ratio` formula divided by total retrieved (10 docs) → ratio=0.1 even for 1 correct cite
  - Docker: `scripts/` dir not in image → required `docker compose build app` + `docker compose up -d app` × multiple iterations
New blockers: none
Next: `/report embed-model-migration` to finalize; also security-audit awaiting lb_mui sign-off

## Sync: 2026-04-29 (session #135 — /implement S005 T003+T004 ALL DONE ✅)
Decisions added: none
Tasks changed: S005 T003→DONE, T004→DONE; S005 story DONE ✅
Files created:
- `backend/rag/eval/__init__.py` — empty package init
- `backend/rag/eval/multilingual_recall.py` — harness CLI: `_compute_metrics` (recall@10+MRR), `_pgvector_top10` (`<=>` cosine, public docs only), `run_eval` (batch embed P002 + DB loop), `main` (`--model` AC6 flag); JSON stdout
- `tests/rag/test_multilingual_recall.py` — 14 unit tests (all_hits/no_hits/partial recall, MRR rank1/rank2/mixed/no-hits, per-lang 2-lang + 4-lang, per-category, D09 verdict pass/fail ×2); 1 integration smoke (`@pytest.mark.integration`); 14/14 PASS
- `docs/embed-model-migration/reports/recall_e5.md` — report template: run metadata, global/per-lang/per-category result tables, D09 verdict section (thresholds 0.6/0.5), misses/anomalies section, traceability links
Bugs fixed: none
New blockers: none
Next: live eval run on target DB — `python -m backend.rag.eval.multilingual_recall --model zylonai/multilingual-e5-large`; fill recall_e5.md with actual numbers; then `/report embed-model-migration`

## Sync: 2026-04-29 (session #134 — /implement S005 T001+T002 DONE)
Decisions added: none
Tasks changed: S005 T001→DONE, T002→DONE
Files created:
- `backend/rag/eval/multilingual_recall.fixtures.json` — 12 ingest docs (3×4 lang, UUIDs e5000000-...001 to 033), 120 queries (30×4 lang), 35 cross-lingual entries (EN→JA:5, JA→EN:10, VI→EN:10, KO→EN:10), user_group_id=null (public), all AC7 traceability satisfied
- `tests/rag/test_eval_fixtures.py` — 9 tests: total count, per-lang count, schema validation, cross-lingual min count, cross-lingual pairs, AC7 traceability, ingest docs fields, ingest docs lang coverage; **9/9 PASS**
Bugs fixed during build:
- EN→JA direction bug: initial q-en-026..030 had JA-text queries with `query_lang: "en"` → not true cross-lingual; fixed to EN-text queries pointing to JA docs (IDs 011-013)
- UnicodeDecodeError on Windows: open() without encoding='utf-8' fails on CJK content; fixed in validation script
Key fixture decisions:
- Fixture co-defines eval corpus (`ingest_docs[]`) — no stable S002 ingest set exists (S002 uses fully mocked UUIDs, rolled back after each test)
- Fixed UUID prefix `e5000000-0000-0000-0000-0000000000{NN}`: 01-03=EN, 11-13=JA, 21-23=VI, 31-33=KO
- T002 tests pure JSON load — no DB/Ollama/OIDC stub needed
New blockers: none
Next: /implement S005 T003 — eval harness CLI (`backend/rag/eval/__init__.py` + `backend/rag/eval/multilingual_recall.py`); recall@10+MRR, --model flag (AC6), pgvector `<=>` search, `pytest.mark.integration` skip gate

---

## Sync: 2026-04-29 (session #133 — /tasks S005)
Decisions added: none
Tasks changed: S005 → BROKEN_DOWN (4 tasks defined)
Files created:
- `docs/embed-model-migration/tasks/S005.tasks.md` (4 tasks: T001+T002 TDD pair for fixtures, T003 harness CLI, T004 report + unit tests; groups G1[T001,T002] → G2[T003] → G3[T004])
Task breakdown:
- T001: `backend/rag/eval/multilingual_recall.fixtures.json` — 120 entries, 30×4 lang, ≥30 cross-lingual
- T002: `tests/rag/test_eval_fixtures.py` — schema + count + AC7 traceability (TDD pair with T001)
- T003: `backend/rag/eval/multilingual_recall.py` — harness CLI, recall@10+MRR, `--model` flag (AC6)
- T004: `tests/rag/test_multilingual_recall.py` + `docs/embed-model-migration/reports/recall_e5.md` — unit tests (mock-based) + live-run report
New blockers: none (S002+S003+S004 must be complete before T003/T004 integration run)
Next: /analyze S005 T001 → /implement S005

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

## Sync: 2026-04-28 (session #129 — /tasks S002 + /implement S002 T001–T003)
Decisions added: none
Tasks changed: S002 T001→DONE, T002→DONE, T003→DONE; S002 story complete
Files created:
- `docs/embed-model-migration/tasks/S002.tasks.md` (3 atomic tasks, AC mapping AC1/AC2→T001, AC3/AC4/AC5→T002/T003)
- `tests/rag/test_ingest_pipeline.py` (8 tests: 4 pipeline-body + 4 multilingual parametrized; 7 PASS + 1 SKIP ja-MeCab)
Files modified:
- `backend/api/routes/documents.py` — L95 `batch_embed` → `batch_embed_passage`; L67 docstring updated; header memory comment added
- `docs/embed-model-migration/tasks/S002.tasks.md` — T001/T002/T003 DONE
Test pattern notes:
- Patch `async_session_factory` at origin (`backend.db.session.async_session_factory`), NOT at `documents.py` namespace — imports inside `ingest_pipeline` are deferred (function-local), so module attribute does not exist on `documents`.
- OIDC env stub required at top of any test file under `tests/rag/` that imports from `backend.api.routes.documents` — `tests/api/conftest.py` does not propagate to `tests/rag/`.
- JA case skipped via `_mecab_available()` runtime check — established pattern from `test_tokenizers.py`.
- For real-chunker tests, mock only `OllamaEmbedder` + `async_session_factory` + `update_fts` — leave `chunk_document` real to validate `Chunk.lang` propagation end-to-end.
T005 status: still BLOCKED — only S003 caller (`query_processor.py:49` embed_one) remains. Pre-flight grep gate now: 1 caller (was 2).
New blockers: none
Next: /tasks S003 (query_processor embed_one → embed_query + retriever.py `<->` → `<=>` cosine fix)

---

## Sync: 2026-04-28 (session #130 — /tasks S003)
Decisions added: none
Tasks changed: S003 → BROKEN_DOWN (4 tasks defined)
Files created:
- `docs/embed-model-migration/tasks/S003.tasks.md` (4 tasks: T001+T002 caller-swap pair, T003+T004 cosine-fix pair; parallel groups G1[T001,T003], G2[T002,T004])
Files modified:
- `.claude/memory/WARM/embed-model-migration.mem.md` — S003 task rows added
Task breakdown:
- T001: `query_processor.py:49` `embed_one` → `embed_query` (~2 lines)
- T002: `test_query_processor.py` mock swap + dim 768→1024 assertion + no-prefix test (~12 lines)
- T003: `retriever.py:51` `<->` → `<=>` + score `1.0-dist` → `1.0-dist/2.0` (~3 lines)
- T004: `test_retriever_rbac.py` score expectations + cosine-operator regression test (~15 lines)
AC4/AC5 deferred: cross-lingual smoke + latency covered by S005 eval harness (not unit-testable without live Ollama)
S001 T005 gate: unblocked once T001 merges (last embed_one caller eliminated)
New blockers: none
Next: /analyze S003 T001 → /implement S003

---

## Sync: 2026-04-28 (session #128 — /implement S001 T001–T004)
Decisions added: D-S001-01 (double-prefix guard → ValueError fail-fast, not strip+warn)
Tasks changed: T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→BLOCKED
Files modified:
- `backend/rag/embedder.py` — EMBEDDING_MODEL default `multilingual-e5-large`; added `_embed(prompt)`, `_check_no_prefix()`, `embed_query()`, `embed_passage()`, `batch_embed_passage()`; legacy `embed_one`/`_embed_one`/`batch_embed` retained pending T005
- `docs/env.example` — `EMBEDDING_MODEL=zylonai/multilingual-e5-large` + mxbai rollback comment
- `tests/rag/test_embedder.py` — 22/22 PASS; 13 new tests (T001×2, T002×5, T003×4, T004×4); legacy batch_embed tests updated to patch `_embed`
- `docs/embed-model-migration/tasks/S001.tasks.md` — T001–T004 DONE, T005 BLOCKED, story status IN_PROGRESS
New blockers: T005 blocked — pre-flight grep found 2 live callers: `documents.py:95` (S002, `batch_embed`) + `query_processor.py:49` (S003, `embed_one`). T005 cannot land until both are swapped.
Next: /implement S002 (documents.py) or /implement S003 (query_processor.py) — both unblocked

---

## Sync: 2026-04-29 (session #133 — /implement S004 T002+T003+T004 ALL DONE)
Decisions added: none
Tasks changed: S004 T002→DONE, T003→DONE, T004→DONE | S004 story DONE ✅
Files created:
- `docs/embed-model-migration/ops/ollama_setup.md` — Ollama runbook; primary pull path + digest pin + smoke curl (1024-dim assert) + Docker run + OLLAMA_MAX_EMBED_CHARS; Appendix B self-convert (llama.cpp → GGUF → ollama create); troubleshooting table
- `docs/embed-model-migration/ops/license.md` — provenance doc; upstream=intfloat MIT; zylonai distribution; digest pinned; internal-only note; POC scope + D11 carry-over link; backup GGUF field (TODO for ops)
- `docs/embed-model-migration/ops/LICENSE.e5` — verbatim MIT license text; intfloat copyright holders
Files modified:
- `docs/env.example` — added `OLLAMA_MAX_EMBED_CHARS=1400` after EMBEDDING_MODEL line
- `docs/embed-model-migration/tasks/S004.tasks.md` — T002/T003/T004 → DONE; story status → DONE ✅
- `.claude/memory/HOT.md` — S004 DONE recorded
Notes:
- root `.env.example` (at repo root, not docs/) — permission-denied for agent write; lb_mui manually updated: `EMBEDDING_MODEL=zylonai/multilingual-e5-large` + `OLLAMA_MAX_EMBED_CHARS=1400` added
- T004 coordination check: all model tags consistent across ollama_setup.md, license.md, docs/env.example (no drift)
- T001 unit tests: 12/12 PASS confirmed in T004 run
New blockers: none
Next: S005 — eval harness + 120-query fixture set (30×JA/EN/VI/KO, ≥25% cross-lingual); recall@10 pass bar ≥ 0.6

---

## Sync: 2026-04-29 (session #132 — /tasks S004 + /implement S004 T001)
Decisions added: none
Tasks changed: S004 T001→DONE | S004 BROKEN_DOWN (4 tasks: T001 DONE, T002/T003/T004 TODO)
Files created:
- `docs/embed-model-migration/tasks/S004.tasks.md` (4 tasks, G1[T001,T002,T003] → G2[T004])
- `scripts/truncate_and_reset.py` — idempotent truncate script; `--confirm` gate; SQLAlchemy `text()`; row-count logging; `DATABASE_URL` from env; exits non-zero on error
- `tests/ops/__init__.py` — new test scope created
- `tests/ops/test_truncate_and_reset.py` — 12 tests (confirm gate×3, SQL safety×3, logging×2, idempotency×2, env config×2); 12/12 PASS
Test pattern note: tests that mock `_build_engine` must also `patch.dict("os.environ", {"DATABASE_URL": "postgresql://stub"})` — script checks env before calling `_build_engine`
New blockers: none
Next: S004 T002 (ollama_setup.md) + T003 (license.md + LICENSE.e5) — parallel-safe, run together

---

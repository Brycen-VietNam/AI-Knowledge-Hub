# Checklist: document-ingestion
Generated: 2026-04-07 | Model: haiku | Spec: v1 DRAFT | Stories: S001–S005
Approved: 2026-04-07 | Approver: lb_mui

---

## Result: ✅ PASS — WARN-approved (3/3 approved by lb_mui 2026-04-07)

**Passed: 29/32**
**Warnings: 3 — all approved**
**Blockers: 0**

---

## ✅ Passed (29/32)

### Spec Quality
- [x] Spec file exists at `docs/document-ingestion/spec/document-ingestion.spec.md`
- [x] Layer 1 summary complete — all fields filled (Epic, Priority, Story count, Token budget, Critical path, Parallel-safe, Blocking specs, Blocked by, Agents needed)
- [x] Layer 2 stories have clear AC statements — 22 ACs total, all SMART (specific, measurable, testable)
- [x] Layer 3 sources fully mapped — 22/22 ACs traced in both spec and sources file
- [x] All ACs are testable — no vague "should work well" criteria
- [x] API contract defined for S001 (POST) and S005 (GET list, GET by ID, DELETE) — internal pipeline stories S002–S004 have no public API
- [x] No silent assumptions — D01–D10 all explicitly captured in WARM memory; Q4–Q8 have stated defaults in clarify.md

### Architecture Alignment
- [x] No CONSTITUTION violations — spec aligns with all C001–C016
- [x] No HARD rule violations in spec design — R001 (RBAC WHERE clause), R002 (no PII in metadata), R003 (auth on endpoints), R004 (/v1/ prefix), R005 (CJK tokenizer), R007 (latency SLA) all addressed
- [x] Agent scope assignments match AGENTS.md registry — api-agent (routes), rag-agent (chunker, embedder, bm25), db-agent (migration 006, model) correctly scoped
- [x] Dependency direction follows ARCH.md A002 — api → rag → db (no reverse)
- [x] pgvector/schema changes have migration plan — migration 006 specified for `status` column (S005 impl notes)
- [x] Auth pattern specified — both OIDC Bearer and API-key; write permission = API-key only (D09)

### Multilingual Completeness
- [x] All 4 languages addressed — ja/en/vi/ko covered in S004 AC1 (MeCab/kiwipiepy/jieba/underthesea)
- [x] CJK tokenization strategy mentioned — S002 uses CJK-aware token counting; S004 uses TokenizerFactory.get(lang) per C005/C006
- [x] Response language behavior defined — ingestion has no response language concern; lang stored per-chunk for retrieval use

### Dependencies
- [x] Dependent specs: all blocking specs DONE — auth-api-key-oidc ✅, rbac-document-filter ✅, cjk-tokenizer ✅, llm-provider ✅
- [x] External contracts locked — Ollama /api/embeddings (D10), EMBEDDING_MODEL env var, TokenizerFactory interface (cjk-tokenizer)
- [x] No circular story dependencies — S001 → S002 → S003 → S004 linear; S003 ∥ S004 after S002

### Agent Readiness
- [x] Token budget estimated in Layer 1 — ~4k tokens
- [x] Parallel-safe stories identified — S003 ∥ S004 (after S002 complete)
- [x] Subagent assignments listed — api-agent, rag-agent, db-agent identified

---

## ⚠️ Warnings — All Approved by lb_mui 2026-04-07

---

⚠️ **WARN-1: clarify.md BLOCKER questions Q1–Q3 show ❓ (not updated with answers)**

Risk: Future readers of clarify.md see unresolved blockers and cannot determine if /plan was properly gated. Creates ambiguity about whether decisions are authoritative.

Mitigation: Decisions D08 (bm25_indexer CREATE new), D09 (OIDC=read-only / API-key=write), D10 (Ollama embeddings) are fully captured in WARM memory (`document-ingestion.mem.md`). No actual design ambiguity exists. Clarify file update is documentation hygiene only.

Approve? [x] Yes, proceed  [ ] No, resolve first — **APPROVED lb_mui 2026-04-07**

---

⚠️ **WARN-2: Prompt caching strategy not documented in spec**

Risk: Feature includes async pipeline orchestration (BackgroundTasks dispatching S002→S003→S004). If LLM prompts are added later (e.g. content quality check), caching will need to be retrofitted.

Mitigation: Ingestion pipeline has NO LLM path in current scope — no answer generation, no prompt. Marking N/A is appropriate. Route A (stable prefix) applies to subagent dispatch per CLAUDE.md default. No Route B (direct API) path in this feature.

Approve? [x] Yes, proceed (N/A — no LLM path in ingestion)  [ ] No, resolve first — **APPROVED lb_mui 2026-04-07**

---

⚠️ **WARN-3: S001 write-permission RBAC relies on auth_type check (D09) — not enforced by existing RBAC middleware**

Risk: The rbac-document-filter middleware filters by group membership (user_group_ids), not by auth_type. D09 decision (API-key=write, OIDC=read-only) requires a NEW check in documents.py that is not in the current middleware. If omitted, OIDC users could write documents.

Mitigation: Implement auth_type gate inline in `POST /v1/documents` route handler: check `current_user.auth_type == "api_key"` before proceeding. Document this in S001 implementation notes. No middleware change needed.

Approve? [x] Yes, proceed  [ ] No, resolve first — **APPROVED lb_mui 2026-04-07**

---

## ❌ Blockers

_None._

---

## Next Steps

**✅ PASS — Proceed to `/plan document-ingestion`**

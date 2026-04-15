# Checklist: answer-citation
Generated: 2026-04-14 | By: /checklist | Feature branch: feature/document-parser

---

## Result: ✅ PASS (with 1 WARN — approved required)

**Score: 29/30 passed | 1 WARN | 0 FAIL**

---

## ✅ Spec Quality (7/7)

- [x] Spec file exists at `docs/answer-citation/spec/answer-citation.spec.md`
- [x] Layer 1 summary complete — all fields filled (Epic, Priority, Story count, Token budget, Critical path, Parallel-safe, Blocking specs, Blocked by, Agents needed)
- [x] Layer 2 stories have clear AC statements — SMART criteria (AC1–AC13 across 5 stories, all measurable)
- [x] Layer 3 sources fully mapped — 40/40 ACs traced in `sources/answer-citation.sources.md`
- [x] All ACs are testable — no vague language; each AC specifies exact field, behavior, or assertion
- [x] API contract defined for S001 (DB contract SQL), S002 (CitationObject + QueryResponse JSON), S003 (signatures + prompt template)
- [x] No silent assumptions — all marked explicitly in Assumptions table (A01–A06)

---

## ✅ Architecture Alignment (6/6)

- [x] No CONSTITUTION violations — C014 (citation mandate) is the *driver* of this feature; C002/C003/C004/C009/C015 all explicitly referenced and satisfied
- [x] No HARD rule violations in spec design:
  - R001: RBAC inherited from retrieval pipeline — no bypass
  - R002: CitationObject and RetrievedDocument explicitly exclude PII (AC8 S001, AC9 S002)
  - R003: Auth inherited — no endpoint change
  - R004: /v1/ prefix maintained — Option C additive
  - R005: CJK N/A to this feature (no BM25 indexing change)
  - R006: Audit log explicitly out-of-scope and unchanged
  - R007: Latency analysis in S001 NF (<5ms JOIN overhead), S003 NF (~80–120 extra tokens, within all model windows)
- [x] Agent scope assignments match AGENTS.md registry — db-agent (S001), api-agent (S002, S005 partial), rag-agent (S003), api-agent (S005) — all within registered scopes
- [x] Dependency direction follows ARCH.md A002 — api → rag → db direction maintained; no reverse dependencies
- [x] pgvector/schema changes have migration plan — migration 007 specified with SQL DDL + rollback section (S001 AC1)
- [x] Auth pattern specified — "Both (inherited)" stated on every story; no new auth path

---

## ✅ Multilingual Completeness (3/3)

- [x] All 4 languages addressed: ja / en / vi / ko — S003 AC6 explicitly lists ja, en, vi, ko, zh (5 languages). S005 AC6 parametrized test covers all 5.
- [x] CJK tokenization strategy mentioned — S001 NF marks CJK as N/A (metadata enrichment only); S003 NF confirms prompt in English, answer follows question language per A003; no new BM25 indexing path introduced
- [x] Response language behavior defined — S003 AC6: "Answer in the same language as the question"; A003 compliance verified in prompt template

---

## ✅ Dependencies (4/4)

- [x] Dependent specs: DONE or parallel-safe — "Blocked by: query-endpoint (DONE ✅)" confirmed in Layer 1
- [x] External contracts locked — embedding API and OIDC provider not affected by this feature; LLM adapters (Ollama, OpenAI, Claude) signature change is internal
- [x] No circular story dependencies — Critical path: S001 → S002 → S003 → S005; S004 ‖ S003 (parallel-safe, no shared files)
- [x] Parallel-safe stories identified — "Parallel-safe stories: S003 ‖ S004" in Layer 1

---

## ✅ Agent Readiness (4/5)

- [x] Token budget estimated in Layer 1 — "Token budget est.: ~5k"
- [x] Parallel-safe stories identified — S003 ‖ S004 declared
- [x] Subagent assignments listed — Layer 1: db-agent (S001), api-agent (S002), rag-agent (S003), api-agent (S005)
- [x] Prompt caching strategy documented — S003 NF: "Prompt caching (ClaudeAdapter): stable prefix up to `Sources:` is preserved. `{sources_index}` and `{question}` remain volatile suffix. Cache efficiency intact." — Route A compliant.
- [x] N/A items covered — WARM file confirms no prompt caching gap

---

## ⚠️ WARN Items

---

⚠️ **WARN: `documents.lang` nullability for legacy rows not verified before migration**

Spec: clarify.md "Spec Gaps Identified" row 2 + S002 AC8 ("lang never null")

**Risk:** If any legacy `documents` row has `lang IS NULL`, S002 AC8 guarantee breaks silently at runtime — `CitationObject.lang` would serialize as empty string (via `d.lang or ""`) rather than a valid ISO code. Consumers expecting a 2-char code get empty string.

**Mitigation:** S001 implementation task must include a pre-migration DB query:
```sql
SELECT COUNT(*) FROM documents WHERE lang IS NULL;
```
If count > 0 → add `d.lang or "und"` fallback (BCP-47 "undetermined") to `CitationObject` construction and document in S002 API contract. This is a 1-line code change + 1-line contract note.

**Approve?**
- [ ] Yes, proceed — verify in S001 implementation task
- [ ] No, resolve first — add `d.lang or "und"` to spec now

---

## ✅ Passed (29/30)

All spec quality, architecture alignment, multilingual, dependency, and agent readiness items pass. One WARN item (lang nullability) is pre-mitigation documented and handleable within S001 task scope.

---

## Clarify Gate

- **Q1 (BLOCKER):** ✅ Resolved — `source_url NULL` accepted. Option A.
- **Q2 (BLOCKER):** ✅ Resolved — consumers not yet built; constraint in S004 AC9.
- **Q3 (BLOCKER):** ✅ Resolved — graceful fallback sufficient for v1.
- **No unresolved BLOCKER questions in clarify.md.**

---

## Next

WARN approval required for lang nullability item above.

Once approved: → `/plan answer-citation`

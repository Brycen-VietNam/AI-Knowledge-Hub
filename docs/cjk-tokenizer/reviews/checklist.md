# Checklist: cjk-tokenizer
Generated: 2026-04-06 | Model: haiku | Spec: DRAFT → gate result below

---

## Result: ⚠️ WARN — 0 blockers, 2 items require approval

---

### ❌ Blockers
_None._

---

### ⚠️ WARN Items (require approval before /plan)

---

**⚠️ WARN-01: Dockerfile change in rag-agent scope**
Risk: S001 requires `apt-get install mecab libmecab-dev mecab-ipadic-utf8` added to Dockerfile. Dockerfile is shared infrastructure — a rag-agent story touching it may conflict with other agents' CI assumptions or base image strategy.
Mitigation: Scope the Dockerfile change to a separate task within S001. Document it explicitly in the task file. Flag in /plan that this is an infra-touching change requiring DevOps review before merge.
Approve? [x] Yes, proceed — lb_mui 2026-04-06

---

**⚠️ WARN-02: Prompt caching strategy — N/A path**
Risk: Feature has no LLM prompts or subagent orchestration. Caching policy item marked N/A.
Mitigation: N/A — `cjk-tokenizer` is a pure Python library layer (tokenize → list[str]). No LLM call, no prompt, no subagent dispatch from within this feature. Caching strategy not applicable.
Approve? [x] Yes, proceed — auto-approved (N/A case per policy)

---

### ✅ Passed (24/24)

**Spec Quality**
- [x] Spec exists: `docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md`
- [x] Layer 1 summary complete: all fields filled (epic, priority, story count, budget, critical path, parallel-safe, agents)
- [x] Layer 2 stories: 4 stories, all ACs are SMART (specific, measurable, testable)
- [x] Layer 3 sources: 22/22 ACs fully traced — 0 pending
- [x] All ACs testable: no vague "should work" statements
- [x] API contract: N/A — internal library, no HTTP endpoint (explicitly noted in each story)
- [x] No silent assumptions: all marked explicitly; confidence threshold and Dockerfile clarified in /clarify

**Architecture Alignment**
- [x] CONSTITUTION: No violations — C005 (MeCab/kiwipiepy/jieba/underthesea), C006 (underthesea vi), C009 (no hardcode lang="en"), all satisfied by spec design
- [x] HARD rules: R005 ("whitespace split on Japanese WRONG") addressed by AC4 regression test in S004; no other HARD rules applicable
- [x] Agent scope: rag-agent owns `backend/rag/` — `backend/rag/tokenizers/` is correct scope per AGENTS.md
- [x] Dependency direction: `backend/rag/tokenizers/` → no imports from `backend/api/` or `backend/auth/` — A002 satisfied
- [x] pgvector/schema changes: None — pure Python tokenizer layer, no DB changes
- [x] Auth pattern: N/A — internal library

**Multilingual Completeness**
- [x] All 4 languages covered: ja (MeCab S001-AC1), ko (kiwipiepy S001-AC2), zh (jieba S001-AC3), vi (underthesea S001-AC4)
- [x] CJK tokenization strategy: fully defined — one backend per language, Factory dispatch in S002
- [x] Response language behavior: N/A — tokenizer outputs tokens, not user-facing responses

**Dependencies**
- [x] db-schema-embeddings: ✅ DONE (HOT.md)
- [x] auth-api-key-oidc: ✅ DONE (HOT.md)
- [x] rbac-document-filter: ✅ DONE (HOT.md)
- [x] No circular story dependencies: S001 → S002 → S003 ∥ S004 is DAG

**Agent Readiness**
- [x] Token budget: ~4k estimated in Layer 1
- [x] Parallel-safe stories: S003 ∥ S004 identified
- [x] Subagent: rag-agent single owner — no multi-agent coordination needed
- [x] Prompt caching: N/A — no LLM path (WARN-02 approved)

---

### Gate Status

```
WARN-01: ✅ Approved — lb_mui 2026-04-06
WARN-02: ✅ Auto-approved (N/A)
BLOCKERs: 0

RESULT: ✅ PASS (WARN-approved) — proceed to /plan
```

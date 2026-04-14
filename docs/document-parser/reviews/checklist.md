# Checklist: document-parser
Date: 2026-04-13 | Spec status: CLARIFIED | Model: haiku (claude-haiku-4-5-20251001)

---

## Result: ⚠️ WARN — 2 items need approval

```
Passed: 22/24 ✅  |  Blockers: 0  |  Unresolved BLOCKERs in clarify: 0
WARN-01: AGENTS.md missing — scope assignments unverifiable (low implementation risk)
WARN-02: libmagic Docker availability unconfirmed — must add Dockerfile check to /plan tasks
```

---

## Spec Quality — 7/7 ✅

- [x] Spec file exists at `docs/document-parser/spec/document-parser.spec.md`
- [x] Layer 1 summary complete — Epic, Priority, Story count, Token budget, Critical path, Parallel-safe, Blocking/Blocked-by, Agents all filled
- [x] Layer 2 stories have clear AC statements (SMART criteria)
- [x] Layer 3 sources fully mapped — 23/23 ACs traced; AC11 (G3 gap patch) traced to R007
- [x] All ACs are testable — each specifies observable behavior or error code
- [x] API contract defined for S004 (full: request, all response codes 202/413/415/422/504)
- [x] No silent assumptions — Q5–Q10 made explicit in clarify.md

---

## Architecture Alignment — 5/6 ✅, 1 ⚠️

- [x] No CONSTITUTION violations — C002/C003/C004/C009 all addressed; CONSTITUTION.md file not found but verified via WARM constraints list
- [x] No HARD rule violations — R001 N/A, R002 ✅, R003 ✅ (S004 AC2), R004 ✅ (S004 AC10), R005 ✅ (delegated to chunker), R006 ✅ (S004 AC5), R007 ✅ (AC11 timeout guard)
- [⚠️] Agent scope assignments — AGENTS.md file not found; `api-agent` / `rag-agent` consistent with ARCH.md A001 directory boundaries (WARN-01)
- [x] Dependency direction follows ARCH.md A002 — parser (rag layer) ← upload route (api layer); no reverse deps
- [x] pgvector/schema changes — N/A: no new schema; uses existing `documents` table
- [x] Auth pattern specified — API-key only (S004 AC2, inherits document-ingestion D09)

---

## Multilingual Completeness — 3/3 ✅

- [x] All 4 languages (ja/en/vi/ko) — parser is format-only; all languages served by downstream chunker pipeline (A003)
- [x] CJK tokenization strategy — S001/S002/S003 NFR + WARM: delegated to chunker
- [x] Response language behavior — N/A for upload endpoint (202 structural); query response = existing behavior

---

## Dependencies — 2/3 ✅, 1 ⚠️

- [x] Dependent specs DONE or parallel-safe — document-ingestion ✅, cjk-tokenizer ✅
- [⚠️] External contracts locked — `python-magic` requires `libmagic` system library; Docker availability unconfirmed (Q15 open) (WARN-02)
- [x] No circular story dependencies — S001 → S002/S003 (parallel) → S004

---

## Agent Readiness — 3/3 ✅ + 1 N/A

- [x] Token budget estimated — `~4k tokens` (Layer 1)
- [x] Parallel-safe stories identified — S002, S003 parallel-safe after S001
- [x] Subagent assignments — api-agent (S004), rag-agent (S001–S003)
- [N/A] Prompt caching strategy — No LLM path in this feature; parser is pure Python extraction; BackgroundTasks delegates to existing pipeline. No new LLM call introduced.

---

## WARN Items

### ⚠️ WARN-01: AGENTS.md file not found — agent scope unverifiable
Risk: Cannot confirm `api-agent` and `rag-agent` scope assignments match registry; future subagent dispatch may target wrong scope.
Mitigation: Scope assignments in spec (`api-agent` → `backend/api/`, `rag-agent` → `backend/rag/parser/`) are consistent with ARCH.md A001 directory boundaries, which are verifiable. The WARN is documentation-only risk, not implementation risk.
Approve? [x] Yes, proceed  [ ] No, resolve first

### ⚠️ WARN-02: `libmagic` Docker availability unconfirmed (Q15 — open)
Risk: `python-magic` wraps `libmagic` (C system library). If not in Docker base image, `SecurityGate` will fail at runtime with `ImportError` or missing `.so`.
Mitigation: (1) /plan must include a task to verify Docker image or add `RUN apt-get install -y libmagic1` to Dockerfile; (2) SecurityGate unit tests catch import failure early; (3) fallback: use `python-magic-bin` (bundles libmagic) if Docker change is blocked.
Approve? [x] Yes, proceed  [ ] No, resolve first

---

## Next

Both WARNs approved → proceed to `/plan document-parser`
- WARN-02 mitigation: add Dockerfile verification/update as explicit task in /plan

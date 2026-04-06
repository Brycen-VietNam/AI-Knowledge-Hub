# Sources Traceability: cjk-tokenizer
Created: 2026-04-06 | Feature spec: `docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Per-language tokenizer backends

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: MeCab for Japanese | Constitution | CONSTITUTION.md C005 | "MeCab (ja) ... no Java runtime dependency allowed" | 2026-03-18 |
| AC2: kiwipiepy for Korean | Constitution + Backlog | CONSTITUTION.md C005 + backlog.md 2026-03-18 | kiwipiepy (MIT) chosen over KoNLPy to avoid Java runtime | 2026-03-18 |
| AC3: jieba for Chinese | Constitution | CONSTITUTION.md C005 | "jieba (zh)" explicitly listed | 2026-03-18 |
| AC4: underthesea for Vietnamese | Constitution | CONSTITUTION.md C006 | "Vietnamese (vi) requires underthesea tokenizer before BM25 indexing" | 2026-03-18 |
| AC5: WhitespaceTokenizer for en only | Hard rule + Conversation | HARD.md R005 + lb_mui 2026-04-06 | Whitespace split forbidden for CJK; allowed for en and explicit fallback | 2026-04-06 |
| AC6: No Java runtime | Constitution | CONSTITUTION.md C005 | "No Java runtime dependency allowed" — design constraint | 2026-03-18 |
| AC7: BaseTokenizer ABC | Conversation | lb_mui decision 2026-04-06 | Option A selected: Factory.get(lang) pattern for testability and A001 boundary isolation | 2026-04-06 |
| AC8: Empty string → empty list | Business logic | Internal convention | Safe default; empty input to tokenizer should not raise at library level | 2026-04-06 |

### Story S002: TokenizerFactory with lazy loading

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1–AC5: Factory lang mapping (ja/ko/zh/vi/en) | Conversation | lb_mui decision 2026-04-06 | Option A agreed: TokenizerFactory.get(lang) returns singleton per lang | 2026-04-06 |
| AC6: UnsupportedLanguageError on unknown lang | Constitution | CONSTITUTION.md P005 — fail fast, fail visibly | Unknown language must not silently degrade to wrong tokenizer | 2026-04-06 |
| AC7: Lazy loading on first get() | Performance rule | PERF.md — startup cost | MeCab and kiwipiepy initialization is expensive; defer to first use | 2026-04-06 |
| AC8: Thread safety | Business logic | FastAPI async/threading model | Multiple workers share process; singleton dict without lock = race condition | 2026-04-06 |

### Story S003: Language auto-detection

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: langdetect library | Existing behavior | backend/rag/retriever.py pattern | Consistent with detection approach already established in codebase | 2026-04-06 |
| AC2: Confidence ≥ 0.85 threshold | Conversation | lb_mui decision 2026-04-06 | Option A: raise LanguageDetectionError on failure; 0.85 is default assumption | 2026-04-06 |
| AC3: LangDetectException → raise | Conversation | lb_mui decision 2026-04-06 | Option A: fail fast on detection failure | 2026-04-06 |
| AC4: LanguageDetectionError distinct class | Constitution | CONSTITUTION.md P005 | Distinct exceptions required for observability across languages/timezones | 2026-04-06 |
| AC5: 512 char truncation | Security rule | SECURITY.md S003 | "Query strings: strip control chars, limit to 512 tokens before embedding" | 2026-03-18 |
| AC6: Empty string → error | Conversation | lb_mui decision 2026-04-06 | Option A: empty input raises LanguageDetectionError, not silent empty | 2026-04-06 |

### Story S004: Tokenizer tests

| AC | Source Type | Reference | Details | Date |
|---|---|---|---|---|
| AC1: Golden examples ≥2 per lang | Constitution | CONSTITUTION.md testing policy | "AI answer quality validated via golden dataset regression suite" | 2026-03-18 |
| AC2: Factory tests all 5 langs + error | Constitution | CONSTITUTION.md testing policy | "Backend unit test coverage ≥ 80% for new code" | 2026-03-18 |
| AC3: detect_language() test coverage | Business logic | CONSTITUTION P005 — fail fast | All error paths for detection must be tested | 2026-04-06 |
| AC4: Whitespace not for CJK regression | Hard rule | HARD.md R005 | "WRONG: whitespace split on Japanese text" — explicit rule | 2026-03-18 |
| AC5: ≥80% coverage | Constitution | CONSTITUTION.md testing policy | Standard threshold for new code | 2026-03-18 |
| AC6: Performance <200ms per lang | Performance rule | PERF.md P001 — latency SLA | Tokenizer must not dominate 2000ms query budget; 200ms = ~10% budget | 2026-04-06 |

---

## Summary

**Total ACs:** 22
**Fully traced:** 22/22 ✓
**Pending sources:** 0
**Assumptions requiring /clarify:** 1 (S003 AC2 — confidence threshold 0.85)

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Constitution** | CONSTITUTION.md constraints (C001–C016), principles (P001–P008) |
| **Hard rule** | HARD.md (R001–R007), SECURITY.md (S001–S005), PERF.md (P001–P005) |
| **Backlog** | backlog.md license/architecture decisions |
| **Conversation** | lb_mui design decisions in /specify session 2026-04-06 |
| **Existing behavior** | Current codebase (retriever.py, models.py, etc.) |
| **Business logic** | Derived from system constraints + engineering judgment |

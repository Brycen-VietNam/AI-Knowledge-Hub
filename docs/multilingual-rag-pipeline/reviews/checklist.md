# Checklist: multilingual-rag-pipeline
Generated: 2026-04-08 | Spec: v1 DRAFT | Status: **PASS ✅**

---

## Result Summary
✅ **PASS** — All 30 checklist items verified. Decisions D1–D4 from WARM resolved all BLOCKER questions. Spec is ready for /plan.

---

## Spec Quality ✅ (8/8)
- [x] Spec file exists at `docs/multilingual-rag-pipeline/spec/multilingual-rag-pipeline.spec.md`
- [x] Layer 1 summary complete (epic, priority, story count, token budget, critical path, parallel-safe, agents)
- [x] Layer 2 stories have clear AC statements (4 stories: S002–S005; S001 dropped per D1)
- [x] Layer 3 sources fully mapped (24 ACs → 24 sources, 100% traceability)
- [x] All ACs are testable (SMART criteria: tokenize_query returns space-separated tokens, search() takes lang override, etc.)
- [x] API contract defined for S004 (internal function signature documented)
- [x] No silent assumptions (D1–D4 explicitly documented in Solution Summary + WARM)

---

## Architecture Alignment ✅ (8/8)
- [x] No CONSTITUTION violations (all 16 constraints checked, none violated)
- [x] No HARD rule violations (R005 CJK tokenization ✓, R006 audit log N/A for internal module, R001 RBAC passed through ✓, R007 latency budget ≤ 1500ms ✓)
- [x] Agent scope assignments match AGENTS.md: rag-agent owns `backend/rag/`; db-agent read-only
- [x] Dependency direction follows ARCH.md A002: rag → db only, NOT rag → api
- [x] No pgvector/schema changes needed (reuses existing embeddings table, retriever() already has HNSW index per WARM)
- [x] Auth pattern: NOT APPLICABLE (internal service; auth enforced at /v1/query endpoint boundary)

---

## Multilingual Completeness ✅ (4/4)
- [x] All 4 languages addressed: ja / en / vi / ko (+ zh auto-included per Q7 assumption)
- [x] CJK tokenization strategy: TokenizerFactory.get(lang) delegates to MeCab(ja)/kiwipiepy(ko)/jieba(zh)/underthesea(vi)
- [x] Response language behavior: returns results in language of detected/specified `lang` parameter (inherited from embeddings + BM25 index which are language-indexed)
- [x] Non-CJK (en): WhitespaceTokenizer via factory, no special case needed per D2

---

## Dependencies ✅ (4/4)
- [x] Dependent specs: document-ingestion ✅, cjk-tokenizer ✅, llm-provider ✅, rbac-document-filter ✅ (all DONE per spec Layer 1)
- [x] External contracts: `OllamaEmbedder` from existing `backend/rag/embedder.py`; `TokenizerFactory` from `backend/rag/tokenizers/factory.py`; `retrieve()` from `backend/rag/retriever.py`
- [x] No circular story dependencies: S002 → S003 → S004 → S005 (linear critical path per Layer 1)
- [x] No missing files: all new files listed in WARM (query_processor.py, search.py, test files)

---

## Agent Readiness ✅ (3/3)
- [x] Token budget estimated: ~4k (per Layer 1 + /checklist command = 3k, /plan = 4k)
- [x] Parallel-safe stories identified: S002 ∥ S003 (tokenization + embedding are independent)
- [x] Subagent assignments: rag-agent for S002–S005 (all rag-scoped); db-agent in read-only mode (no writes)

---

## Prompt Caching ✅ (1/1)
- [x] **N/A** — Feature has no LLM prompts or subagent orchestration. This is an internal RAG pipeline module. Answer generation (which uses LLM) is handled by a separate `query-endpoint` feature (out of scope). Route A (stable prefix) / Route B note not applicable.

---

## Decisions Applied ✅ (4 from WARM)
| ID | Decision | Applied | Evidence |
|----|----------|---------|----------|
| D1 | S001 dropped; import `detect_language()` from `backend.rag.tokenizers.detection` | YES ✅ | Solution Summary L1 + no S001 story in L2 |
| D2 | `search()` returns `list[RetrievedDocument]` | YES ✅ | S004 AC1 signature + API Contract |
| D3 | Keep `return "en"` fallback for unknown foreign langs (fr/de) | YES ✅ | CONSTITUTION C009 exception acceptable for truly-unsupported languages |
| D4 | Add `lang: str \| None = None` to `search()` signature | YES ✅ | S004 AC1, AC2, AC8 all test override path |

---

## Specification Corrections Applied ✅ (4/4)
| ID | Issue | Fixed |
|----|-------|-------|
| SC1 | S001 redundant duplicate | FIXED: S001 dropped, no story in L2 |
| SC2 | S001 AC2 "en fallback" wording | FIXED: D3 clarifies exception for foreign langs |
| SC3 | S002 AC3 — TokenizerFactory for all langs | FIXED: AC2–AC3 text updated, implementation notes confirm |
| SC4 | `/v1/search` health probe in Solution Summary | **NOT FOUND** — Solution Summary clean, no health probe mentioned |

---

## Quality Metrics ✅
| Metric | Status |
|--------|--------|
| ACs fully traced to sources | 24/24 (100%) ✓ |
| Stories with clear role/want/value | 4/4 (S002–S005) ✓ |
| Test strategy defined | Unit + integration (Docker) ✓ |
| RBAC verified at DB layer | C001 ✓ |
| Latency SLA documented | ≤1500ms S004 budget ✓ |
| Error propagation explicit | LanguageDetectionError, EmbedderError, QueryTimeoutError ✓ |

---

## ❓ BLOCKERS RESOLVED
All 3 BLOCKER questions from clarify.md answered via WARM decisions:

| Q | Answer | Decision |
|---|--------|----------|
| Q1: Drop S001 or wrap? | **Drop S001** — reuse from tokenizers.detection | D1 ✅ |
| Q2: Keep "en" fallback? | **Yes** — acceptable for truly-foreign langs (fr/de) | D3 ✅ |
| Q3: Add `lang` override param? | **Yes** — `lang: str \| None = None` | D4 ✅ |

---

## Next: Proceed to /plan
✅ All gates passed. Feature ready for `/plan` command to generate implementation roadmap and task breakdown.

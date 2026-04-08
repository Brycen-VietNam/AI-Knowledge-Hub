# WARM Memory: multilingual-rag-pipeline
Created: 2026-04-08 | Status: SPEC DRAFT | Phase: /specify complete → /clarify next

---

## Spec Summary
Wire language detection → query tokenization → query embedding → hybrid retrieval into a unified `search()` service function that the query-endpoint can call as a black box.

5 stories, 24 ACs. Priority: P0.

## Key Files (new)
| File | Story | Action |
|------|-------|--------|
| `backend/rag/query_processor.py` | S002, S003 | CREATE — `tokenize_query()` + `embed_query()` |
| `backend/rag/search.py` | S004 | CREATE — `search()` public interface |
| `tests/rag/test_query_processor.py` | S002, S003 | CREATE |
| `tests/rag/test_search.py` | S004, S005 | CREATE |

## Key Files (existing — read only)
| File | Role |
|------|------|
| `backend/rag/retriever.py` | Called by search() — retrieve() + RetrievedDocument |
| `backend/rag/embedder.py` | Called by embed_query() — OllamaEmbedder |
| `backend/rag/bm25_indexer.py` | Tokenization pattern reference — tokenize_for_fts() |
| `backend/rag/tokenizers/factory.py` | Called by tokenize_query() — TokenizerFactory |

## Decisions
- D1 (2026-04-08): S001 dropped — `detect_language()` reused from `backend.rag.tokenizers.detection`. `search.py` imports directly. No new file created.
- D2 (2026-04-08): `tokenize_query()` uses `TokenizerFactory.get(lang)` for ALL langs (including "en") — no special-case whitespace split needed.
- D3 (2026-04-08): Q2 resolved — `return "en"` for unknown foreign langs (fr/de) kept as-is. Latin langs use whitespace path correctly; label mismatch acceptable for P0.
- D4 (2026-04-08): Q3 resolved — `search()` signature adds `lang: str | None = None`. None → auto-detect. Provided → skip detection, validate against `_SUPPORTED`, raise `UnsupportedLanguageError` if invalid.

## Sync: 2026-04-08 (session #029)
Decisions added: D1, D2, D3, D4
Tasks changed: /specify→DONE, /clarify→DONE
Files touched: spec.md (4 SC corrections), clarify.md created, WARM updated, HOT updated
Questions resolved: Q1, Q2, Q3
New blockers: none

## Open Questions
_All resolved ✅_
- Q1: Drop S001, import from `tokenizers.detection` ✅ (D1)
- Q2: Keep `return "en"` for unknown foreign langs ✅ (D3)
- Q3: Add `lang: str | None = None` to `search()` ✅ (D4)

## Auto-Answered
- OQ3 resolved: `langdetect` confirmed — already in use (`DetectorFactory.seed=0`)
- OQ1-fallback resolved: hard-fail (default assumption Q4) unless lb_mui overrides
- `LanguageDetectionError` + `UnsupportedLanguageError` already defined in `tokenizers/exceptions.py`
- `TokenizerFactory` handles "en" via `WhitespaceTokenizer` — no special-case needed

## Spec Corrections Needed (before /plan)
- SC1: S001 may be dropped/replaced — depends on Q1
- SC2: S001 AC2 "en fallback" wording — depends on Q2
- SC3: S002 AC3 — update to use factory for all langs (not whitespace special-case)
- SC4: Remove `/v1/search` health-probe from Solution Summary — not in any story, violates R003

## Assumptions
- A1: `langdetect` confirmed ✅
- A2: `search()` returns `list[RetrievedDocument]` — query-endpoint maps to HTTP response
- A3 (new): `tokenize_query()` delegates ALL langs to `TokenizerFactory.get(lang)` uniformly

## Status by Phase
| Phase | Status |
|-------|--------|
| /specify | DONE ✅ 2026-04-08 |
| /clarify | DONE ✅ 2026-04-08 |
| /checklist | DONE ✅ 2026-04-08 — PASS (all 30 items) |
| /plan | DONE ✅ 2026-04-08 — multilingual-rag-pipeline.plan.md |
| /tasks | DONE ✅ 2026-04-08 — S002–S005.tasks.md (7 tasks, TDD workflow) |
| /analyze | DONE ✅ 2026-04-08 — S002–S005.analysis.md (no conflicts, 100% confidence) |
| /implement | → NEXT |
| /reviewcode | — |
| /report | — |

## Implementation Readiness
**All gates CLEAR** ✅
- ✅ Spec: DRAFT (v1), all 24 ACs defined
- ✅ Checklist: PASS (30/30 items verified)
- ✅ Plan: Layer 1+2 complete (critical path: S002→S003→S004→S005, G1 parallel: S002∥S003)
- ✅ Tasks: 7 atomic tasks (2 per S002–S003, 3 per S004, 2 per S005)
- ✅ Analysis: 0 conflicts, 0 missing dependencies, 0 security issues
- ✅ TDD workflow: test-first for all tasks

## Implementation Plan
**Parallel Group G1** (can run concurrently):
- S002 (T001→T002): Query tokenization via TokenizerFactory
- S003 (T001→T002): Query embedding via OllamaEmbedder singleton

**Sequential Group G2** (after G1 complete):
- S004 (T001→T002→T003): Unified search() service + unit + integration tests
- S005 (T001→T002): Docker integration validation + coverage check

## Key Implementation Patterns (from analysis)
| Item | Pattern | Location |
|------|---------|----------|
| TokenizerFactory usage | Delegate to factory.get(lang) for all langs | S002 |
| OllamaEmbedder singleton | Module-level _embedder = OllamaEmbedder() | S003 |
| Orchestration (search) | Detect/validate lang → tokenize → embed → retrieve | S004 |
| Error propagation | All errors bubble up (no try-except swallowing) | All |
| RBAC pass-through | user_group_ids passed unchanged to retrieve() | S004 |
| Integration test | Docker fixture reuse + @pytest.mark.integration | S005 |

## Sync: 2026-04-08 (session #031)
Decisions applied: D1–D4 (all from prior syncs)
Tasks: /analyze→DONE (4 stories, 7 tasks, 0 conflicts detected)
Files: S002–S005.analysis.md created
Confidence: All rules (R001, R005, R007, A001–A003) validated ✅
Next: /implement G1 (S002 ∥ S003) or proceed directly to S002-T001

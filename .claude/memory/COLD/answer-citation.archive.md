# Feature Memory: answer-citation
> Created by /specify. Updated after each SDD phase. Loaded only when working on this feature.

Status: REVIEWED ✅ S001–S005 — APPROVED (3 warnings, 0 blockers)
Updated: 2026-04-15 (session #055)

---

## Summary (5 bullets max — always current)
- Enriches `/v1/query` response with `citations: list[CitationObject]` alongside existing `sources: list[str]` (Option C — additive, no breaking change)
- Requires DB migration 007: `ALTER TABLE documents ADD COLUMN source_url TEXT NULL`
- `_dense_search()` needs INNER JOIN to `documents`; `_bm25_search()` already queries `documents` — both must SELECT `title, lang, source_url`
- LLM prompt changed from raw `{context}` to numbered `[N] title\nchunk` index with explicit `[N]` marker instruction; graceful fallback if model omits markers
- `generate_answer()` and `LLMProvider.complete()` signatures extended with `doc_titles: list[str]`

## Key Decisions
| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D-CIT-01 | Option C (additive) — add `citations` alongside `sources` | Zero client breakage; opt-in for new consumers | 2026-04-14 |
| D-CIT-02 | `source_url` column requires migration 007 — does not exist in schema | NULL nullable — zero downtime migration | 2026-04-14 |
| D-CIT-03 | No score filter on `citations` — mirrors `sources` exactly | Consumers decide what to display; no asymmetry | 2026-04-14 |
| D-CIT-04 | Marker index is 1-based; `citations` array is 0-indexed (`[N]` → `citations[N-1]`) | Natural language convention | 2026-04-14 |
| D-CIT-05 | API layer builds CitationObject from RetrievedDocument, NOT from LLM output | Trust retrieval pipeline data, not model-generated structured data | 2026-04-14 |
| D-CIT-06 | `source_url NULL` acceptable at launch — plain-text title rendered for existing docs | Option A: populate incrementally via PATCH; no retroactive backfill | 2026-04-14 |
| D-CIT-07 | Q2 (consumer strict parsing) N/A — consumers not yet implemented. S004 AC9 mandates permissive JSON parsing in rendering contract | Constraint enforced at contract level, not at API level | 2026-04-14 |
| D-CIT-08 | Graceful fallback sufficient for v1 — no minimum marker rate. Monitor `inline_markers_present` post-launch | Hard gate deferred until 1 sprint of metrics available | 2026-04-14 |
| D-CIT-09 | Delete `LLMResponse.sources: list[str]` in S003-T001 | Dead field — chunk TEXT content, never used by `query.py`; external API `sources` unaffected | 2026-04-14 |

## Spec
Path: `docs/answer-citation/spec/answer-citation.spec.md`
Stories: 5 | Priority: P1
Sources: `docs/answer-citation/sources/answer-citation.sources.md`

## Plan
Path: `docs/answer-citation/plan/answer-citation.plan.md`
Critical path: S001 → S002 → S003 → S005 (S004 ‖ S003)

## Task Progress
| Task | Story | Status | Agent | Notes |
|------|-------|--------|-------|-------|
| T001–T005 | S001 | DONE ✅ | db-agent | G1 — 5 tasks; migration 007 + ORM + RetrievedDocument + retriever JOIN |
| T001–T003 | S002 | DONE ✅ | api-agent | G2 — 3 tasks; 5/5 tests pass; file: `docs/answer-citation/tasks/S002.tasks.md` |
| T001–T006 | S003 | DONE ✅ | rag-agent | G3 — 6 tasks; 96/96 tests pass; file: `docs/answer-citation/tasks/S003.tasks.md` |
| T001–T002 | S004 | DONE ✅ | api-agent | G3 — 2 tasks; citation-rendering-contract.md + api-reference.md updated |
| T001–T005 | S005 | DONE ✅ | api-agent | G4 — 5 tasks; 80/80 pass; citation.py 100%, query.py 92%, generator.py 100%, retriever.py 91% |

## Files Touched
- `docs/answer-citation/reviews/checklist.md` (CREATED — /checklist output)
- `docs/answer-citation/plan/answer-citation.plan.md` (CREATED — /plan output)
- `backend/api/models/__init__.py` (CREATED — S002-T001)
- `backend/api/models/citation.py` (CREATED — S002-T001: CitationObject)
- `backend/api/routes/query.py` (MODIFIED — S002-T002: citations field + populate; S003-T006: content_docs + doc_titles)
- `backend/rag/llm/base.py` (MODIFIED — S003-T001: delete sources, add inline_markers_present; T002: abstract signature +doc_titles)
- `backend/rag/llm/prompts/answer.txt` (MODIFIED — S003-T003: {context}→{sources_index}, [N] marker instruction)
- `backend/rag/llm/ollama.py` (MODIFIED — S003-T004: doc_titles, sources_index, inline_markers_present)
- `backend/rag/llm/openai.py` (MODIFIED — S003-T005: same pattern)
- `backend/rag/llm/claude.py` (MODIFIED — S003-T006: same pattern)
- `backend/rag/generator.py` (MODIFIED — S003-T006: doc_titles param added)
- `tests/rag/test_llm_provider.py` (MODIFIED — S003: remove sources=, add doc_titles, inline_markers_present assertions)
- `tests/rag/test_generator.py` (MODIFIED — S003: remove sources=, add doc_titles)
- `tests/api/test_query.py` (MODIFIED — S003: remove sources= from all LLMResponse constructors)
- `tests/api/test_query_rbac.py` (MODIFIED — S003: same)
- `tests/api/test_rate_limiter.py` (MODIFIED — S003: same)
- `tests/api/test_query_route.py` (MODIFIED — S003: same)
- `tests/api/test_citation.py` (MODIFIED — S003: same; S005-T001: +AC9, +AC11 → 7 tests total)
- `tests/api/test_query.py` (MODIFIED — S005-T002: +3 tests AC9–AC11 integration)
- `tests/rag/test_generator.py` (MODIFIED — S005-T003: +7 tests AC5a/5b/6 doc_titles/6 CJK×5/GAP-2)
- `tests/rag/test_retriever_rbac.py` (MODIFIED — S005-T004: +test_retrieved_document_enrichment)

## Open Questions
| # | Question | Owner | Due |
|---|----------|-------|-----|
| ~~Q1~~ | ~~A01: Is `source_url NULL` acceptable?~~ | ✅ Resolved — Option A accepted | 2026-04-14 |
| ~~Q2~~ | ~~A04: Consumer lenient JSON parsing?~~ | ✅ Resolved — consumers not yet built; constraint in S004 AC9 | 2026-04-14 |
| ~~Q3~~ | ~~A03: Graceful fallback sufficient?~~ | ✅ Resolved — yes for v1; monitor post-launch | 2026-04-14 |

## CONSTITUTION Violations Found
_None — updated by /checklist or /rules._

---

## Implementation Gaps & Deferred Items
> Phát hiện qua so sánh commit `80f2c59` vs spec hiện tại (session #048, 2026-04-14)

### GAP-1 — `LLMResponse.sources` là dead field ✅ RESOLVED
- **File:** `backend/rag/llm/base.py` + tất cả adapters
- **Quyết định:** **XÓA** `LLMResponse.sources` — confirmed lb_mui 2026-04-14
- **S003-T001 action:** Remove `sources: list[str]` from `LLMResponse` dataclass; remove `sources=[...]` from all 3 adapter `LLMResponse(...)` constructor calls; update any test asserting `.sources` on `LLMResponse`
- **Không ảnh hưởng:** External API `sources` field trong `/v1/query` response — đến từ retriever, không từ `LLMResponse`

### GAP-2 — S005 thiếu test out-of-range marker
- **Vấn đề:** Không có test xác nhận API trả 200 bình thường khi LLM emit `[99]` nhưng `citations` chỉ có 3 phần tử. Consumer contract (S004 AC2) nói render plain text — nhưng API side chưa có test coverage.
- **Hành động:** Thêm `test_oob_marker_in_answer` vào S005 khi chạy /tasks S005. AC nhỏ, không cần sửa spec chính thức.

### BACKLOG-1 — `cited` flag per source (feature `citation-quality`)
- **Nguồn:** commit `80f2c59` S002 — `CitedSource.cited: bool` phân biệt doc được LLM cite vs chỉ retrieved
- **Yêu cầu:** Parser `_parse_citations(answer, num_docs) -> set[int]` sau LLM response
- **Tại sao defer:** D-CIT-03 đã chốt `citations` mirrors `sources` (confirmed lb_mui); thay đổi sẽ phá contract
- **Khi nào làm:** Sau /report answer-citation, tạo feature `citation-quality`

### BACKLOG-2 — Confidence scoring fix (feature `confidence-scoring`)
- **Nguồn:** commit `80f2c59` S003 — fix sentinel `0.9` cứng trong Ollama + Claude adapters
- **Vấn đề thực:** `low_confidence` **không bao giờ trigger** với Ollama (`ollama.py:49`) và Claude (`claude.py:46`); OpenAI chỉ đúng khi logprobs available
- **Formula đề xuất:** `cited_ratio * 0.8 + 0.2` (cần validate với team)
- **Files:** `backend/rag/llm/ollama.py:49`, `backend/rag/llm/claude.py:46`, `backend/rag/llm/openai.py:50`
- **Khi nào làm:** Sau /report answer-citation, tạo feature `confidence-scoring`

---

## Sync: 2026-04-15 (session #055)
Decisions added: none (review only — no new D-series)
Tasks changed: all S001–S005 stories → REVIEWED ✅
Files touched:
  - docs/answer-citation/reviews/answer-citation.review.md (CREATED — /reviewcode output, APPROVED)
  - .claude/memory/HOT.md (UPDATED — status → REVIEWED, Recent Decisions, Next Session Start)
  - .claude/memory/WARM/answer-citation.mem.md (UPDATED — status REVIEWED)
Questions resolved: none
New blockers: none
Review result: APPROVED — 0 blockers, 3 warnings:
  W1: retrieve() sequential dense+BM25 missing comment (latency risk near 1000ms budget)
  W2: sources=[doc_id UUIDs] — confirm this is intended API contract vs prior text content
  W3: confidence sentinel 0.9 hardcoded Ollama/Claude — tracked BACKLOG-2, OK to defer

## Sync: 2026-04-15 (session #054)
Decisions added: none (S005 execution only — no new D-series)
Tasks changed: S005 T001→DONE, T002→DONE, T003→DONE, T004→DONE, T005→DONE; S005 story → DONE ✅
Files touched:
  - tests/api/test_citation.py (MODIFIED — S005-T001: +AC9 backward_compat_sources_present, +AC11 score_rounded_to_4dp → 7 tests total)
  - tests/api/test_query.py (MODIFIED — S005-T002: +test_query_response_has_citations_and_sources, +test_query_response_citations_not_null, +test_query_response_citation_fields_complete)
  - tests/rag/test_generator.py (MODIFIED — S005-T003: +inline_markers_present, +inline_markers_fallback, +doc_titles_passed_to_adapter, +cjk_answer_language[ja/en/vi/ko/zh], +oob_marker_in_answer [GAP-2])
  - tests/rag/test_retriever_rbac.py (MODIFIED — S005-T004: +test_retrieved_document_enrichment consolidated)
  - docs/answer-citation/tasks/S005.tasks.md (UPDATED — all tasks → DONE ✅)
  - .claude/memory/HOT.md (UPDATED — S005 DONE, next → /report)
  - .claude/memory/WARM/answer-citation.mem.md (UPDATED — status ALL DONE, task board, files touched)
Questions resolved: GAP-2 (OOB marker test added — confirmed no API change needed, graceful by design)
New blockers: none
Coverage results: citation.py 100% ✅ | query.py 92% ✅ | generator.py 100% ✅ | retriever.py 91% ✅
Test result: 80 passed, 10 skipped (DB integration — expected), 0 failed

## Sync: 2026-04-14 (session #050)
Decisions added: none
Tasks changed: all stories status → ANALYSIS COMPLETE (analysis file covers all 5 stories)
Files touched:
  - docs/answer-citation/tasks/all-stories.analysis.md (CREATED — /analyze output, all stories)
  - .claude/memory/HOT.md (updated: In Progress status, Recent Decisions, Next Session Start)
Questions resolved: none
New blockers: none
Analysis risks captured:
  - ❌ {context}→{sources_index} rename: atomic across T003+T004+T005+T006 (KeyError if partial)
  - ❌ LLMResponse.sources delete: atomic across base.py + 3 adapter sites in S003-T001
  - ⚠️ doc_titles/chunks index alignment: must derive from same `content_docs` filtered list in query.py
  - ⚠️ backend/api/models/ is empty — create __init__.py in S002-T001
  - ⚠️ _bm25_search chunk_index=0 hardcoded (intentional) — AC12 test should assert >=0

## Sync: 2026-04-14 (session #049)
Decisions added: D-CIT-09 (xóa LLMResponse.sources — confirmed lb_mui)
Tasks changed: all 5 stories → TODO (task files created); S003-T001 unblocked
Files touched:
  - docs/answer-citation/tasks/S001.tasks.md (CREATED — 5 tasks, db-agent)
  - docs/answer-citation/tasks/S002.tasks.md (CREATED — 3 tasks, api-agent)
  - docs/answer-citation/tasks/S003.tasks.md (CREATED — 6 tasks, rag-agent)
  - docs/answer-citation/tasks/S004.tasks.md (CREATED — 2 tasks, api-agent)
  - docs/answer-citation/tasks/S005.tasks.md (CREATED — 5 tasks, api-agent)
  - .claude/memory/WARM/answer-citation.mem.md (updated: D-CIT-09, GAP-1 resolved, task progress board)
  - .claude/memory/HOT.md (updated: In Progress, Recent Decisions, Active Blockers cleared, Next Session)
Questions resolved: GAP-1 (LLMResponse.sources → xóa)
New blockers: none

## Sync: 2026-04-14 (session #048)
Decisions added: none
Tasks changed: none
Files touched:
  - .claude/memory/WARM/answer-citation.mem.md (updated: GAP-1, GAP-2, BACKLOG-1, BACKLOG-2 added)
  - .claude/memory/HOT.md (updated: Active Blockers, Deferred Features, Next Session Start)
Questions resolved: none
New blockers: DECISION PENDING — `LLMResponse.sources` dead field (GAP-1), needed before S003 /tasks

## Sync: 2026-04-14 (session #047)
Decisions added: none (plan generation only — no new D-series)
Tasks changed: all 5 stories → pending /tasks (S001 db-agent, S002 api-agent, S003 rag-agent, S004 api-agent, S005 api-agent)
Files touched:
  - docs/answer-citation/plan/answer-citation.plan.md (CREATED — /plan output, Layer 1 + Layer 2)
  - .claude/memory/HOT.md (updated: status → PLAN COMPLETE, Recent Decisions, Next Session Start)
  - .claude/memory/WARM/answer-citation.mem.md (updated: status, task progress, files touched)
Questions resolved: none
New blockers: none (WARN lang-nullability carried into S001 task scope — no new blockers)

## Sync: 2026-04-14 (session #046)
Decisions added: none (checklist validation only)
Tasks changed: none (/plan not yet run)
Files touched:
  - docs/answer-citation/reviews/checklist.md (CREATED — 29/30 PASS, 1 WARN)
  - .claude/memory/HOT.md (updated: status → CHECKLIST PASS, Recent Decisions, Next Session Start)
  - .claude/memory/WARM/answer-citation.mem.md (updated: status, files touched)
Questions resolved: none
New blockers: WARN — `documents.lang` nullability not pre-verified. Mitigation: pre-migration `SELECT COUNT(*) FROM documents WHERE lang IS NULL`; add `d.lang or "und"` fallback if any rows found. Pending lb_mui approval before /plan.

## Sync: 2026-04-14 (session #045)
Decisions added: D-CIT-06, D-CIT-07, D-CIT-08
Tasks changed: none (/plan not yet run)
Files touched:
  - docs/answer-citation/clarify/answer-citation.clarify.md (CREATED)
  - docs/answer-citation/spec/answer-citation.spec.md (updated: S004 AC9 added)
  - .claude/memory/WARM/answer-citation.mem.md (updated: decisions, questions resolved, status)
  - .claude/memory/HOT.md (updated: In Progress → CLARIFIED, Recent Decisions, Next Session Start)
  - .claude/memory/feedback_api_additive_consumer_contract.md (CREATED)
Questions resolved: Q1 (source_url NULL ok), Q2 (consumers not built → contract AC), Q3 (graceful fallback ok)
New blockers: none

## Sync: 2026-04-14 (session #044)
Decisions added: D-CIT-01, D-CIT-02, D-CIT-03, D-CIT-04, D-CIT-05
Tasks changed: none (/plan not yet run)
Files touched:
  - docs/answer-citation/spec/answer-citation.spec.md (CREATED)
  - docs/answer-citation/sources/answer-citation.sources.md (CREATED)
  - .claude/memory/WARM/answer-citation.mem.md (CREATED)
  - .claude/memory/HOT.md (updated: In Progress, Recent Decisions, Next Session Start)
Questions resolved: A05 (no score filter — confirmed lb_mui), A06 (title NOT NULL — confirmed ORM)
New blockers: none

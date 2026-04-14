# Plan: answer-citation
Created: 2026-04-14 | Based on spec: v1 | Checklist: PASS (29/30, 1 WARN — lang nullability, pre-mitigated in S001)

---

## LAYER 1 — Plan Summary
> Load this section for sprint planning and status reviews.

| Field | Value |
|-------|-------|
| Total stories | 5 |
| Sessions estimated | 2 |
| Critical path | S001 → S002 → S003 → S005 |
| Token budget total | ~5k tokens |

### Parallel Execution Groups
```
G1 (start immediately):
  S001 — db-agent    — DB migration + RetrievedDocument enrichment

G2 (after G1 complete):
  S002 — api-agent   — CitationObject model + QueryResponse extension

G3 (after G2, run together):
  S003 — rag-agent   — LLM prompt engineering for inline [N] markers
  S004 — api-agent   — Consumer rendering contract (documentation only)

G4 (after G3 complete):
  S005 — api-agent   — Tests and coverage
```

### Agent Assignments
| Agent | Stories | Can start |
|-------|---------|-----------|
| db-agent | S001 | immediately |
| api-agent | S002, S004, S005 | S002 after S001; S004 after S002 (parallel with S003); S005 after S003 |
| rag-agent | S003 | after S002 |

### Risk
| Risk | Mitigation |
|------|------------|
| `documents.lang` NULL for legacy rows | S001 must run `SELECT COUNT(*) FROM documents WHERE lang IS NULL` pre-migration; apply `d.lang or "und"` fallback if > 0 |
| LLM `[N]` marker compliance | AC5 fallback: return answer as-is with citations still populated; no re-prompt, no error |
| Dense search JOIN overhead | INNER JOIN on `documents.id` PK index (nested loop) — expected < 5ms p95; within 1.0s retrieval timeout |
| Prompt token budget | New prompt is ~80–120 tokens longer; well within all three model context windows; LLM timeout unchanged |

---

## LAYER 2 — Story Plans
> Load one story at a time during /tasks phase.

---

### S001: DB Migration + RetrievedDocument Enrichment
**Agent**: db-agent
**Parallel group**: G1
**Depends on**: none

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/db/migrations/007_add_source_url.sql` |
| MODIFY | `backend/db/models/document.py` — add `source_url` ORM field |
| MODIFY | `backend/rag/retriever.py` — enrich `_dense_search`, `_bm25_search`, `_merge` |
| MODIFY | `backend/rag/models.py` (or wherever `RetrievedDocument` is defined) — add 3 optional fields |

**Subagent dispatch**: YES (self-contained DB + retrieval layer)
**Est. tokens**: ~1.5k
**Test entry**: `pytest tests/rag/test_retriever_rbac.py -k "enrichment"`

**Story-specific notes**
- Migration 007 is zero-downtime: adding nullable column with no default/constraint is safe in PostgreSQL.
- `_bm25_search` already JOINs `documents d` — only need to add 3 SELECT columns. No structural change.
- `_dense_search` needs `INNER JOIN documents d ON d.id = e.doc_id` added. Verify FK: `embeddings.doc_id` → `documents.id`.
- WARN mitigation: Before running migration, include pre-check task: `SELECT COUNT(*) FROM documents WHERE lang IS NULL`. If count > 0, apply `d.lang or "und"` fallback in `RetrievedDocument` construction.
- `RetrievedDocument` new fields all have `= None` defaults — no existing callers break.

**Outputs expected**
- [ ] `backend/db/migrations/007_add_source_url.sql` with rollback section
- [ ] `Document` ORM: `source_url: Mapped[str | None]`
- [ ] `RetrievedDocument`: 3 new optional fields (`title`, `source_url`, `lang`)
- [ ] `_dense_search`: JOIN + 3 new SELECT columns
- [ ] `_bm25_search`: 3 new SELECT columns
- [ ] `_merge`: fields propagated via `**vars()` spread (no code change if spread is already generic)
- [ ] AC7: no new SQL queries per `search()` call
- [ ] Tests extended: `test_retriever_rbac.py` AC12

---

### S002: CitationObject Model + QueryResponse Extension
**Agent**: api-agent
**Parallel group**: G2
**Depends on**: S001 (RetrievedDocument must have title/lang/source_url)

**Files**
| Action | Path |
|--------|------|
| CREATE | `backend/api/models/citation.py` — `CitationObject` Pydantic model |
| MODIFY | `backend/api/routes/query.py` — add `citations` field to `QueryResponse`, populate from `docs` list |

**Subagent dispatch**: YES (self-contained API model layer)
**Est. tokens**: ~1k
**Test entry**: `pytest tests/api/test_citation.py`

**Story-specific notes**
- `CitationObject` fields (from spec): `doc_id: str`, `title: str`, `source_url: str | None`, `chunk_index: int`, `score: float`, `lang: str`
- `QueryResponse` gains `citations: list[CitationObject] = Field(default_factory=list)`. `sources: list[str]` is NOT touched.
- Build call site: `citations=[CitationObject(doc_id=str(d.doc_id), title=d.title or "", source_url=d.source_url, chunk_index=d.chunk_index, score=round(d.score, 4), lang=d.lang or "") for d in docs]`
- `citations = []` on NoRelevantChunksError / null answer path. Never null — always serialized as `[]`.
- `score` rounded to 4dp. Ordering inherits from `_merge()` — hybrid score descending, matching `sources`.
- R002: no user_id, user_group_id, chunk text, email, IP in CitationObject.

**Outputs expected**
- [ ] `backend/api/models/citation.py` (new file, 100% coverage target)
- [ ] `QueryResponse` with `citations` field — additive only
- [ ] `sources` field unchanged
- [ ] `citations: []` on null-answer path
- [ ] Tests: AC1–AC4, AC10 in `tests/api/test_citation.py`

---

### S003: LLM Prompt Engineering for Inline Citation Markers
**Agent**: rag-agent
**Parallel group**: G3 (parallel with S004)
**Depends on**: S002 (CitationObject established; adapter signature change follows query.py contract)

**Files**
| Action | Path |
|--------|------|
| MODIFY | `backend/rag/generator.py` — extend `generate_answer()` to accept `doc_titles: list[str]` |
| MODIFY | `backend/rag/llm/base.py` — extend `LLMProvider.complete()` abstract method |
| MODIFY | `backend/rag/llm/ollama_adapter.py` — implement updated `complete()` signature |
| MODIFY | `backend/rag/llm/openai_adapter.py` — implement updated `complete()` signature |
| MODIFY | `backend/rag/llm/claude_adapter.py` — implement updated `complete()` signature |
| MODIFY | `backend/rag/llm/prompts/answer.txt` — new numbered-index template |
| MODIFY | `backend/rag/models.py` (or `backend/rag/llm/models.py`) — add `inline_markers_present: bool = False` to `LLMResponse` |
| MODIFY | `backend/api/routes/query.py` — pass `doc_titles=[d.title or "" for d in docs if d.content]` |

**Subagent dispatch**: YES (rag-agent scope — generator + adapters)
**Est. tokens**: ~1.5k
**Test entry**: `pytest tests/rag/test_generator.py`

**Story-specific notes**
- All 3 adapters must update `complete()` — no adapter may skip `doc_titles` parameter.
- Numbered index format: `[1] {title_1}\n{chunk_text_1}\n\n[2] {title_2}\n{chunk_text_2}`
- Prompt template is fully authoritative — paste verbatim from spec AC3. No paraphrasing.
- Fallback (AC5): if no `\[\d+\]` match in response → return answer as-is, set `inline_markers_present = False`. No error.
- `inline_markers_present` is observability only — does NOT affect `citations` population or business logic.
- Prompt caching (ClaudeAdapter): stable prefix through `Sources:` line. `{sources_index}` + `{question}` are volatile suffix (Route A compliant per spec NF).
- CJK: prompt instruction is in English; model answers in question language. AC6 covers ja/en/vi/ko/zh.

**Outputs expected**
- [ ] `generate_answer()` signature updated with `doc_titles`
- [ ] `LLMProvider.complete()` abstract signature updated
- [ ] All 3 adapter `complete()` implementations updated
- [ ] `backend/rag/llm/prompts/answer.txt` — new template (verbatim from spec)
- [ ] `LLMResponse.inline_markers_present: bool = False`
- [ ] `query.py` call site passes `doc_titles`
- [ ] Tests: AC5–AC8 in `tests/rag/test_generator.py`

---

### S004: Consumer Rendering Contract (Documentation)
**Agent**: api-agent
**Parallel group**: G3 (parallel with S003 — no shared files)
**Depends on**: S002 (CitationObject API contract must be final)

**Files**
| Action | Path |
|--------|------|
| CREATE | `docs/answer-citation/citation-rendering-contract.md` |
| MODIFY | `docs/query-endpoint/api-reference.md` — add link to rendering contract |

**Subagent dispatch**: NO (documentation — inline with api-agent during G3)
**Est. tokens**: ~0.5k
**Test entry**: N/A (documentation only)

**Story-specific notes**
- Document must have `Contract-Version: 1.0` header (AC1).
- Must cover all 9 ACs from spec: `[N]` → `citations[N-1]` (0-indexed), OOB → plain text, low_confidence warning, source_url null handling, ordering guarantee, empty-citations behavior, backward compat guarantee, lenient JSON parsing requirement.
- No code changes. No auth. No tests.
- Link format for `api-reference.md`: `See [Citation Rendering Contract](../answer-citation/citation-rendering-contract.md)`.

**Outputs expected**
- [ ] `docs/answer-citation/citation-rendering-contract.md` with `Contract-Version: 1.0`
- [ ] All 9 AC behaviors documented
- [ ] Link added to `docs/query-endpoint/api-reference.md`

---

### S005: Tests and Coverage
**Agent**: api-agent
**Parallel group**: G4
**Depends on**: S003 (all implementation complete before writing integration tests)

**Files**
| Action | Path |
|--------|------|
| CREATE | `tests/api/test_citation.py` — new test file (AC1–AC4, AC9–AC11) |
| MODIFY | `tests/api/test_query.py` — extend with integration ACs (AC9–AC11) |
| MODIFY | `tests/rag/test_generator.py` — extend with AC5–AC8 |
| MODIFY | `tests/rag/test_retriever_rbac.py` — extend with AC12 |

**Subagent dispatch**: YES (can be dispatched after G3 gate)
**Est. tokens**: ~1k
**Test entry**: `pytest tests/api/test_citation.py tests/api/test_query.py tests/rag/test_generator.py tests/rag/test_retriever_rbac.py -v`

**Story-specific notes**
- AC1–AC12 map 1:1 to test functions. Test naming: `test_citation_object_construction`, `test_citation_object_no_source_url`, etc. (exact names from spec).
- AC13 coverage thresholds: `citation.py` 100%, `query.py` ≥80% (no regression), `generator.py` ≥80%, `retriever.py` ≥80%.
- AC6 is parametrized: `@pytest.mark.parametrize("lang", ["ja", "en", "vi", "ko", "zh"])`.
- Use existing auth fixtures from `test_query.py` — no new auth setup.
- Mock boundaries: `search()` mocked for API-layer tests; DB mocked for retriever unit tests; adapter mocked for generator tests.

**Outputs expected**
- [ ] `tests/api/test_citation.py` (new — AC1–AC4, AC9–AC11)
- [ ] `test_query.py` extended (AC9–AC11)
- [ ] `test_generator.py` extended (AC5–AC8)
- [ ] `test_retriever_rbac.py` extended (AC12)
- [ ] Coverage thresholds met per AC13
- [ ] All tests pass: `pytest` exit 0

---

## Checklist Gate Reference
- Checklist: `docs/answer-citation/reviews/checklist.md` — PASS (29/30)
- WARN: `documents.lang` nullability — mitigated in S001 pre-migration check + `d.lang or "und"` fallback
- No unresolved BLOCKERs

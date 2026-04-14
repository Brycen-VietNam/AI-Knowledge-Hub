# Sources Traceability: answer-citation
Created: 2026-04-14 | Feature spec: `docs/answer-citation/spec/answer-citation.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: DB Migration + RetrievedDocument Enrichment

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: migration 007 | Constitution | CONSTITUTION.md C014 | "AI answers must cite ≥1 source with confidence ≥0.4" — `source_url` column required for CitationObject | 2026-03-18 |
| AC2: ORM field | Existing behavior | `backend/db/models/document.py:19–25` | `Document` model has no `source_url` field today | 2026-04-14 |
| AC3: RetrievedDocument extension | Existing behavior | `backend/rag/retriever.py:23–29` | `RetrievedDocument` dataclass has `doc_id, chunk_index, score, user_group_id, content` only | 2026-04-14 |
| AC4: dense JOIN | Existing behavior | `backend/rag/retriever.py:41–63` | `_dense_search` queries `embeddings e` only — no JOIN to `documents` | 2026-04-14 |
| AC5: BM25 select | Existing behavior | `backend/rag/retriever.py:66–97` | `_bm25_search` queries `documents d` — `d.title, d.lang` available but not selected | 2026-04-14 |
| AC6: merge spread | Existing behavior | `backend/rag/retriever.py:114` | `**vars(all_docs[did])` spread naturally carries new dataclass fields | 2026-04-14 |
| AC7: no extra queries | Requirement doc | `PERF.md P001, HARD.md R007` | `/v1/query` p95 < 2000ms — no additional SQL round-trips permitted | 2026-04-14 |
| AC8: R002 compliance | Requirement doc | `HARD.md R002` | "pgvector embedding metadata must only contain: doc_id, lang, user_group_id, created_at" — no PII | 2026-04-14 |

### Story S002: CitationObject Model + QueryResponse Extension

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: CitationObject model | Constitution | CONSTITUTION.md C014 | Source citation mandate drives CitationObject design | 2026-03-18 |
| AC2: additive Option C | Conversation | lb_mui, /specify session | Chose Option C (add `citations` alongside `sources`) to avoid breaking existing clients | 2026-04-14 |
| AC3: ordering matches sources | Existing behavior | `backend/rag/retriever.py:100–116` | `_merge()` returns docs ordered by hybrid score descending | 2026-04-14 |
| AC4: no score filter | Conversation | lb_mui, /specify session | `citations` mirrors `sources` exactly — consumers decide what to display | 2026-04-14 |
| AC5: empty on null answer | Existing behavior | `backend/api/routes/query.py` | `NoRelevantChunksError` path returns `{answer: null, reason: "no_relevant_chunks"}` | 2026-04-14 |
| AC6: score rounded to 4dp | Business logic | SDD convention | Avoids floating-point noise in JSON serialization | 2026-04-14 |
| AC7: source_url nullable | Requirement doc | Migration 007 (S001 AC1) | `source_url` is nullable — null until ingestion pipeline populates it | 2026-04-14 |
| AC8: lang never null | Existing behavior | `backend/db/models/document.py:20` | `lang: Mapped[str] = mapped_column(CHAR(2), nullable=False)` | 2026-04-14 |
| AC9: R002 no PII | Requirement doc | `HARD.md R002` | No user_id, user_group_id, content, email, IP in citation objects | 2026-04-14 |
| AC10: citations not omitted | Business logic | SDD convention | Consistent schema — empty array preferred over absent key for consumers | 2026-04-14 |

### Story S003: LLM Prompt Engineering for Inline Citation Markers

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: generate_answer signature | Existing behavior | `backend/rag/generator.py:7–10` | Current signature `generate_answer(query, chunks)` — no titles | 2026-04-14 |
| AC2: LLMProvider.complete signature | Existing behavior | `backend/rag/llm/base.py:25` | Current `complete(prompt, context_chunks)` — no titles | 2026-04-14 |
| AC3: prompt template | Existing behavior | `backend/rag/llm/prompts/answer.txt` | Current prompt uses `{context}` (raw chunks) — no numbered index, no `[N]` instruction | 2026-04-14 |
| AC4: numbered index format | Business logic | SDD convention | `[N] title\nchunk` format gives model both document name and content for attribution | 2026-04-14 |
| AC5: fallback on missing markers | Business logic | SDD convention | Model compliance is probabilistic — hard failure would break citations for all queries | 2026-04-14 |
| AC6: multilingual | Requirement doc | `CLAUDE.md`, `ARCH.md A003` | "Never hardcode lang='en' as fallback. Response language = detected query language." | 2026-04-14 |
| AC7: inline_markers_present | Business logic | SDD convention | Observability flag — enables monitoring of model citation compliance rate | 2026-04-14 |
| AC8: call site update | Existing behavior | `backend/api/routes/query.py` | Call site passes `chunks=[d.content for d in docs if d.content]` — must pass parallel `doc_titles` | 2026-04-14 |
| AC9: no marker parsing | Business logic | SDD convention | Marker indices are advisory (model can produce off-by-one) — API layer must not depend on marker integrity | 2026-04-14 |

### Story S004: Consumer Rendering Contract

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC8: rendering contract | Business logic | Consumer team requirement | SPA, Teams bot, Slack bot need consistent citation rendering — no existing contract exists | 2026-04-14 |

### Story S005: Tests and Coverage

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1–AC12: test cases | Requirement doc | `CLAUDE.md` team conventions | "≥80% test coverage" standard; test patterns from `tests/api/test_query.py`, `tests/rag/` | 2026-04-14 |
| AC13: coverage targets | Requirement doc | `CLAUDE.md` team conventions | Existing coverage gates — 100% for new models, ≥80% for modified files | 2026-04-14 |

---

## Summary

**Total ACs:** 40 (S001: 8, S002: 10, S003: 9, S004: 8, S005: 13)
**Fully traced:** 40/40 ✓
**Pending sources:** 0

---

## How to Update

When spec changes or new ACs discovered:
1. Add row to relevant Story table
2. Include source type + reference (must be findable)
3. Add date
4. Update Summary section
5. Commit with message: `docs: update sources traceability for answer-citation`

---

## Source Type Reference

| Type | Examples |
|---|---|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |

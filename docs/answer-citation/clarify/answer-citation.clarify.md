# Clarify: answer-citation
Generated: 2026-04-14 | Spec: v1 DRAFT | Feature branch: feature/document-parser

---

## BLOCKER — Must answer before /plan

| # | Question | Answer | Owner | Due |
|---|----------|--------|-------|-----|
| Q1 | Is `source_url NULL` for all existing documents acceptable to product? Consumers will render titles as plain text (no link) for any doc without a URL — is this UX acceptable at launch? | ✅ Accepted. Option A — ship with NULL. Consumers render plain-text title. `source_url` populated incrementally via `/v1/documents` PATCH by consumer teams. | lb_mui (PO) | Resolved 2026-04-14 |
| Q2 | Do all three consumers (Web SPA, Teams bot, Slack bot) use lenient JSON parsing — unknown keys silently ignored? | ✅ N/A — consumers not yet implemented. Risk is zero now. Constraint moved to S004 AC9: rendering contract MUST mandate permissive JSON parsing for all consumer implementations. | lb_mui | Resolved 2026-04-14 |
| Q3 | Is graceful fallback (answer used as-is when no `[N]` markers present) sufficient, or does the team require a minimum inline marker rate? | ✅ Graceful fallback is sufficient for v1. Monitor via `inline_markers_present` metric post-launch. Hard minimum rate deferred — revisit after 1 sprint of data. | Team / PO | Resolved 2026-04-14 |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q4 | Which LLM adapter is the primary target for prompt engineering validation (S003)? Ollama/Llama 3 is local and free but marker compliance is lower than OpenAI/Claude. | Default: Ollama (C015 — LLM_PROVIDER default). Test all three adapters but tune prompt for Ollama behavior. |
| Q5 | `RetrievedDocument.lang` is sourced from `documents.lang` — is this column guaranteed NOT NULL for all existing documents, or can it be NULL for legacy rows? | Assume non-null based on ORM inspection (nullable=False per A06 analogue). Verify via `SELECT COUNT(*) FROM documents WHERE lang IS NULL` before S001 migration. |
| Q6 | Is `chunk_index` always set on `RetrievedDocument` instances returned by both `_dense_search` and `_bm25_search`? The spec (S002 AC) expects it on `CitationObject` — if BM25 path omits it, a default (0) must be documented. | Assume `chunk_index` is present on dense path (embeddings.chunk_index selected) and defaulted to 0 on BM25 path where not applicable. |
| Q7 | Should the numbered `[N]` index in the prompt be capped at a maximum (e.g., top 5 sources) even when `top_k` is higher, to keep prompt length predictable? | Default: no cap — pass all retrieved chunks to match `citations` count exactly (S002 AC3: citations mirrors sources). |
| Q8 | Migration 007 — is there a DB migration review gate before code lands, or can migration + ORM change be merged in a single PR? | Default: single PR per CLAUDE.md team conventions (migration file first, ORM second within same PR). |

---

## NICE — Won't block

| # | Question |
|---|----------|
| Q9 | Should `CitationObject.score` use banker's rounding or standard rounding to 4dp? Python `round()` uses banker's rounding. |
| Q10 | Should the citation rendering contract (S004) be published to a shared docs repo/Confluence or only live under `docs/answer-citation/`? |
| Q11 | Is `LLMResponse.inline_markers_present` flag surfaced in `/v1/metrics` or only used internally for observability? |
| Q12 | Should future citations support page-level anchors (e.g., `source_url + #page=3`) or is flat URL sufficient for v1? |

---

## Auto-answered from existing files

| Q# | Question | Answer | Source |
|----|----------|--------|--------|
| — | Should `citations` be additive or replace `sources`? | Additive (Option C) — `sources: list[str]` is NOT removed | D-CIT-01, WARM/answer-citation.mem.md |
| — | RBAC: does citation enrichment require any new auth logic? | No — enrichment happens inside existing authenticated retrieval pipeline. Inherited auth (R003, C003). | HARD.md R003 |
| — | Can PII appear in `CitationObject`? | No. `title`, `source_url`, `lang` are non-PII document metadata. `user_id`, `user_group_id`, chunk text are forbidden. | HARD.md R002 / CONSTITUTION C002 |
| — | What is the citation mandate? | C014: AI answers must cite ≥1 source. Confidence < 0.4 → `low_confidence: true`. No answer if no relevant chunks. | CONSTITUTION.md C014 |
| — | Is a score filter applied to `citations`? | No. `citations` mirrors `sources` exactly — all retrieved docs included regardless of score. | D-CIT-03, A05 (confirmed lb_mui) |
| — | Is `documents.title` always non-null? | Yes. ORM confirms `nullable=False`. A06 confirmed 2026-04-14. | A06, spec Layer 3 S001 |
| — | Is `generate_answer()` safe to extend with `doc_titles` param? | Yes. Only 1 caller (`query.py`) confirmed by grep (A02). | A02, spec Assumptions |
| — | What is the migration numbering? | 007 — next in sequence after existing migrations. | D-CIT-02, ARCH.md A006 |
| — | What languages must the prompt support? | ja, en, vi, ko, zh — never hardcode `lang="en"`. Answer in question language. | ARCH.md A003, CONSTITUTION C009 |
| — | Is the index 1-based or 0-based in answers? | 1-based in answer text (`[N]`); 0-indexed in `citations` array (`citations[N-1]`). | D-CIT-04 |
| — | Is API versioning required? | /v1/ prefix maintained. `citations` is additive — no /v2/ needed. | CONSTITUTION C004 |
| — | Must the answer fall back gracefully if LLM omits markers? | Yes. Answer used as-is. `citations` still populated from retrieval. S003 AC5. | SDD convention, S003 AC5 |

---

## Spec Gaps Identified

| Gap | Location | Risk | Recommendation |
|-----|----------|------|----------------|
| `chunk_index` on BM25 path not explicitly confirmed | S001 AC5 / S002 AC model | Medium — `CitationObject.chunk_index` may default to 0 silently for BM25 results | Add explicit note to S001 AC5: "BM25 path sets chunk_index=0 if not available" |
| `documents.lang` nullability for legacy rows not verified | S001 AC4, S002 AC8 (`lang` always present) | Low — if legacy rows have NULL lang, S002 AC8 guarantee breaks | Verify via DB query before S001 migration. Add fallback `d.lang or "und"` to be safe. |
| Consumer strict-deserialization risk (Q2) | S002 API Contract | High if any consumer uses strict JSON models | Must confirm before merge — cannot fix post-launch if SPA/bot breaks |

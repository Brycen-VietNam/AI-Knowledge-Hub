# Clarify: document-parser
Generated: 2026-04-13 | Resolved: 2026-04-13 | Spec: CLARIFIED | Stories: S001–S004

---

## BLOCKER — Resolved ✅

| # | Question | Answer | Owner | Resolved |
|---|----------|--------|-------|----------|
| Q1 | Should OCR (e.g. Tesseract) be in scope for image-only PDFs? | **Out of scope.** Spec keeps `ERR_PDF_NO_TEXT`. OCR added to P2 backlog. | lb_mui | 2026-04-13 |
| Q2 | New endpoint or merge into `POST /v1/documents`? | **New endpoint** `POST /v1/documents/upload` — separate from existing JSON route. | lb_mui | 2026-04-13 |
| Q3 | Does `ingest_pipeline` accept `content: str` directly or read from DB? | **Confirmed: `ingest_pipeline(doc_id, content: str)` — content passed as arg** (D11: not stored in DB). Verified in [documents.py:62](backend/api/routes/documents.py#L62). | Code check | 2026-04-13 |
| Q4 | How is `title` handled on the upload endpoint? | **Optional form field; defaults to filename stem** if omitted (e.g. `"Q1-Report.pdf"` → `"Q1-Report"`). | lb_mui | 2026-04-13 |

---

## SHOULD — Assume if unanswered by sprint start

| # | Question | Default assumption |
|---|----------|--------------------|
| Q5 | Max page count for PDF uploads? Spec bounds by `MAX_UPLOAD_BYTES=20MB` but a 20MB PDF could be 1000+ pages and still parse slowly. | Assume no explicit page-count cap; rely on `MAX_UPLOAD_BYTES` + parser timeout. Add `PARSER_TIMEOUT_SECS` env var (default: 30s) as process-level guard. |
| Q6 | PPTX (.pptx) support: any team requesting it? Spec marks it P2+. | Assume out of scope for this sprint. Add to backlog P2 only if stakeholder confirms. |
| Q7 | Should `ParsedDocument.lang` be populated by the parser (e.g. from PDF metadata `lang` attribute) or always left as `None` and delegated to the chunker? | Assume parsers set `lang=None`; chunker's `detect_language()` always runs (A003). Exception: if PDF XMP metadata contains explicit `dc:language`, populate it to avoid redundant detection. |
| Q8 | For DOCX: should tracked-changes (revision marks) be included or excluded from extracted text? | Assume accepted/final text only — ignore revision marks (`python-docx` default behavior). |
| Q9 | HTML encoding: what if `Content-Type` header declares charset but `<meta charset>` disagrees? | Assume `<meta charset>` wins (beautifulsoup4 `from_encoding` detection); fall back to UTF-8. |
| Q10 | Should the upload endpoint return the document `title` in the 202 response alongside `document_id` and `status`? Current contract only returns `{"document_id", "status"}`. | Assume no — keep 202 minimal, consistent with existing `POST /v1/documents` pattern. |

---

## NICE — Won't block planning or implementation

| # | Question |
|---|----------|
| Q11 | Should there be a `GET /v1/documents/{id}/parse-status` endpoint to poll parsing progress? (Currently status is on the document row.) |
| Q12 | Should rejected file types return a list of supported MIME types in the error body for discoverability? |
| Q13 | Password-protected PDFs: raise `ERR_PARSE_FAILED` or a more specific `ERR_PDF_ENCRYPTED`? |
| Q14 | Should `ParsedDocument` carry a `word_count` field for future analytics / rate limiting by content size? |
| Q15 | `python-magic` requires `libmagic` system library — is it already in the Docker base image, or does the Dockerfile need updating? |

---

## Auto-answered from existing files

| # | Question | Answer | Source |
|---|----------|--------|--------|
| A1 | Auth required on upload endpoint? | Yes — `verify_token` + API-key write gate. | CONSTITUTION.md C003, R003, document-ingestion D09 |
| A2 | Error response shape? | `{"error": {"code": "...", "message": "...", "request_id": "..."}}` | ARCH.md A005 |
| A3 | Route prefix? | `/v1/` mandatory. Breaking changes → `/v2/`. | CONSTITUTION.md C004, HARD.md R004 |
| A4 | Language detection fallback? | Auto-detect at chunker layer — never hardcode `lang="en"`. | CONSTITUTION.md C009, ARCH.md A003 |
| A5 | CJK tokenization responsibility? | Chunker (existing pipeline) — parser extracts raw text only. | HARD.md R005, cjk-tokenizer feature |
| A6 | Audit log requirement? | Required after document row created (not at parser layer). | HARD.md R006 |
| A7 | MIME validation approach? | Magic bytes check, not extension only. | SECURITY.md S003 |
| A8 | PII in ParsedDocument metadata? | Forbidden. Only doc_id, lang, created_at, source_format allowed. | CONSTITUTION.md C002 |
| A9 | Embedding batch size? | Min 32 docs — handled by existing embedder, parser doesn't touch this. | PERF.md P002 |
| A10 | Connection pool? | min=5 max=20 at app startup — upload route uses existing `get_db`. | PERF.md P005 |
| A11 | Rate limiting on upload endpoint? | `/v1/documents` write: 20 req/min per user (C013). Upload counts against same bucket. | CONSTITUTION.md C013 |
| A12 | Library licenses? | All selected libs (pdfplumber MIT, python-docx MIT, beautifulsoup4 MIT) satisfy OSS requirement. | Backlog license matrix 2026-04-08 |

---

## Spec gaps — Patched ✅

| # | Gap | Fix applied |
|---|-----|-------------|
| G1 | S004 AC1 missing `title` form field. | Patched: `title` added as optional field (default: filename stem) in S004 AC1 and API contract. |
| G2 | S004 AC5 data flow ambiguous (arg vs DB). | Patched: AC5 now explicit — `parse() → text str → ingest_pipeline(doc_id, content=text)`, consistent with D11. |
| G3 | No timeout guard for runaway parses. | Patched: AC11 added to S004 — `asyncio.wait_for(PARSER_TIMEOUT_SECS=30)`, 504 on timeout. |
| G4 | SecurityGate signature read bytes before size check → OOM risk. | Patched: S003 AC4 signature changed to `validate(file_size, file_bytes, declared_mime, filename)` — size check first. |

---

## Summary

**Blockers resolved:** 4/4 ✅ (Q1–Q4)
**Should-answer (assumed):** 6 (Q5–Q10)
**Nice-to-have:** 5 (Q11–Q15)
**Auto-answered from files:** 12 (A1–A12)
**Spec gaps patched:** 4/4 ✅ (G1–G4)

> Next: `/checklist document-parser`

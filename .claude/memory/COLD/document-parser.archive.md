# COLD Archive: document-parser
Created: 2026-04-13 | Archived: 2026-04-13 | Status: DONE ✅
Feature: PDF/DOCX/HTML/TXT/MD file upload → text extraction → existing ingestion pipeline

---

## Spec Summary
- 4 stories, 24 ACs, P1 priority  (AC11 added via clarify gap G3 — parser timeout)
- New endpoint: `POST /v1/documents/upload` (multipart/form-data)
- New layer: `backend/rag/parser/` (ParserBase, ParserFactory, PdfParser, DocxParser, HtmlParser, TxtParser, SecurityGate)
- Wires into existing `ingest_pipeline` from document-ingestion — no duplication

## Key Decisions
- D01: pdfplumber (MIT) for PDF; python-docx (MIT) for DOCX; beautifulsoup4 (MIT) for HTML
- D02: python-magic for MIME + magic-byte validation (SECURITY.md S003)
- D03: MAX_UPLOAD_BYTES default 20MB — env-configurable
- D04: API-key only for upload (inherits document-ingestion D09 write gate)
- D05: lang resolution order: provided → parser-detected → chunker auto-detect (A003)
- D06: Image-only PDF raises ParseError("ERR_PDF_NO_TEXT") — no silent failure

## Files to Create
- `backend/rag/parser/__init__.py`
- `backend/rag/parser/base.py` — ParserBase, ParsedDocument, ParseError, UnsupportedFormatError, SecurityError
- `backend/rag/parser/factory.py` — ParserFactory
- `backend/rag/parser/pdf_parser.py` — PdfParser
- `backend/rag/parser/docx_parser.py` — DocxParser
- `backend/rag/parser/html_parser.py` — HtmlParser
- `backend/rag/parser/txt_parser.py` — TxtParser
- `backend/rag/parser/security_gate.py` — SecurityGate
- `backend/api/routes/upload.py` — POST /v1/documents/upload

## Files to Modify
- `backend/api/app.py` — register upload router
- `requirements.txt` — add pdfplumber, python-docx, beautifulsoup4, python-magic

## Integration Points
- document-ingestion: `ingest_pipeline` in documents.py — reused via BackgroundTasks
- cjk-tokenizer: chunker handles CJK tokenization downstream; parser is format-only
- auth: `verify_token` + API-key write gate (same as POST /v1/documents)
- audit_log: write after document row created (R006)

## Open Questions
- Q5: Max page count for PDF? → Assumed: no cap, rely on MAX_UPLOAD_BYTES + PARSER_TIMEOUT_SECS
- Q6: PPTX support? → Out of scope this sprint, P2 backlog
- ~~Q1–Q4: All resolved via clarify session 2026-04-13~~

## Constitution Constraints Applied
- C002: No PII in ParsedDocument metadata (doc_id added by route handler, not parser)
- C003 + R003: verify_token on upload endpoint
- C004 + R004: /v1/ prefix on upload route
- C009 + A003: auto-detect lang, never hardcode
- SECURITY.md S003: magic-byte check before parse
- A005: all errors follow {"error": {"code": ..., "message": ..., "request_id": ...}}
- R006: audit log after document creation

## Clarify Findings (2026-04-13)
- 4 BLOCKERS: Q1 OCR scope, Q2 new vs merged endpoint, Q3 ingest_pipeline signature, Q4 title field on upload
- 4 spec gaps: G1 title missing from S004 AC1, G2 parse→ingest data flow unclear, G3 no parser timeout AC, G4 SecurityGate OOM risk on size check order
- 12 auto-answered from CONSTITUTION.md / existing specs

## Key Decisions (additions from clarify)
- D07: OCR out of scope — image-only PDF raises ERR_PDF_NO_TEXT; OCR added to P2 backlog
- D08: New endpoint POST /v1/documents/upload — separate from existing JSON route
- D09-reuse: ingest_pipeline(doc_id, content: str) confirmed — content passed as arg (D11 from document-ingestion)
- D10: title optional on upload — defaults to filename stem (Path(filename).stem)
- D11: PARSER_TIMEOUT_SECS=30 env var — asyncio.wait_for wrapper; 504 on timeout
- D12: SecurityGate checks file_size first (before read) to prevent OOM on large uploads

## Plan
- Path: `docs/document-parser/plan/document-parser.plan.md`
- Critical path: P0 (Dockerfile+deps) → S001 → S002‖S003 → S004
- Parallel group G2: S002 + S003 safe to run concurrently after S001 interface locked
- Pre-impl gate P0: add libmagic1 to Dockerfile + 4 new packages to requirements.txt (WARN-02 resolution)
- Agent assignments: rag-agent (P0, S001, S002, S003) | api-agent (S004)
- New files: 10 | Modified files: 4

## Tasks

### P0: Dockerfile + Dependencies ✅ DONE 2026-04-13
| Task | Title | Status |
|------|-------|--------|
| T001 | Add libmagic1 to Dockerfile | DONE |
| T002 | Add parser deps to requirements.txt | DONE |

### S001: Parser Interface + Format Dispatch (rag-agent) ✅ DONE 2026-04-13
| Task | Title | Status |
|------|-------|--------|
| T001 | Create parser base types (base.py) | DONE |
| T002 | Create tests/rag/parser/ package init | DONE |
| T003 | Create ParserFactory (factory.py) | DONE |
| T004 | Create parser __init__.py + test_factory.py | DONE |

### S002: PDF + DOCX Parsers (rag-agent) ✅ DONE 2026-04-13
| Task | Title | Status |
|------|-------|--------|
| T001 | Create PdfParser + test_pdf_parser.py | DONE |
| T002 | Create DocxParser + test_docx_parser.py | DONE |
| T003 | Register PdfParser in ParserFactory | DONE |
| T004 | Register DocxParser in ParserFactory | DONE |

### S003: HTML + TXT Parsers + Security Gate (rag-agent) ✅ DONE 2026-04-13
| Task | Title | Status |
|------|-------|--------|
| T001 | Create HtmlParser + test_html_parser.py | DONE |
| T002 | Create TxtParser + test_txt_parser.py | DONE |
| T003 | Create SecurityGate + test_security_gate.py | DONE |
| T004 | Register HtmlParser in ParserFactory | DONE |
| T005 | Register TxtParser in ParserFactory | DONE |

### S004: Upload Endpoint + Ingestion Wiring (api-agent) ✅ DONE 2026-04-13
| Task | Title | Status |
|------|-------|--------|
| T001 | Create upload.py route + unit tests | DONE |
| T002 | Register upload router in app.py + exception handlers | DONE |
| T003 | Integration tests (upload valid file → DB) | DONE |
| T004 | Update backend/api/routes/__init__.py | DONE |

**Total tasks: 19 across 5 stories (P0 + S001–S004)**

## Sync: 2026-04-13
Decisions added: D13 (MdParser: preserve raw Markdown, no HTML rendering; chunker handles downstream)
Tasks changed: MD-T001 (md_parser.py)→DONE, MD-T002 (factory.py)→DONE, MD-T003 (__init__.py)→DONE, MD-T004 (test_md_parser.py)→DONE
Files touched: backend/rag/parser/md_parser.py (NEW), backend/rag/parser/factory.py, backend/rag/parser/__init__.py, tests/rag/parser/test_md_parser.py (NEW)
Questions resolved: none
New blockers: none — S004 still unblocked

## Review (2026-04-13)
- Verdict: CHANGES_REQUIRED → FIXES_COMPLETE (2026-04-13)
- Blocker fixed: A003 — `or "en"` replaced with langdetect (upload.py); NULL stored on LangDetectException
- Warnings fixed: FIX-T002 duplicate dep, FIX-T003 query_hash sentinel "UPLOAD", FIX-T004 filename sanitize, FIX-T005 title max_length=500, FIX-T006 chunked read, FIX-T007 md_parser utf-8 errors=replace, FIX-T008 SecurityGate request_id re-log
- 3 new tests added: test_lang_detection_used_when_form_and_parser_lang_are_none, test_lang_none_stored_when_langdetect_raises, test_crlf_in_filename_stripped_from_title_and_logs, test_md_parser_japanese_utf8_no_mojibake
- 18/18 unit tests pass | Review saved: docs/document-parser/reviews/document-parser.review.md

## Status Log
- 2026-04-13: SPEC created — 4 stories, 23 ACs, all constitution constraints checked
- 2026-04-13: CLARIFY complete — all 4 blockers resolved, 4 spec gaps patched; spec → CLARIFIED; ready for /checklist
- 2026-04-13: PLAN complete — checklist WARN-approved (WARN-01: AGENTS.md missing, WARN-02: libmagic confirmed missing from Docker); plan saved; next: /tasks S001
- 2026-04-13: TASKS complete — 19 tasks across P0+S001–S004; all files in docs/document-parser/tasks/; next: /analyze P0 T001
- 2026-04-13: P0 DONE — libmagic1 in Dockerfile (WARN-02 resolved), 4 parser packages in requirements.txt; dry-run verified; next: /implement S001
- 2026-04-13: S001 DONE — parser interface layer complete; 9 files created; 6/6 tests pass; next: /implement S002 ‖ /implement S003
- 2026-04-13: S002‖S003 DONE — PdfParser, DocxParser, HtmlParser, TxtParser, SecurityGate implemented; 32/32 tests pass (2 slow skipped); pytest.ini updated with `slow` mark; python-magic-bin required on Windows (libmagic1 in Docker handles Linux)
- 2026-04-13: MD support DONE — MdParser added; factory.py updated (text/markdown MIME + .md/.markdown ext); 37/37 tests pass
- 2026-04-13: S004 DONE — upload.py, app.py exception handlers + upload.router, routes/__init__.py, python-multipart in requirements.txt; 9/9 unit tests pass; feature COMPLETE

## Sync: 2026-04-13
Decisions added: D12 (size-first in SecurityGate), pytest `slow` mark registered
Tasks changed: S002/T001→DONE, S002/T002→DONE, S002/T003→DONE, S002/T004→DONE, S003/T001→DONE, S003/T002→DONE, S003/T003→DONE, S003/T004→DONE, S003/T005→DONE
Files touched: backend/rag/parser/pdf_parser.py, backend/rag/parser/docx_parser.py, backend/rag/parser/html_parser.py, backend/rag/parser/txt_parser.py, backend/rag/parser/security_gate.py, tests/rag/parser/test_pdf_parser.py, tests/rag/parser/test_docx_parser.py, tests/rag/parser/test_html_parser.py, tests/rag/parser/test_txt_parser.py, tests/rag/parser/test_security_gate.py, pytest.ini
Questions resolved: none new
New blockers: none — S004 unblocked

## Sync: 2026-04-13 (session #041)
Decisions added: python-multipart required for UploadFile/Form support (added to requirements.txt)
Tasks changed: S004/T001→DONE, S004/T002→DONE, S004/T003→DONE, S004/T004→DONE
Files touched: backend/api/routes/upload.py (NEW), tests/api/test_upload.py (NEW), backend/api/app.py, backend/api/routes/__init__.py, requirements.txt
Questions resolved: none
New blockers: none — feature COMPLETE, ready for /report

## Sync: 2026-04-13 (session #042 — post-implement S004-fix)
Decisions added: FIX-T003 resolution — query_hash NOT NULL → sentinel "UPLOAD" for upload rows (not empty string); FIX-T008 → Option B chosen (re-log at route layer with request_id, not passing request_id into SecurityGate)
Tasks changed: FIX-T001→DONE, FIX-T002→DONE, FIX-T003→DONE, FIX-T004→DONE, FIX-T005→DONE, FIX-T006→DONE, FIX-T007→DONE, FIX-T008→DONE; S004-fix.tasks.md Status→DONE
Files touched: backend/api/routes/upload.py (MODIFIED — all 6 fixes), backend/rag/parser/md_parser.py (MODIFIED — FIX-T007), tests/api/test_upload.py (MODIFIED — 3 new tests), tests/rag/parser/test_md_parser.py (MODIFIED — 1 new test)
Questions resolved: AuditLog.query_hash nullability confirmed NOT NULL → "UPLOAD" sentinel chosen
New blockers: none
Test result: 18/18 unit tests PASS (3 integration errors pre-existing — require live DB)

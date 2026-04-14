# Spec: document-parser
Created: 2026-04-13 | Author: lb_mui | Status: CLARIFIED

---

## LAYER 1 — Summary (load this section for /plan, /checklist)

| Field | Value |
|-------|-------|
| Epic | api |
| Priority | P1 |
| Story count | 4 |
| Token budget est. | ~4k |
| Critical path | S001 → S002 → S003 → S004 |
| Parallel-safe stories | S002, S003 (after S001 interface is defined) |
| Blocking specs | document-ingestion (already done — parser plugs in as pre-step) |
| Blocked by | document-ingestion ✅, cjk-tokenizer ✅ |
| Agents needed | api-agent, rag-agent |

### Problem Statement
Currently `POST /v1/documents` accepts only raw text (`content` field). Users cannot upload binary files (PDF, DOCX, HTML), forcing manual text extraction before upload. This blocks real-world adoption where source documents are always files.

### Solution Summary
- Add a `POST /v1/documents/upload` endpoint accepting multipart file uploads (PDF, DOCX, HTML, TXT)
- Implement a parser layer (`backend/rag/parser/`) that extracts plain text from each format
- Integrate parser output into the existing ingestion pipeline (chunker → embedder → BM25 index)
- Enforce MIME type validation + magic-byte check (security, S003)
- Preserve per-page / per-section metadata (page number, heading) as chunk metadata for citation

### Out of Scope
- OCR for scanned/image-only PDFs (future feature)
- PowerPoint (.pptx) parsing (not in backlog — add to P2)
- Streaming upload progress UI (frontend concern)
- Document versioning / update-in-place (separate feature)

---

## LAYER 2 — Story Detail

---

### S001: Parser Interface + Format Dispatch

**Role / Want / Value**
- As a: backend developer
- I want: a clean `ParserBase` interface with format-based dispatch
- So that: new formats can be added without touching existing code

**Acceptance Criteria**
- [ ] AC1: `backend/rag/parser/base.py` defines `ParserBase` abstract class with `parse(bytes) -> ParsedDocument` method
- [ ] AC2: `ParsedDocument` dataclass contains: `text: str`, `lang: str | None`, `metadata: dict` (page_count, sections, source_format)
- [ ] AC3: `ParserFactory.get_parser(mime_type, filename)` returns the correct parser or raises `UnsupportedFormatError`
- [ ] AC4: Supported formats at launch: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/html`, `text/plain`
- [ ] AC5: `UnsupportedFormatError` includes the rejected MIME type in its message
- [ ] AC6: Unit tests cover: PDF dispatch, DOCX dispatch, HTML dispatch, TXT dispatch, unknown MIME → error

**Auth Requirement**
- [ ] Not applicable (library code — no auth)

**Non-functional**
- Latency: N/A (library)
- Audit log: not required at this layer
- CJK support: parser is format-only; language detection delegated to chunker (existing A003)

**Implementation notes**
- `backend/rag/parser/__init__.py`, `base.py`, `factory.py`
- `ParsedDocument` intentionally simple — no PII, no user data
- Factory uses MIME type as primary key, filename extension as fallback only

---

### S002: PDF + DOCX Parsers

**Role / Want / Value**
- As a: knowledge worker
- I want: to upload a PDF or Word document directly
- So that: I don't need to manually copy-paste text before uploading

**Acceptance Criteria**
- [ ] AC1: `PdfParser.parse(bytes)` extracts text from all pages using `pdfplumber` (MIT license)
- [ ] AC2: PDF metadata includes `page_count` and per-page `page_number` in returned `ParsedDocument.metadata`
- [ ] AC3: PDF with no extractable text (image-only) raises `ParseError` with code `"ERR_PDF_NO_TEXT"`
- [ ] AC4: `DocxParser.parse(bytes)` extracts text from all paragraphs and tables using `python-docx` (MIT license)
- [ ] AC5: DOCX metadata includes `section_count` (number of paragraphs > 0 chars) in `ParsedDocument.metadata`
- [ ] AC6: Corrupt/truncated PDF raises `ParseError` with code `"ERR_PARSE_FAILED"`
- [ ] AC7: Corrupt/truncated DOCX raises `ParseError` with code `"ERR_PARSE_FAILED"`
- [ ] AC8: Unit tests cover: multi-page PDF, single-page PDF, image-only PDF → error, multi-section DOCX, empty DOCX → error, corrupt input → error

**Auth Requirement**
- [ ] Not applicable (library code)

**Non-functional**
- Latency: PDF parse < 3s for documents ≤ 50 pages; DOCX < 1s for ≤ 200KB
- Audit log: not required at parser layer
- CJK support: text extracted as-is; tokenization handled downstream by chunker

**Implementation notes**
- `backend/rag/parser/pdf_parser.py`, `backend/rag/parser/docx_parser.py`
- `pdfplumber` preferred over PyMuPDF (license clarity); `python-docx` for DOCX
- Table cells in DOCX: join with `" | "` separator, then newline after each row

---

### S003: HTML + TXT Parsers + Security Gate

**Role / Want / Value**
- As a: system integrator
- I want: safe parsing of HTML and plain-text files with MIME + magic-byte validation
- So that: malicious uploads (disguised as documents) are rejected before any parsing occurs

**Acceptance Criteria**
- [ ] AC1: `HtmlParser.parse(bytes)` extracts visible text using `beautifulsoup4` (MIT), stripping `<script>`, `<style>`, and all tags
- [ ] AC2: HTML headings (`<h1>`–`<h6>`) are preserved as section separators in extracted text (prefixed with `##`)
- [ ] AC3: `TxtParser.parse(bytes)` decodes as UTF-8 (fallback: latin-1) and returns text with basic whitespace normalization
- [ ] AC4: `SecurityGate.validate(file_size: int, file_bytes: bytes, declared_mime: str, filename: str)` — size check runs FIRST (before reading bytes) using `UploadFile.size` from FastAPI; magic-byte check runs second
- [ ] AC5: Magic-byte mismatch between declared MIME and actual content raises `SecurityError` with code `"ERR_MIME_MISMATCH"` — file is rejected without parsing
- [ ] AC6: Files exceeding `MAX_UPLOAD_BYTES` (default: 20MB, env-configurable) raise `SecurityError` with code `"ERR_FILE_TOO_LARGE"` — checked via `file_size` arg BEFORE `await file.read()` to prevent OOM
- [ ] AC7: Unit tests cover: valid HTML, HTML with script tags (stripped), TXT UTF-8, TXT latin-1 fallback, MIME mismatch → error, oversized file → error

**Auth Requirement**
- [ ] Not applicable (library code — security gate is called from route handler)

**Non-functional**
- Latency: HTML + TXT parse < 500ms for ≤ 500KB
- Audit log: security rejection events should be logged at WARNING level (standard Python logging, not audit_log table)
- CJK support: not applicable at this layer

**Implementation notes**
- `backend/rag/parser/html_parser.py`, `backend/rag/parser/txt_parser.py`, `backend/rag/parser/security_gate.py`
- `python-magic` wraps `libmagic` — verify it's available in Docker image
- `MAX_UPLOAD_BYTES` env var; default 20MB = 20 * 1024 * 1024 bytes

---

### S004: Upload Endpoint + Ingestion Wiring

**Role / Want / Value**
- As a: API consumer (web SPA or bot)
- I want: a `POST /v1/documents/upload` endpoint that accepts a file
- So that: I can upload raw files and have them parsed, chunked, embedded, and indexed automatically

**Acceptance Criteria**
- [ ] AC1: `POST /v1/documents/upload` accepts `multipart/form-data` with fields: `file` (required), `title` (optional str, max 500 chars — defaults to filename stem if omitted), `user_group_id` (optional int), `lang` (optional 2-char string)
- [ ] AC2: Endpoint is protected by `verify_token` (R003); only API-key auth can upload (same write-gate as document-ingestion D09)
- [ ] AC3: Route validates file field is present; returns 422 with `"ERR_NO_FILE"` if missing
- [ ] AC4: `SecurityGate.validate()` is called first; MIME mismatch or oversized file returns 415 / 413 respectively, with standard error shape (A005)
- [ ] AC5: On success: (1) parser extracts `text: str` from file bytes synchronously in the route handler; (2) Document row is inserted with `status="processing"` and `title` (provided or filename stem); (3) `ingest_pipeline(doc_id, content=text)` is dispatched via `BackgroundTasks` — consistent with D11 (content NOT stored in DB); endpoint returns 202 `{"document_id": "<uuid>", "status": "processing"}`
- [ ] AC6: `lang` field on uploaded document: use provided value if given; otherwise use `ParsedDocument.lang` if parser detected it; otherwise leave as `None` (chunker's language detection handles it — A003)
- [ ] AC7: Integration test: upload a valid PDF → 202, confirm document row created in DB with `status="processing"`
- [ ] AC8: Integration test: upload oversized file → 413
- [ ] AC9: Integration test: upload file with wrong extension/MIME → 415
- [ ] AC10: `/v1/documents/upload` added to API router in `backend/api/app.py`; route prefix `/v1/` enforced (R004)
- [ ] AC11: Parser calls are wrapped with `asyncio.wait_for(timeout=PARSER_TIMEOUT_SECS)` (env var, default: 30s); timeout raises `ParseError` with code `"ERR_PARSE_TIMEOUT"` → route returns 504

**API Contract**
```
POST /v1/documents/upload
Headers: X-API-Key: <key>
Body: multipart/form-data
  file:          <binary>   required
  title:         <str>      optional, max 500 chars (default: filename stem)
  user_group_id: <int>      optional
  lang:          <str>      optional, 2-char ISO 639-1

Response 202:
  {"document_id": "<uuid>", "status": "processing"}

Response 413:
  {"error": {"code": "ERR_FILE_TOO_LARGE", "message": "...", "request_id": "..."}}

Response 415:
  {"error": {"code": "ERR_MIME_MISMATCH", "message": "...", "request_id": "..."}}
  {"error": {"code": "ERR_UNSUPPORTED_FORMAT", "message": "...", "request_id": "..."}}

Response 422:
  {"error": {"code": "ERR_NO_FILE", "message": "...", "request_id": "..."}}

Response 504:
  {"error": {"code": "ERR_PARSE_TIMEOUT", "message": "...", "request_id": "..."}}
```

**Auth Requirement**
- [x] API-Key only (write gate, same as `POST /v1/documents`)

**Non-functional**
- Latency: endpoint response (before background parse) < 200ms; total parse+ingest p95 < 10s for 50-page PDF
- Audit log: document upload events logged via existing audit_log mechanism (R006) after document row created
- CJK support: delegated to chunker (existing pipeline)

**Implementation notes**
- `backend/api/routes/upload.py` (new file, keep separate from `documents.py`)
- Re-use `ingest_pipeline` from `document-ingestion` — no duplication
- `UploadFile` from FastAPI + `await file.read()` — enforce MAX_UPLOAD_BYTES before passing to SecurityGate
- Add `python-magic`, `pdfplumber`, `python-docx`, `beautifulsoup4` to `requirements.txt`

---

## LAYER 3 — Sources Traceability

### S001 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC3 | Business logic | Backlog item #9: "PDF/DOCX/HTML → text extraction before chunk + embed" | 2026-04-08 |
| AC4 | Business logic | CONSTITUTION.md — project languages: ja, en, vi, ko + Asia formats | 2026-03-18 |
| AC5–AC6 | Existing behavior | document-ingestion spec pattern: structured errors (A005) | 2026-04-08 |

### S002 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC3 | Business logic | Backlog #9 — PDF required; pdfplumber chosen for MIT license (backlog license matrix) | 2026-04-08 |
| AC4–AC5 | Business logic | Backlog #9 — DOCX required; python-docx MIT | 2026-04-08 |
| AC6–AC7 | Existing behavior | document-ingestion error pattern — ParseError follows A005 shape | 2026-04-08 |

### S003 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1–AC2 | Business logic | Backlog #9 — HTML required for web content ingestion | 2026-04-08 |
| AC3 | Existing behavior | document-ingestion accepts plain text — TXT format is natural extension | 2026-04-08 |
| AC4–AC5 | CONSTITUTION.md | SECURITY.md S003 — "validate MIME type + magic bytes, not just extension" | 2026-03-18 |
| AC6 | Business logic | P95 latency SLA (R007) — large files must be rejected early | 2026-03-18 |

### S004 Sources
| AC | Source | Reference | Date |
|----|--------|-----------|------|
| AC1 | Business logic | Backlog #9 — file upload endpoint; multipart is FastAPI standard | 2026-04-08 |
| AC2 | CONSTITUTION.md | C003 — all /v1/* require auth; D09 from document-ingestion — api_key=write | 2026-04-08 |
| AC3–AC4 | CONSTITUTION.md | A005 — standard error shape; SECURITY.md S003 — MIME validation | 2026-03-18 |
| AC5 | Existing behavior | document-ingestion BackgroundTasks pattern (documents.py) | 2026-04-08 |
| AC6 | CONSTITUTION.md | C009 + A003 — lang auto-detect, never hardcode | 2026-03-18 |
| AC7–AC9 | CONSTITUTION.md | CONSTITUTION.md testing conventions — integration tests for critical paths | 2026-03-18 |
| AC10 | CONSTITUTION.md | R004 — /v1/ prefix mandatory | 2026-03-18 |
| AC11 | Business logic | G3 clarify gap — parser timeout guard; R007 latency SLA requires hard timeout | 2026-04-13 |

# Plan: document-parser
Generated: 2026-04-13 | Status: READY | Checklist: WARN-approved (both items)

---

## Layer 1 — Plan Summary

Stories: 4 | Sessions est.: 2 | Critical path: S001 → S002+S003 (parallel) → S004

**Parallel groups:**
```
G1 (sequential, required first):
  S001 — rag-agent   Parser Interface + Format Dispatch

G2 (parallel, after G1):
  S002 — rag-agent   PDF + DOCX Parsers
  S003 — rag-agent   HTML + TXT Parsers + Security Gate

G3 (sequential, after G2):
  S004 — api-agent   Upload Endpoint + Ingestion Wiring
```

**Pre-implementation task (before G1):**
- P0 — Dockerfile + requirements.txt update (WARN-02 resolution)
  - Add `libmagic1` to `apt-get install` in Dockerfile
  - Add `pdfplumber`, `python-docx`, `beautifulsoup4`, `python-magic` to `requirements.txt`
  - Agent: rag-agent | Blocks: S003 SecurityGate

**Token budget total:** ~4k (within spec estimate)

---

## Layer 2 — Per-Story Plans

---

### P0: Dependencies + Docker (pre-implementation gate)
Agent: rag-agent | Parallel: none | Depends: none | Blocks: S003

**Purpose:** Resolve WARN-02 before any parser code lands. `libmagic` must be available in Docker or `python-magic-bin` fallback chosen.

**Files:**
```
MODIFY: Dockerfile
  — Add libmagic1 to apt-get block (after mecab line)
  — Add python-magic to comment noting WARN-02 resolution

MODIFY: requirements.txt
  — Add section: # Document parser (document-parser feature)
  — pdfplumber>=0.11.0
  — python-docx>=1.1.0
  — beautifulsoup4>=4.12.0
  — python-magic>=0.4.27
```

**Decision point:** If `libmagic1` install is blocked (e.g. Alpine base switch), use `python-magic-bin>=0.4.14` instead (bundles libmagic). Choose one — do not include both.

**Test:** `docker build . --no-cache` must succeed and `python -c "import magic"` must pass inside container.

**Subagent dispatch:** YES — self-contained; no app code changes.

---

### S001: Parser Interface + Format Dispatch
Agent: rag-agent | Group: G1 | Depends: P0 | Blocks: S002, S003

**6 ACs | Files to create: 3**

**Files:**
```
CREATE: backend/rag/parser/__init__.py
  — Exports: ParserBase, ParsedDocument, ParseError, UnsupportedFormatError,
             SecurityError, ParserFactory

CREATE: backend/rag/parser/base.py
  — ParsedDocument dataclass: text: str, lang: str | None, metadata: dict
  — ParserBase ABC: abstract parse(data: bytes) -> ParsedDocument
  — ParseError(Exception): code: str, message: str
  — UnsupportedFormatError(ParseError): includes rejected mime_type in message
  — SecurityError(Exception): code: str, message: str

CREATE: backend/rag/parser/factory.py
  — ParserFactory.get_parser(mime_type: str, filename: str) -> ParserBase
  — Primary dispatch key: mime_type
  — Fallback: filename extension (only if mime_type is application/octet-stream)
  — Raises UnsupportedFormatError for unknown types
  — Supported MIME map (4 types per AC4):
      application/pdf                                          → PdfParser
      application/vnd.openxmlformats-officedocument.
        wordprocessingml.document                             → DocxParser
      text/html                                               → HtmlParser
      text/plain                                              → TxtParser
```

**Key interface contract (must not change — S002/S003 depend on this):**
```python
class ParserBase(ABC):
    @abstractmethod
    def parse(self, data: bytes) -> ParsedDocument: ...

@dataclass
class ParsedDocument:
    text: str
    lang: str | None
    metadata: dict  # keys vary by format; no PII (R002/C002)
```

**Test file:** `tests/rag/parser/test_factory.py`
- PDF dispatch, DOCX dispatch, HTML dispatch, TXT dispatch
- Unknown MIME → UnsupportedFormatError with mime_type in message
- `application/octet-stream` + `.pdf` extension → PdfParser

**Est. tokens:** ~1k | **Subagent dispatch:** YES

---

### S002: PDF + DOCX Parsers
Agent: rag-agent | Group: G2 | Depends: S001 | Parallel-safe: S003

**8 ACs | Files to create: 2**

**Files:**
```
CREATE: backend/rag/parser/pdf_parser.py
  — PdfParser(ParserBase)
  — Uses pdfplumber; open from BytesIO
  — Extracts text page-by-page; joins with "\n\n"
  — metadata: {"page_count": int, "pages": [{"page_number": int, "text": str}], "source_format": "pdf"}
  — No text extracted from any page → ParseError(code="ERR_PDF_NO_TEXT")
  — pdfplumber raises exception → ParseError(code="ERR_PARSE_FAILED")
  — lang: None always (chunker handles — A003)

CREATE: backend/rag/parser/docx_parser.py
  — DocxParser(ParserBase)
  — Uses python-docx; open from BytesIO
  — Extract paragraphs (text > 0 chars) + tables (cells joined with " | ", rows with "\n")
  — section_count = count of paragraphs with len(text.strip()) > 0
  — metadata: {"section_count": int, "source_format": "docx"}
  — No paragraphs/tables → ParseError(code="ERR_PARSE_FAILED")  [empty DOCX]
  — python-docx raises exception → ParseError(code="ERR_PARSE_FAILED")
  — lang: None always
```

**Performance bounds (non-functional, verify in tests):**
- PDF: < 3s for ≤50 pages (use `@pytest.mark.slow` tag, skip in CI fast-path)
- DOCX: < 1s for ≤200KB fixture

**Test file:** `tests/rag/parser/test_pdf_parser.py` + `tests/rag/parser/test_docx_parser.py`
- Multi-page PDF (fixture: 3-page minimal PDF bytes)
- Single-page PDF
- Image-only PDF bytes → ERR_PDF_NO_TEXT
- Multi-section DOCX (fixture: paragraphs + table)
- Empty DOCX → ERR_PARSE_FAILED
- Corrupt truncated bytes → ERR_PARSE_FAILED (both parsers)

**Est. tokens:** ~1.5k | **Subagent dispatch:** YES (S002 and S003 can run in parallel)

---

### S003: HTML + TXT Parsers + Security Gate
Agent: rag-agent | Group: G2 | Depends: S001 | Parallel-safe: S002

**7 ACs | Files to create: 3**

**Files:**
```
CREATE: backend/rag/parser/html_parser.py
  — HtmlParser(ParserBase)
  — Uses beautifulsoup4 (html.parser backend — no lxml dep needed)
  — Strip <script>, <style> and all other tags
  — h1–h6 → prepend "## " before text content before stripping tag
  — metadata: {"source_format": "html"}
  — lang: None (A003)

CREATE: backend/rag/parser/txt_parser.py
  — TxtParser(ParserBase)
  — Decode: try UTF-8, fallback latin-1
  — Normalize: collapse runs of whitespace/blank lines (≤2 consecutive newlines)
  — metadata: {"source_format": "txt"}
  — lang: None (A003)

CREATE: backend/rag/parser/security_gate.py
  — SecurityGate (no base class — utility class)
  — MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
  — validate(file_size: int, file_bytes: bytes, declared_mime: str, filename: str) -> None
      Step 1: if file_size > MAX_UPLOAD_BYTES → SecurityError(code="ERR_FILE_TOO_LARGE")
      Step 2: actual_mime = magic.from_buffer(file_bytes[:2048], mime=True)
      Step 3: if actual_mime != declared_mime and not _compatible(actual_mime, declared_mime):
                  → SecurityError(code="ERR_MIME_MISMATCH")
  — _compatible(): allow text/plain ↔ text/html flexibility (HTML served as text/plain is common)
  — Rejection events: log at WARNING level via standard Python logging (not audit_log table)
```

**Test file:** `tests/rag/parser/test_html_parser.py` + `tests/rag/parser/test_txt_parser.py` + `tests/rag/parser/test_security_gate.py`
- Valid HTML → text, no script/style content
- HTML with `<script>alert(1)</script>` → script stripped completely
- `<h1>Title</h1><p>Body</p>` → "## Title\nBody"
- TXT UTF-8 (ASCII + CJK chars)
- TXT latin-1 encoded bytes → decoded correctly
- MIME mismatch (PDF bytes declared as text/plain) → ERR_MIME_MISMATCH
- Oversized file_size → ERR_FILE_TOO_LARGE (before reading bytes — pass small bytes to confirm size arg is used)

**Est. tokens:** ~1.5k | **Subagent dispatch:** YES (parallel with S002)

---

### S004: Upload Endpoint + Ingestion Wiring
Agent: api-agent | Group: G3 | Depends: S001 + S002 + S003 | Blocks: none

**11 ACs | Files to create: 1 | Files to modify: 2**

**Files:**
```
CREATE: backend/api/routes/upload.py
  — Header comments per project convention (spec, task, rule references)
  — router = APIRouter()
  — PARSER_TIMEOUT_SECS = float(os.getenv("PARSER_TIMEOUT_SECS", "30"))
  — POST /v1/documents/upload
      dependencies: [Depends(verify_token)]
      Form fields: file: UploadFile, title: str | None, user_group_id: int | None, lang: str | None
      Handler logic (in order):
        1. Verify file field present → 422 ERR_NO_FILE if missing
        2. SecurityGate.validate(file.size, <not yet read>, declared_mime, filename)
             → 413 ERR_FILE_TOO_LARGE | 415 ERR_MIME_MISMATCH
        3. content_bytes = await file.read()
           Re-run SecurityGate.validate(file.size, content_bytes[:2048], ...)
             [size already checked in step 2; this re-validates magic bytes]
        4. parser = ParserFactory.get_parser(file.content_type, file.filename)
             → 415 ERR_UNSUPPORTED_FORMAT on UnsupportedFormatError
        5. parsed = await asyncio.wait_for(
               asyncio.to_thread(parser.parse, content_bytes),
               timeout=PARSER_TIMEOUT_SECS
           )  → 504 ERR_PARSE_TIMEOUT on asyncio.TimeoutError
              → 422 ERR_PARSE_FAILED on ParseError
        6. resolved_title = title or Path(file.filename).stem
        7. resolved_lang = lang or parsed.lang  # None → chunker auto-detects (A003)
        8. INSERT Document(title=resolved_title, status="processing", lang=resolved_lang,
                           user_group_id=user_group_id) → get doc_id
        9. await audit_log.write(user_id, [doc_id], query_hash=None)  (R006)
       10. background_tasks.add_task(ingest_pipeline, doc_id, parsed.text)
       11. return JSONResponse({"document_id": str(doc_id), "status": "processing"}, status_code=202)

MODIFY: backend/api/app.py
  — Add: from backend.api.routes import upload
  — Add exception handler for ParseError → 422 with A005 shape
  — Add exception handler for SecurityError → 415/413 (check code to pick status)
  — app.include_router(upload.router)  [after documents.router line]

MODIFY: backend/api/routes/__init__.py
  — Add upload to module (if explicit exports used)
```

**Rate limiting:** Upload counts against `/v1/documents` write bucket (20 req/min per C013). No new rate-limit config needed — existing middleware applies to `/v1/` prefix.

**Auth gate note:** `verify_token` already enforces API-key write / OIDC read distinction (D09 from document-ingestion). No additional gate code needed.

**Test files:** `tests/api/routes/test_upload.py`
- Unit: missing file field → 422 ERR_NO_FILE
- Unit: UnsupportedFormatError from factory → 415 ERR_UNSUPPORTED_FORMAT
- Unit: SecurityError ERR_FILE_TOO_LARGE → 413
- Unit: SecurityError ERR_MIME_MISMATCH → 415
- Unit: ParseError from parser → 422 ERR_PARSE_FAILED
- Unit: asyncio.TimeoutError → 504 ERR_PARSE_TIMEOUT
- Integration: upload valid minimal PDF → 202 + document row in DB with status="processing"
- Integration: upload oversized file → 413
- Integration: upload file with wrong MIME → 415

**Est. tokens:** ~2k | **Subagent dispatch:** NO — touches app.py (shared file); run sequentially after G2.

---

## Dispatch Schedule

```
Session 1:
  [now]   P0  — rag-agent  Dockerfile + requirements.txt
  [P0 done] S001 — rag-agent  Parser Interface + Factory

Session 2:
  [S001 done, parallel]
    S002 — rag-agent  PDF + DOCX Parsers
    S003 — rag-agent  HTML + TXT + SecurityGate
  [S002+S003 done, sequential]
    S004 — api-agent  Upload Endpoint + Wiring
```

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| libmagic not in Docker image | HIGH (confirmed by Dockerfile review) | P0 adds libmagic1 to apt-get; fallback: python-magic-bin |
| pdfplumber slow on large PDFs | MEDIUM | PARSER_TIMEOUT_SECS=30 guard (AC11); performance tests tagged @slow |
| ingest_pipeline signature drift | LOW | Confirmed via code check: `ingest_pipeline(doc_id, content: str)` in documents.py:62 |
| app.py exception handlers conflict | LOW | S004 adds ParseError/SecurityError handlers; existing handlers (EmbedderError etc.) unaffected |

---

## Files Inventory

### New files (10)
```
backend/rag/parser/__init__.py
backend/rag/parser/base.py
backend/rag/parser/factory.py
backend/rag/parser/pdf_parser.py
backend/rag/parser/docx_parser.py
backend/rag/parser/html_parser.py
backend/rag/parser/txt_parser.py
backend/rag/parser/security_gate.py
backend/api/routes/upload.py
tests/rag/parser/   (directory + test files per story)
tests/api/routes/test_upload.py
```

### Modified files (4)
```
Dockerfile            — P0: libmagic1 apt-get
requirements.txt      — P0: pdfplumber, python-docx, beautifulsoup4, python-magic
backend/api/app.py    — S004: include upload router + exception handlers
backend/api/routes/__init__.py  — S004: export upload module
```

---

## Next
`/tasks document-parser --story S001` to generate task breakdown for S001.
Run P0 tasks first (Dockerfile + requirements) before any parser implementation.

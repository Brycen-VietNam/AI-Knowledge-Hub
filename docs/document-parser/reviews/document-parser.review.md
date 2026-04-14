## Code Review: document-parser (S004 + Security Gate + Parser Layer)
Level: security | Date: 2026-04-13 | Reviewer: Claude (opus)

### Task Review Criteria
- AC1 — POST /v1/documents/upload with file + optional title/user_group_id/lang: ✅ PASS
- AC2 — verify_token + API-key write gate (403 for OIDC): ✅ PASS (see WARN-1 on double-declaration)
- AC3 — SecurityGate validates size (413) and magic bytes (415) before parsing: ✅ PASS
- AC4 — ParserFactory dispatches by MIME type: ✅ PASS
- AC5 — asyncio.wait_for with PARSER_TIMEOUT_SECS; 504 on timeout: ✅ PASS
- AC6 — ParseError → 422: ✅ PASS
- AC7 — title defaults to Path(filename).stem: ✅ PASS (see WARN-3 on filename sanitization)
- AC8 — lang fallback: ⚠️ FUNCTIONAL but violates A003 (see BLOCKER)
- AC9 — Document row INSERT with status="processing": ✅ PASS
- AC10 — audit_log written before background dispatch: ✅ PASS
- AC11 — 202 with document_id + status: ✅ PASS

### Full Checks
- Error handling on all external calls: ✅ PASS — parser, DB, and gate calls wrapped
- Logging with request_id: ⚠️ PARTIAL — SecurityGate logs rejections without request_id; upload.py has no logging on rejection paths
- No magic numbers: ✅ PASS — PARSER_TIMEOUT_SECS and MAX_UPLOAD_BYTES are env-driven
- Docstrings on new public functions: ❌ FAIL — upload_file, _write_audit_log, SecurityGate.validate, ParserFactory.get_parser, PdfParser.parse, MdParser.parse all lack docstrings
- No commented-out dead code: ✅ PASS

### Security Checks
- R003 (auth on every endpoint): ✅ PASS — verify_token applied
- R004 (/v1/ prefix): ✅ PASS
- R006 (audit log on document creation): ⚠️ PARTIAL — audit row written but `query_hash=""` is semantically wrong (see WARN-2)
- S001 (no SQL string interpolation): ✅ PASS — ORM-only
- S002 (JWT validation): N/A — inherited
- S003 (MIME + magic bytes): ✅ PASS; filename sanitization: ❌ FAIL (see WARN-3); title sanitization: ❌ FAIL (see WARN-4)
- S005 (no hardcoded secrets): ✅ PASS
- A003 (no hardcoded lang="en" fallback): ❌ FAIL — `resolved_lang = lang or parsed.lang or "en"` (BLOCKER)
- A005 (error shape): ✅ PASS — `_error()` helper consistent throughout

---

### Issues Found

#### ❌ BLOCKER — Must fix before merge

**BLOCKER-1: A003 violation — hardcoded `"en"` fallback**
File: `backend/api/routes/upload.py` line 121
```python
resolved_lang = lang or parsed.lang or "en"   # ← violates A003
```
A003 prohibits hardcoding `lang="en"` as fallback. For a multilingual platform (JP, VI, KO, EN), silently defaulting to English will break CJK tokenization downstream.

Fix: run `langdetect` on `parsed.text` when both `lang` and `parsed.lang` are `None`. Store `NULL`/`"und"` or raise 422 if detection confidence is too low.
```python
from langdetect import detect, LangDetectException
if lang:
    resolved_lang = lang
elif parsed.lang:
    resolved_lang = parsed.lang
else:
    try:
        resolved_lang = detect(parsed.text)
    except LangDetectException:
        resolved_lang = None  # store NULL; downstream chunker handles
```

---

#### ⚠️ WARNING — Should fix before merge

**WARN-1: Double `verify_token` dependency declaration**
File: `backend/api/routes/upload.py` line 48
`dependencies=[Depends(verify_token)]` on decorator AND `user: Annotated[..., Depends(verify_token)]` in signature. FastAPI's `use_cache=True` means only one call per request — no security gap. But the decorator-level dep is dead code; remove it to avoid future confusion if cache behavior changes.

**WARN-2: `query_hash=""` in audit log**
File: `backend/api/routes/upload.py` line 45
Empty string is misleading and will pollute audit queries. Options: pass `None` (if column is nullable), use `"upload"` sentinel, or SHA-256 of `("upload", doc.id)`. Document the choice; `""` is the worst option.

**WARN-3: Filename not sanitized**
File: `backend/api/routes/upload.py` line 74
`filename = file.filename` used verbatim in logging and as title fallback. CRLF/control chars → log injection. Strip control chars and cap at 255 chars:
```python
import unicodedata
filename = "".join(c for c in file.filename if unicodedata.category(c) != "Cc")[:255]
```

**WARN-4: `title` form field unbounded and unsanitized**
No length limit on `title` — a client can submit megabytes. Add `max_length=500` in `Form(...)` and strip control chars.

**WARN-6: Unbounded `await file.read()` when `file.size is None`**
Chunked uploads bypass the pre-read size gate (`file_size=0`), loading the entire body before the post-read check. Fix: read in chunks with a byte counter, abort when limit is exceeded.

**WARN-8: `MdParser` latin-1 fallback produces mojibake for CJK**
File: `backend/rag/parser/md_parser.py` line 14
`data.decode("latin-1")` on UnicodeDecodeError will produce garbage for Japanese/Korean/Vietnamese content. Use `utf-8` with `errors="replace"` or `chardet` instead.

**WARN-10: SecurityGate logging lacks request_id correlation**
File: `backend/rag/parser/security_gate.py` lines 43, 51
Rejection warnings log filename but not request_id — not traceable in production logs. Either pass `request_id` into `validate()` or log at the route layer after catching.

---

#### Recommended (lower priority)

- WARN-5: `file.size` trust for pre-read gate — current two-phase design correctly handles hostile Content-Length; no change needed but document the assumption.
- WARN-7: No `parsed.text` length cap — 20 MiB markdown → huge blob in `ingest_pipeline`. Consider a max-character post-parse cap.
- WARN-9: `python-magic-bin` required on Windows dev — confirm CI installs correct variant (libmagic1 in Docker, python-magic-bin in dev requirements).
- WARN-11: `MAX_UPLOAD_BYTES` default evaluated per call in `validate()` — move to module-level constant.
- WARN-12: `importlib.import_module` in `ParserFactory` — safe given static map; add comment that `_MIME_MAP` must never accept user input.
- WARN-13: `_error()` mints fresh UUID when `request.state.request_id` absent — log a warning when falling back to avoid silent divergence from access logs.

---

### Suggested Tests
```python
# BLOCKER-1 fix verification
def test_lang_detection_used_when_neither_form_nor_parser_provides_lang():
    # parsed.lang=None, form lang=None → expect langdetect called, not "en" stored

# WARN-1 double dep
def test_verify_token_called_exactly_once_per_request(mock_verify_token):
    # assert mock_verify_token.call_count == 1

# WARN-3 filename injection
def test_crlf_in_filename_stripped_from_title_and_logs():
    file = ("report\r\nInjected.txt", ...)
    # assert document title == "reportInjected"

# WARN-8 MdParser CJK
def test_md_parser_japanese_utf8_no_mojibake():
    jp_text = "知識ベース".encode("utf-8")
    doc = MdParser().parse(jp_text)
    assert "知識ベース" in doc.text

# WARN-6 chunked oversized body
def test_chunked_upload_oversized_returns_413_before_memory_exhaustion():
    # stream > 20MB in chunks, assert 413 before full body loaded
```

---

### Verdict
[ ] APPROVED  [x] CHANGES REQUIRED  [ ] BLOCKED

**Blockers: 1**
BLOCKER-1: A003 hardcoded `"en"` fallback — must fix before merge.
After resolving BLOCKER-1, address WARN-3, WARN-4, WARN-6, WARN-8, WARN-10 before shipping.

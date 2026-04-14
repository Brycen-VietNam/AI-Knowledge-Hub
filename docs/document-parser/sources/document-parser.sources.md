# Sources Traceability: document-parser
Created: 2026-04-13 | Feature spec: `docs/document-parser/spec/document-parser.spec.md`

---

## Purpose
Maps each Acceptance Criteria to its source (requirement doc, email, business logic, existing behavior).
Enables: audit trail, regression analysis, design rationale lookup.

---

## AC-to-Source Mapping

### Story S001: Parser Interface + Format Dispatch

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: ParserBase abstract class | Business logic | Backlog #9 — "PDF/DOCX/HTML → text extraction" | Interface pattern consistent with existing tokenizer base.py | 2026-04-08 |
| AC2: ParsedDocument dataclass | Business logic | Backlog #9 + CONSTITUTION.md C002 | No PII in metadata; doc_id added downstream by route handler | 2026-04-08 |
| AC3: ParserFactory dispatch | Existing behavior | backend/rag/tokenizers/factory.py | Same factory pattern as TokenizerFactory | 2026-04-13 |
| AC4: Supported MIME types | Business logic | Backlog #9 — PDF, DOCX, HTML listed explicitly | TXT added as natural extension of existing content field | 2026-04-08 |
| AC5: UnsupportedFormatError message | Existing behavior | document-ingestion error pattern (A005) | Structured error shape used throughout backend | 2026-04-08 |
| AC6: Unit tests | CONSTITUTION.md | Testing conventions — ≥80% coverage for new code | — | 2026-03-18 |

### Story S002: PDF + DOCX Parsers

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: pdfplumber for PDF | Business logic | Backlog license matrix — MIT license required | pdfplumber chosen over PyMuPDF for cleaner MIT license | 2026-04-08 |
| AC2: page_number in metadata | Business logic | Citation requirement (backlog #10 answer-citation) | Page metadata enables source citation downstream | 2026-04-13 |
| AC3: Image-only PDF → ParseError | Business logic | R007 latency SLA — silent failure on no-text PDF wastes pipeline time | Fail fast with clear error | 2026-03-18 |
| AC4: python-docx for DOCX | Business logic | Backlog license matrix — MIT license required | — | 2026-04-08 |
| AC5: section_count metadata | Business logic | Citation support — section metadata aids answer-citation | — | 2026-04-13 |
| AC6–AC7: ParseError on corrupt files | Existing behavior | A005 + CONSTITUTION.md P005 — fail fast, fail visibly | — | 2026-03-18 |
| AC8: Unit tests | CONSTITUTION.md | ≥80% coverage + integration tests for critical paths | — | 2026-03-18 |

### Story S003: HTML + TXT Parsers + Security Gate

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: beautifulsoup4 HTML parse | Business logic | Backlog #9 — HTML required | BS4 MIT license; XSS prevention by stripping all tags | 2026-04-08 |
| AC2: Heading preservation | Business logic | Citation support — headings aid section-level citation | — | 2026-04-13 |
| AC3: TXT UTF-8/latin-1 | Existing behavior | document-ingestion accepts plain text strings | Extension of existing content field behavior | 2026-04-08 |
| AC4: python-magic validation | CONSTITUTION.md | SECURITY.md S003 — "validate MIME type + magic bytes, not just extension" | Hard security rule | 2026-03-18 |
| AC5: MIME mismatch → SecurityError | CONSTITUTION.md | SECURITY.md S003 | Prevents disguised executable uploads | 2026-03-18 |
| AC6: MAX_UPLOAD_BYTES gate | CONSTITUTION.md | SECURITY.md S003 + R007 SLA — large unvalidated files break latency SLA | Default 20MB; env-configurable | 2026-03-18 |
| AC7: Unit tests | CONSTITUTION.md | ≥80% coverage for new code | — | 2026-03-18 |

### Story S004: Upload Endpoint + Ingestion Wiring

| AC | Source Type | Reference | Details | Date |
|----|-------------|-----------|---------|------|
| AC1: multipart/form-data contract | Business logic | Backlog #9 — file upload; FastAPI UploadFile is standard | — | 2026-04-08 |
| AC2: API-key only write gate | Existing behavior | document-ingestion D09 decision — api_key=write, OIDC=read | Consistent with POST /v1/documents | 2026-04-08 |
| AC3: 422 on missing file | Existing behavior | document-ingestion validation pattern; A005 error shape | — | 2026-04-08 |
| AC4: SecurityGate first | CONSTITUTION.md | SECURITY.md S003 — validate before processing | Prevents wasted parse on bad input | 2026-03-18 |
| AC5: BackgroundTasks + 202 | Existing behavior | document-ingestion documents.py BackgroundTasks pattern | Re-use ingest_pipeline — no duplication | 2026-04-08 |
| AC6: lang resolution order | CONSTITUTION.md | C009 + A003 — never hardcode lang="en"; auto-detect at chunker | Three-tier: provided → parser-detected → chunker auto-detect | 2026-03-18 |
| AC7–AC9: Integration tests | CONSTITUTION.md | Testing conventions — integration tests for all critical journeys | — | 2026-03-18 |
| AC10: /v1/ prefix | CONSTITUTION.md | C004 + R004 — /v1/ prefix mandatory | — | 2026-03-18 |

---

## Summary

**Total ACs:** 23
**Fully traced:** 23/23 ✓
**Pending sources:** 0

---

## How to Update

When spec changes or new ACs discovered:
1. Add row to relevant Story table
2. Include source type + reference (must be findable)
3. Add date
4. Update Summary section
5. Commit with message: `docs: update sources traceability for document-parser`

---

## Source Type Reference

| Type | Examples |
|------|----------|
| **Requirement doc** | Business requirement PDF, functional spec, product brief |
| **Email** | Stakeholder decision, clarification, approved scope change |
| **Existing behavior** | Current system code, API response, database schema |
| **Business logic** | BrSE analysis, market research, compliance rule |
| **Conversation** | Design discussion, standup decision, client call |
| **Ticket** | JIRA ticket, issue, feature request |
| **Other** | Anything else — be specific |

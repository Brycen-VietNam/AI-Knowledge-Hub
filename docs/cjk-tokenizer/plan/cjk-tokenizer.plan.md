# Plan: cjk-tokenizer
Generated: 2026-04-06 | Checklist: PASS ✅ | Spec: `docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md`

---

## Layer 1 — Plan Summary

| Field | Value |
|---|---|
| Stories | 4 |
| Sessions est. | 2 |
| Critical path | S001 → S002 → S003 ∥ S004 |
| Agent | rag-agent (sole owner) |
| Token budget total | ~14k |

### Parallel Groups
```
G1 (sequential): S001 — tokenizer backends + Dockerfile
G2 (after G1):   S002 — TokenizerFactory
G3 (after G2):   S003 ∥ S004 — detection + tests (parallel-safe, different files)
```

### Infra Note
S001 includes a Dockerfile change (MeCab install). Flag for DevOps review before merge per WARN-01.

---

## Layer 2 — Per-Story Plan

### S001: Per-language tokenizer backends
**Agent:** rag-agent | **Group:** G1 | **Depends:** none | **Sequential**

**Files:**
```
CREATE: backend/rag/tokenizers/__init__.py
CREATE: backend/rag/tokenizers/base.py          — BaseTokenizer ABC
CREATE: backend/rag/tokenizers/exceptions.py    — UnsupportedLanguageError, LanguageDetectionError
CREATE: backend/rag/tokenizers/japanese.py      — MeCab + ipadic
CREATE: backend/rag/tokenizers/korean.py        — kiwipiepy
CREATE: backend/rag/tokenizers/chinese.py       — jieba
CREATE: backend/rag/tokenizers/vietnamese.py    — underthesea word_tokenize
CREATE: backend/rag/tokenizers/whitespace.py    — en / explicit fallback
MODIFY: Dockerfile                              — apt-get mecab libmecab-dev mecab-ipadic-utf8
```

**Key constraints:**
- All backends implement `BaseTokenizer.tokenize(text: str) -> list[str]`
- Empty string → return `[]` (no exception) — AC8
- No Java runtime — kiwipiepy only, no KoNLPy import anywhere
- Japanese: MeCab surface forms (default ipadic output)
- Korean: kiwipiepy, return morpheme `form` only (drop tag/pos tuples)
- Vietnamese: `underthesea.word_tokenize(text)` — not `tokenize()`

**Est. tokens:** ~4k
**Test:** `pytest tests/rag/test_tokenizers.py::test_backends -v`
**Subagent dispatch:** YES — self-contained, no DB or API dependency

---

### S002: TokenizerFactory with lazy loading
**Agent:** rag-agent | **Group:** G2 | **Depends:** S001 | **Sequential**

**Files:**
```
CREATE: backend/rag/tokenizers/factory.py       — TokenizerFactory class
MODIFY: backend/rag/tokenizers/__init__.py      — export TokenizerFactory
```

**Key constraints:**
- `TokenizerFactory.get(lang: str) -> BaseTokenizer`
- Lazy-load: import inside `get()`, not at module level
- Singleton per lang: `_registry: dict[str, BaseTokenizer]` + `threading.Lock`
- Supported: `"ja"`, `"ko"`, `"zh"`, `"vi"`, `"en"`
- Unknown lang → raises `UnsupportedLanguageError` (from exceptions.py)
- `get("en")` → `WhitespaceTokenizer` (not a fallback, explicit only)

**Est. tokens:** ~2k
**Test:** `pytest tests/rag/test_tokenizers.py::test_factory -v`
**Subagent dispatch:** YES — depends only on S001 files

---

### S003: Language auto-detection
**Agent:** rag-agent | **Group:** G3 | **Depends:** S002 | **Parallel-safe with S004**

**Files:**
```
CREATE: backend/rag/tokenizers/detection.py     — detect_language()
MODIFY: backend/rag/tokenizers/__init__.py      — export detect_language
```

**Key constraints:**
- `detect_language(text: str) -> str` returns ISO 639-1 code
- `len(text) < 8` → raise `LanguageDetectionError` immediately (D06)
- `len(text) > 512` → truncate to 512 before detection (SECURITY.md S003)
- `langdetect` confidence < 0.85 → raise `LanguageDetectionError`
- `LangDetectException` → raise `LanguageDetectionError`
- Empty string → raise `LanguageDetectionError`
- Unsupported detected lang (e.g. `"fr"`) with confidence ≥ 0.85 → return `"en"` (WhitespaceTokenizer path)
- Does NOT call TokenizerFactory — detection only, caller dispatches

**Est. tokens:** ~2k
**Test:** `pytest tests/rag/test_tokenizers.py::test_detection -v`
**Subagent dispatch:** YES — parallel with S004

---

### S004: Tokenizer tests — unit + performance
**Agent:** rag-agent | **Group:** G3 | **Depends:** S002 | **Parallel-safe with S003**

**Files:**
```
CREATE: tests/rag/test_tokenizers.py            — full test suite
MODIFY: tests/rag/__init__.py                   — if not exists
```

**Key constraints:**
- Golden examples ≥ 2 per language (ja/ko/zh/vi/en) — include: short query (3 chars handled via error or passthrough), mixed CJK+ASCII, 150+ char sentence
- `test_backends`: one test class per language, assert tokenize() returns `list[str]`
- `test_factory`: all 5 langs + `UnsupportedLanguageError` on unknown
- `test_detection`: high-confidence, confidence < 0.85 → error, `LangDetectException` → error, `len < 8` → error, empty → error
- `test_regression_no_whitespace_for_cjk`: asserts `WhitespaceTokenizer` is NOT returned by Factory for `"ja"/"ko"/"zh"/"vi"`
- `@pytest.mark.performance` on latency test: 200-char input per lang < 200ms
- Coverage ≥ 80% for all `backend/rag/tokenizers/*.py`
- Tests run offline — all libs must be installed, no network calls

**Est. tokens:** ~4k
**Test:** `pytest tests/rag/test_tokenizers.py -v --cov=backend/rag/tokenizers`
**Subagent dispatch:** YES — parallel with S003 (different file: test file only)

---

## Dispatch Order Summary

```
[G1] dispatch rag-agent → S001 (backends + Dockerfile)
      ↓ DONE
[G2] dispatch rag-agent → S002 (Factory)
      ↓ DONE
[G3] dispatch rag-agent → S003 + S004 in parallel
      ↓ BOTH DONE
     → run full test suite
     → DevOps review for Dockerfile change
     → /reviewcode cjk-tokenizer
```

## Pre-dispatch Checklist (orchestrator runs before each G)
- [ ] `/sync` run → HOT.md + WARM updated
- [ ] Previous group tests: PASS
- [ ] No file conflicts between parallel stories

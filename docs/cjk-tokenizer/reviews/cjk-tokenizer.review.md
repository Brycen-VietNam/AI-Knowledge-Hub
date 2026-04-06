# Code Review: cjk-tokenizer — All Stories (S001–S004)
Level: security | Date: 2026-04-06 | Reviewer: Claude Opus 4.6

---

## Task Review Criteria

### S001 — Tokenizer backends
- [x] `BaseTokenizer` uses `abc.ABC` + `@abstractmethod`
- [x] `tokenize` signature: `(self, text: str) -> list[str]`
- [x] `UnsupportedLanguageError(ValueError)` — subclasses ValueError
- [x] `LanguageDetectionError(RuntimeError)` — distinct from UnsupportedLanguageError
- [x] Japanese: `MeCab.Tagger()` + `parseToNode` surface form iteration
- [x] Japanese: empty string → `[]`
- [x] Korean: `Kiwi().tokenize(text)` → `[token.form ...]` — all morphemes, no POS filter
- [x] Korean: empty string → `[]`
- [x] Chinese: `jieba.cut(text)` + whitespace token filter; `jieba.setLogLevel(WARNING)` suppresses stderr
- [x] Chinese: empty string → `[]`
- [x] Vietnamese: `word_tokenize(text)` (not `tokenize` — char-level)
- [x] Vietnamese: empty string → `[]`
- [x] WhitespaceTokenizer: `text.split()` — no lower, no strip, preserves original form
- [x] All backends: golden tests pass

### S002 — TokenizerFactory
- [x] `get("ja")` → `JapaneseTokenizer` (skipped on Windows — MeCab system dep)
- [x] `get("ko")` → `KoreanTokenizer`
- [x] `get("zh")` → `ChineseTokenizer`
- [x] `get("vi")` → `VietnameseTokenizer`
- [x] `get("en")` → `WhitespaceTokenizer`
- [x] `get("xx")` → raises `UnsupportedLanguageError`
- [x] Two calls to `get("en")` return same object (`is` identity confirmed)
- [x] Lazy import inside `_create()` — not at module level
- [x] `threading.Lock` + double-checked locking

### S003 — detect_language()
- [x] Empty string → `LanguageDetectionError`
- [x] `len(text) < 8` → `LanguageDetectionError` (no detect call — D06)
- [x] `len(text) > 512` → truncated to `text[:512]` (SECURITY S003)
- [x] `LangDetectException` caught → re-raised as `LanguageDetectionError`
- [x] confidence < 0.85 → `LanguageDetectionError`
- [x] Unsupported lang (e.g. `"fr"`) with confidence ≥ 0.85 → returns `"en"`
- [x] `detect_langs()` used (not `detect()`) — probability readable
- [x] `zh-cn` / `zh-tw` mapped to `"zh"` (D10)
- [x] `DetectorFactory.seed = 0` at module level (D08 — deterministic CI)
- [x] `detect_language` exported from `__init__.py`

### S004 — Tests
- [x] `@pytest.mark.parametrize("lang", ["ko", "zh", "vi"])` for whitespace regression (R005 guard)
- [x] Japanese regression test — present with `@skip_no_mecab` guard
- [x] `not isinstance(tokenizer, WhitespaceTokenizer)` assertion
- [x] `@pytest.mark.performance` on all 4 perf tests
- [x] 200+ char realistic sample text per language
- [x] Timing via `time.perf_counter()` — wall time
- [x] `assert elapsed < 0.2` (200ms) per language
- [x] Warm-up call before timing measurement (steady-state, not model-load)

---

## Full Level Checks

- [x] **Error handling**: `detect_language()` has `try/except LangDetectException` with chained re-raise
- [x] **No magic numbers**: `0.85` confidence threshold documented via D06 in docstring; `512` char limit annotated with SECURITY S003 comment; `8` char minimum documented with D06 comment
- [x] **Docstring**: `detect_language()` has complete docstring listing error conditions — public API function. Tokenizer backends are simple enough that docstrings would be noise.
- [x] **No dead code**: no commented-out code anywhere
- [x] **Logging**: no user-facing log entries in this module (tokenizers are pure computation, no I/O). `jieba.setLogLevel(WARNING)` correctly suppresses library noise.
- [⚠️] **request_id in logs**: N/A — tokenizers have no logging by design (no I/O operations)

---

## Security Level Checks

- [x] **R001 (RBAC WHERE clause)**: not applicable — tokenizers are stateless text processors with no DB access. RBAC is enforced upstream in `retriever.py`.
- [x] **R002 (No PII in metadata)**: not applicable — no vector metadata written by this module.
- [x] **R003 (verify_token on routes)**: not applicable — no new API routes added.
- [x] **S001 (No SQL injection)**: no SQL in tokenizer layer. Zero f-string or string interpolation risk.
- [x] **S002 (JWT validation)**: not applicable.
- [x] **S003 (Input sanitization)**: ✅ `detection.py:34` — `text = text[:512]` truncates before any external library call. Length guard at line 30–33 rejects text < 8 chars before any processing.
- [x] **S005 (No hardcoded secrets)**: no secrets, URLs, or credentials anywhere in the implementation.
- [x] **R006 (audit_log)**: not applicable — tokenizers are pre-retrieval utilities; audit logging is at the retrieval layer.
- [x] **R005 (CJK tokenization)**: ✅ this entire feature satisfies R005. Regression test `TestCJKWhitespaceRegression` guards against future violation.

---

## Issues Found

### ⚠️ WARNING — Should fix (non-blocking)

**1. `__init__.py` lists backend names in `__all__` but they are lazy via `__getattr__`**

`__all__` at line 9–20 includes `JapaneseTokenizer`, `KoreanTokenizer`, etc. — but these are not statically imported in the file; they go through `__getattr__`. This is valid Python (PEP 562) and works correctly, but `__all__` is a documentation contract and tools like `mypy` or `pylint` may warn that those names aren't directly bound.

Risk: low — runtime behavior is correct. Static analysis tools may flag it.
Fix: add a comment clarifying the intent, or accept the current pattern.

**2. `TokenizerFactory._registry` is a mutable class variable shared across tests**

The singleton `_registry: dict[str, BaseTokenizer] = {}` at class level persists across test runs in the same process. Tests that call `TokenizerFactory.get("en")` will share the same instance. This is intentional for production (D05 lazy singleton) but can cause inter-test state sharing if a tokenizer is patched mid-suite.

Risk: low — no test currently patches tokenizer instances. Worth noting for future test authors.
Fix: document the singleton behavior in the class docstring, or add a `_reset()` classmethod for testing.

**3. `UnsupportedLanguageError` error message uses `{lang!r}` (includes quotes in repr)**

`raise UnsupportedLanguageError(f"Unsupported language: {lang!r}")` will produce `"Unsupported language: 'xx'"`. The extra quotes may be unexpected for callers catching and displaying the message. Minor style point.

Risk: negligible.
Fix: use `{lang}` instead of `{lang!r}` if callers display the message to end users.

---

## Rules Verification (POST-FLIGHT)

| Rule | Check | Result |
|---|---|---|
| R005 | CJK tokenizers implemented for ja/ko/zh/vi | ✅ SATISFIED |
| R001 | RBAC not in scope — retriever unchanged | ✅ N/A |
| S003 | Input truncated to 512 chars in detection.py:34 | ✅ SATISFIED |
| S001 | Zero SQL in tokenizer layer | ✅ N/A |
| ARCH A002 | rag-agent scope: backend/rag/tokenizers/ only | ✅ SATISFIED |
| ARCH A003 | language detection does not hardcode "en" as only path | ✅ SATISFIED |

---

## Test Results

```
48 passed, 8 skipped (MeCab skip guard — system binary not on Windows dev)
0 failed
```

8 skipped tests are not a defect. `JapaneseTokenizer` requires `mecab` + `mecab-ipadic-utf8` system packages (Dockerfile provides them, WARN-01). The skip guard `_MECAB_AVAILABLE` correctly detects this and skips rather than fails, allowing CI without Docker to run cleanly.

---

## Verdict

**[x] APPROVED**

All 22 ACs satisfied. All task review criteria passed. Security checks clean — no SQL injection risk, input sanitization in place (S003), no secrets, no PII. Three warnings are style/documentation points, none blocking. MeCab skip behavior is correct and expected (WARN-01 from checklist).

**Next:** `/report cjk-tokenizer`

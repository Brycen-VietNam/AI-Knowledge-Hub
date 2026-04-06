# Analysis: cjk-tokenizer — All Stories
Generated: 2026-04-06 | Depth: shallow + patterns | Spec: DRAFT

---

## Code Map — Existing RAG layer

### backend/rag/__init__.py
```python
from .retriever import QueryTimeoutError, RetrievedDocument, retrieve
__all__ = ["QueryTimeoutError", "RetrievedDocument", "retrieve"]
```
→ Pattern to follow: new `tokenizers/` subpackage must have its own `__init__.py` with explicit `__all__`.

### backend/rag/retriever.py (relevant signatures)
```python
async def _bm25_search(session, bm25_query: str, user_group_ids, top_k) -> list[RetrievedDocument]:
    # Uses to_tsquery('simple', :query) — WHITESPACE TOKENIZATION
    # This is the call site that needs tokenized tokens before entering here
```
→ **Gap**: `bm25_query` is passed as raw string. After cjk-tokenizer is implemented,
  callers will tokenize first, join to tsquery string, then pass here. The retriever itself is NOT touched by this feature.

---

## Existing Test Patterns to Follow

### tests/rag/test_retriever_rbac.py — established conventions
1. **File header comments**: `# Spec: ...`, `# Task: T00X — ...`, `# Decision: D0X — ...`
2. **Import style**: `from backend.rag.retriever import X` (absolute import from package root)
3. **Smoke test pattern**:
   ```python
   def test_imports():
       from backend.rag.tokenizers import TokenizerFactory  # noqa: F401
   ```
4. **Class-based test grouping**: `class TestJapaneseTokenizer:` with `pytest.mark.asyncio` where needed
5. **Mock pattern**: `unittest.mock.MagicMock()` for simple mocks — consistent with existing tests
6. **Performance test marker**: `@pytest.mark.performance` — already registered in `pytest.ini`
7. **Integration skip guard**: `@pytest.mark.skipif(not os.getenv(...), reason=...)`

### pytest.ini — already configured
- `asyncio_mode = auto` → no need for `@pytest.mark.asyncio` decorator (but existing tests use it — follow existing style)
- `markers`: `integration` and `performance` already registered ✅
- **S004-T002**: `pytest.ini` does NOT need modification — `performance` marker already exists

### tests/rag/__init__.py — exists (empty)
- `tests/rag/test_tokenizers.py` can be created directly, no `__init__.py` change needed

---

## Gaps / Issues Found

### ⚠️ requirements.txt — missing all 4 tokenizer libraries
```
# Current:
fastapi, sqlalchemy, asyncpg, pgvector, PyJWT, cryptography, httpx, pytest, pytest-asyncio

# Missing (must add in S001):
mecab-python3>=1.0.6      # MeCab Python binding
kiwipiepy>=0.18.0          # Korean tokenizer (MIT)
jieba>=0.42.1              # Chinese tokenizer (MIT)
underthesea>=6.8.0         # Vietnamese tokenizer (GPL-3.0, internal OK)
langdetect>=1.0.9          # Language detection (S003)
```
→ **Action**: Add to `requirements.txt` in S001-T001 (same task as base scaffold).

### ⚠️ Dockerfile — does not exist in repo root
`Dockerfile` not found via Glob. Either:
- Located in a subdirectory (e.g. `docker/Dockerfile`)
- Not yet created

→ **Action for S001-T005**: Run `/analyze S001 --depth deep` before implementing T005
  to confirm Dockerfile location. If absent, create it. Flag to DevOps per WARN-01.

### ⚠️ MeCab Python binding: package name
`mecab-python3` is the correct pip package (not `mecab-python` which is unmaintained).
MeCab tagger initialization: `MeCab.Tagger("-Owakati")` outputs space-separated tokens
as a single string → must `split()` and strip trailing `\n`.
Alternative: use `node.surface` iteration (more explicit, preferred for empty-string guard).

### ⚠️ kiwipiepy API note
`Kiwi()` constructor is expensive — lazy-load matters (S002 AC7).
`kiwi.tokenize(text)` returns `list[Token]`; each `Token` has `.form` (str) and `.tag` (str).
Filter: keep all morphemes, return `[t.form for t in kiwi.tokenize(text)]`.
Empty string: `kiwi.tokenize("")` returns `[]` — safe.

### ⚠️ underthesea API note
`underthesea.word_tokenize(text)` returns `list[str]` directly ✅.
`underthesea.tokenize(text)` returns character-level tokens — NOT what we want.
Confirmed correct API: `word_tokenize`.

### ⚠️ langdetect non-determinism
`langdetect` uses random seed internally → same text may return different results across calls.
**Fix**: call `langdetect.DetectorFactory.seed = 0` at module import in `detection.py`.
Without this, CI tests will be flaky.

### ⚠️ jieba startup warning
jieba prints initialization message to stderr on first import.
Suppress with: `jieba.setLogLevel(logging.WARNING)` or `jieba.initialize()` silently.
Add this in `ChineseTokenizer.__init__` or at module level in `chinese.py`.

---

## Patterns to Follow per Story

### S001 — Tokenizer backends
```python
# base.py pattern
from abc import ABC, abstractmethod

class BaseTokenizer(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[str]: ...

# japanese.py pattern — node iteration (explicit, handles empty)
import MeCab
class JapaneseTokenizer(BaseTokenizer):
    def __init__(self):
        self._tagger = MeCab.Tagger()
    def tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        node = self._tagger.parseToNode(text)
        tokens = []
        while node:
            if node.surface:
                tokens.append(node.surface)
            node = node.next
        return tokens
```

### S002 — TokenizerFactory
```python
# factory.py pattern — lazy singleton with lock
import threading
from typing import TYPE_CHECKING

class TokenizerFactory:
    _registry: dict[str, "BaseTokenizer"] = {}
    _lock = threading.Lock()

    @classmethod
    def get(cls, lang: str) -> "BaseTokenizer":
        if lang in cls._registry:
            return cls._registry[lang]
        with cls._lock:
            if lang in cls._registry:   # double-checked locking
                return cls._registry[lang]
            instance = cls._create(lang)
            cls._registry[lang] = instance
            return instance

    @classmethod
    def _create(cls, lang: str) -> "BaseTokenizer":
        if lang == "ja":
            from .japanese import JapaneseTokenizer
            return JapaneseTokenizer()
        # ... etc
        raise UnsupportedLanguageError(f"Unsupported language: {lang!r}")
```

### S003 — detect_language
```python
# detection.py pattern
from langdetect import detect_langs, LangDetectException
from langdetect import DetectorFactory
DetectorFactory.seed = 0   # deterministic results

_SUPPORTED = {"ja", "ko", "zh", "vi", "en"}
_ZH_VARIANTS = {"zh-cn", "zh-tw", "zh"}

def detect_language(text: str) -> str:
    if not text:
        raise LanguageDetectionError("Empty text")
    if len(text) < 8:
        raise LanguageDetectionError(f"Text too short for detection: {len(text)} chars")
    text = text[:512]   # SECURITY.md S003
    try:
        results = detect_langs(text)
    except LangDetectException as e:
        raise LanguageDetectionError(str(e)) from e
    top = results[0]
    if top.prob < 0.85:
        raise LanguageDetectionError(f"Low confidence: {top.prob:.2f} for '{top.lang}'")
    lang = top.lang
    if lang in _ZH_VARIANTS:
        return "zh"
    if lang in _SUPPORTED:
        return lang
    return "en"   # unsupported lang, high confidence → whitespace path
```

---

## Import Convention for tests/rag/test_tokenizers.py
```python
# Follow existing test file header pattern:
# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Story: S001 — Per-language tokenizer backends
# Task: T001 — BaseTokenizer ABC + exceptions
# Task: T002 — JapaneseTokenizer
# ...

from backend.rag.tokenizers import (
    BaseTokenizer, JapaneseTokenizer, KoreanTokenizer,
    ChineseTokenizer, VietnameseTokenizer, WhitespaceTokenizer,
    TokenizerFactory, detect_language,
    UnsupportedLanguageError, LanguageDetectionError,
)
```

---

## S004-T002 — pytest.ini status
`performance` marker already registered in `pytest.ini` ✅
**No change needed** — task file note was incorrect. Remove that action from S004-T002.

---

## Summary of Pre-implement Actions (in order)

| # | Action | Story | Notes |
|---|---|---|---|
| 1 | Add 5 packages to `requirements.txt` | S001-T001 | mecab-python3, kiwipiepy, jieba, underthesea, langdetect |
| 2 | Locate/create Dockerfile | S001-T005 | Confirm path before edit; flag DevOps |
| 3 | Set `DetectorFactory.seed = 0` in detection.py | S003-T001 | Prevents flaky CI tests |
| 4 | Suppress jieba stderr on import | S001-T001 (chinese.py) | `jieba.setLogLevel` |
| 5 | No pytest.ini change needed | S004-T002 | `performance` already registered |

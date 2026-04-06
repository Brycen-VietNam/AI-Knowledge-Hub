# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Task: S003-T001 — detect_language()
# Decision: D06 — text < 8 chars → raise immediately
# Decision: D08 — DetectorFactory.seed = 0 for deterministic CI
# Decision: D10 — zh-cn / zh-tw → "zh"
from langdetect import DetectorFactory, LangDetectException, detect_langs

from .exceptions import LanguageDetectionError

DetectorFactory.seed = 0  # D08: deterministic results across CI runs

_SUPPORTED = {"ja", "ko", "zh", "vi", "en"}
_ZH_VARIANTS = {"zh-cn", "zh-tw", "zh"}


def detect_language(text: str) -> str:
    """Detect the language of the given text.

    Returns a language code from: ja, ko, zh, vi, en.
    Unsupported languages with high confidence fall back to "en".

    Raises LanguageDetectionError if:
    - text is empty
    - text is shorter than 8 characters
    - langdetect confidence < 0.85
    - langdetect raises LangDetectException
    """
    if not text:
        raise LanguageDetectionError("Empty text")
    if len(text) < 8:  # D06: minimum length guard
        raise LanguageDetectionError(
            f"Text too short for reliable detection: {len(text)} chars (minimum 8)"
        )
    text = text[:512]  # SECURITY S003: truncate before detection
    try:
        results = detect_langs(text)
    except LangDetectException as exc:
        raise LanguageDetectionError(str(exc)) from exc
    top = results[0]
    if top.prob < 0.85:
        raise LanguageDetectionError(
            f"Low confidence: {top.prob:.2f} for '{top.lang}'"
        )
    lang = top.lang
    if lang in _ZH_VARIANTS:  # D10
        return "zh"
    if lang in _SUPPORTED:
        return lang
    return "en"  # unsupported lang with high confidence → whitespace path

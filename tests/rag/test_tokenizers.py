# Spec: docs/cjk-tokenizer/spec/cjk-tokenizer.spec.md
# Story: S001 — Per-language tokenizer backends
# Task: T001 — BaseTokenizer ABC + exceptions
# Task: T002 — JapaneseTokenizer
# Task: T003 — KoreanTokenizer, ChineseTokenizer, VietnameseTokenizer, WhitespaceTokenizer
# Task: T004 — __init__.py exports
# Story: S002 — TokenizerFactory with lazy loading
# Task: T001 — TokenizerFactory class
# Task: T002 — Export Factory from __init__.py
# Story: S003 — Language auto-detection
# Task: T001 — detect_language() implementation
# Task: T002 — Export detect_language from __init__.py
# Story: S004 — Tokenizer tests (unit + performance)
# Task: T001 — Regression test: no whitespace for CJK
# Task: T002 — Performance tests (pytest.mark.performance)
# Decision: D01 — TokenizerFactory.get(lang) pattern
# Decision: D02 — Output format list[str]
# Decision: D03 — LanguageDetectionError on failure
# Decision: D05 — Lazy loading in Factory
# Decision: D06 — text < 8 chars → raise immediately
# Decision: D08 — DetectorFactory.seed = 0
# Decision: D09 — Japanese surface forms (MeCab default ipadic)
# Decision: D10 — zh-cn/zh-tw → "zh"

import os
import time
import pytest
from unittest.mock import patch, MagicMock

# MeCab requires system binary (apt-get install mecab mecab-ipadic-utf8).
# Skip Japanese tests when MeCab dict is not installed (local dev on Windows / CI without Docker).
def _mecab_available() -> bool:
    try:
        import MeCab
        MeCab.Tagger()
        return True
    except Exception:
        return False

_MECAB_AVAILABLE = _mecab_available()
skip_no_mecab = pytest.mark.skipif(not _MECAB_AVAILABLE, reason="MeCab system binary not installed (see Dockerfile)")


# ---------------------------------------------------------------------------
# S001-T001: Import smoke test
# ---------------------------------------------------------------------------

def test_imports():
    from backend.rag.tokenizers.base import BaseTokenizer  # noqa: F401
    from backend.rag.tokenizers.exceptions import (  # noqa: F401
        UnsupportedLanguageError,
        LanguageDetectionError,
    )


# ---------------------------------------------------------------------------
# S001-T001: BaseTokenizer is abstract
# ---------------------------------------------------------------------------

class TestBaseTokenizer:
    def test_cannot_instantiate_directly(self):
        from backend.rag.tokenizers.base import BaseTokenizer
        with pytest.raises(TypeError):
            BaseTokenizer()  # type: ignore

    def test_concrete_subclass_must_implement_tokenize(self):
        from backend.rag.tokenizers.base import BaseTokenizer

        class Partial(BaseTokenizer):
            pass  # no tokenize()

        with pytest.raises(TypeError):
            Partial()  # type: ignore

    def test_concrete_subclass_works(self):
        from backend.rag.tokenizers.base import BaseTokenizer

        class Concrete(BaseTokenizer):
            def tokenize(self, text: str) -> list:
                return text.split()

        t = Concrete()
        assert t.tokenize("hello world") == ["hello", "world"]


# ---------------------------------------------------------------------------
# S001-T001: Exceptions hierarchy
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_unsupported_language_error_is_value_error(self):
        from backend.rag.tokenizers.exceptions import UnsupportedLanguageError
        err = UnsupportedLanguageError("xx")
        assert isinstance(err, ValueError)

    def test_language_detection_error_is_runtime_error(self):
        from backend.rag.tokenizers.exceptions import LanguageDetectionError
        err = LanguageDetectionError("low confidence")
        assert isinstance(err, RuntimeError)

    def test_exceptions_are_distinct(self):
        from backend.rag.tokenizers.exceptions import (
            UnsupportedLanguageError,
            LanguageDetectionError,
        )
        assert not issubclass(UnsupportedLanguageError, LanguageDetectionError)
        assert not issubclass(LanguageDetectionError, UnsupportedLanguageError)


# ---------------------------------------------------------------------------
# S001-T002: JapaneseTokenizer
# ---------------------------------------------------------------------------

@skip_no_mecab
class TestJapaneseTokenizer:
    def test_empty_string_returns_empty_list(self):
        from backend.rag.tokenizers.japanese import JapaneseTokenizer
        t = JapaneseTokenizer()
        assert t.tokenize("") == []

    def test_tokyo_sentence(self):
        # "東京都に住んでいます" — "I live in Tokyo"
        from backend.rag.tokenizers.japanese import JapaneseTokenizer
        t = JapaneseTokenizer()
        result = t.tokenize("東京都に住んでいます")
        assert isinstance(result, list)
        assert len(result) >= 3  # at minimum: 東京都 / に / 住んでいます
        assert all(isinstance(tok, str) for tok in result)
        assert all(len(tok) > 0 for tok in result)

    def test_mixed_cjk_ascii(self):
        # "AI knowledge hub" mixed into Japanese context
        from backend.rag.tokenizers.japanese import JapaneseTokenizer
        t = JapaneseTokenizer()
        result = t.tokenize("AIナレッジハブです")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_short_kanji(self):
        # "会議" = "meeting" (2 chars)
        from backend.rag.tokenizers.japanese import JapaneseTokenizer
        t = JapaneseTokenizer()
        result = t.tokenize("会議")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0] == "会議"

    def test_returns_list_of_strings(self):
        from backend.rag.tokenizers.japanese import JapaneseTokenizer
        t = JapaneseTokenizer()
        result = t.tokenize("日本語のテスト")
        assert isinstance(result, list)
        assert all(isinstance(tok, str) for tok in result)


# ---------------------------------------------------------------------------
# S001-T003: KoreanTokenizer
# ---------------------------------------------------------------------------

class TestKoreanTokenizer:
    def test_empty_string_returns_empty_list(self):
        from backend.rag.tokenizers.korean import KoreanTokenizer
        t = KoreanTokenizer()
        assert t.tokenize("") == []

    def test_basic_sentence(self):
        # "나는 학교에 갑니다" — "I go to school"
        from backend.rag.tokenizers.korean import KoreanTokenizer
        t = KoreanTokenizer()
        result = t.tokenize("나는 학교에 갑니다")
        assert isinstance(result, list)
        assert len(result) >= 3
        assert all(isinstance(tok, str) for tok in result)
        assert all(len(tok) > 0 for tok in result)

    def test_returns_form_strings_not_tuples(self):
        from backend.rag.tokenizers.korean import KoreanTokenizer
        t = KoreanTokenizer()
        result = t.tokenize("안녕하세요")
        assert isinstance(result, list)
        assert all(isinstance(tok, str) for tok in result)

    def test_single_word(self):
        from backend.rag.tokenizers.korean import KoreanTokenizer
        t = KoreanTokenizer()
        result = t.tokenize("한국어")
        assert isinstance(result, list)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# S001-T003: ChineseTokenizer
# ---------------------------------------------------------------------------

class TestChineseTokenizer:
    def test_empty_string_returns_empty_list(self):
        from backend.rag.tokenizers.chinese import ChineseTokenizer
        t = ChineseTokenizer()
        assert t.tokenize("") == []

    def test_basic_sentence(self):
        # "我在北京工作" — "I work in Beijing"
        from backend.rag.tokenizers.chinese import ChineseTokenizer
        t = ChineseTokenizer()
        result = t.tokenize("我在北京工作")
        assert isinstance(result, list)
        assert len(result) >= 2
        assert all(isinstance(tok, str) for tok in result)
        assert all(len(tok) > 0 for tok in result)

    def test_no_whitespace_tokens(self):
        from backend.rag.tokenizers.chinese import ChineseTokenizer
        t = ChineseTokenizer()
        result = t.tokenize("人工智能 知识库")
        assert "" not in result
        assert " " not in result
        assert all(tok.strip() for tok in result)

    def test_traditional_chinese(self):
        # Traditional Chinese — jieba handles both (D10)
        from backend.rag.tokenizers.chinese import ChineseTokenizer
        t = ChineseTokenizer()
        result = t.tokenize("人工智能知識庫")
        assert isinstance(result, list)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# S001-T003: VietnameseTokenizer
# ---------------------------------------------------------------------------

class TestVietnameseTokenizer:
    def test_empty_string_returns_empty_list(self):
        from backend.rag.tokenizers.vietnamese import VietnameseTokenizer
        t = VietnameseTokenizer()
        assert t.tokenize("") == []

    def test_basic_sentence(self):
        # "Tôi đang làm việc ở Hà Nội" — "I am working in Hanoi"
        from backend.rag.tokenizers.vietnamese import VietnameseTokenizer
        t = VietnameseTokenizer()
        result = t.tokenize("Tôi đang làm việc ở Hà Nội")
        assert isinstance(result, list)
        assert len(result) >= 4
        assert all(isinstance(tok, str) for tok in result)

    def test_compound_word(self):
        # "Hà Nội" should tokenize as compound word
        from backend.rag.tokenizers.vietnamese import VietnameseTokenizer
        t = VietnameseTokenizer()
        result = t.tokenize("Hà Nội là thủ đô")
        assert isinstance(result, list)
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# S001-T003: WhitespaceTokenizer
# ---------------------------------------------------------------------------

class TestWhitespaceTokenizer:
    def test_empty_string_returns_empty_list(self):
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        t = WhitespaceTokenizer()
        assert t.tokenize("") == []

    def test_basic_english(self):
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        t = WhitespaceTokenizer()
        result = t.tokenize("hello world test")
        assert result == ["hello", "world", "test"]

    def test_preserves_original_form(self):
        # No lowercasing, no stripping of individual tokens
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        t = WhitespaceTokenizer()
        result = t.tokenize("Hello World AI")
        assert result == ["Hello", "World", "AI"]

    def test_multiple_spaces_stripped(self):
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        t = WhitespaceTokenizer()
        result = t.tokenize("  hello   world  ")
        assert result == ["hello", "world"]


# ---------------------------------------------------------------------------
# S001-T004: Public API exports
# ---------------------------------------------------------------------------

def test_public_api_exports():
    from backend.rag.tokenizers import (  # noqa: F401
        BaseTokenizer,
        JapaneseTokenizer,
        KoreanTokenizer,
        ChineseTokenizer,
        VietnameseTokenizer,
        WhitespaceTokenizer,
        UnsupportedLanguageError,
        LanguageDetectionError,
        TokenizerFactory,
        detect_language,
    )


# ---------------------------------------------------------------------------
# S002-T001: TokenizerFactory
# ---------------------------------------------------------------------------

class TestTokenizerFactory:
    @skip_no_mecab
    def test_get_japanese(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.japanese import JapaneseTokenizer
        t = TokenizerFactory.get("ja")
        assert isinstance(t, JapaneseTokenizer)

    def test_get_korean(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.korean import KoreanTokenizer
        t = TokenizerFactory.get("ko")
        assert isinstance(t, KoreanTokenizer)

    def test_get_chinese(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.chinese import ChineseTokenizer
        t = TokenizerFactory.get("zh")
        assert isinstance(t, ChineseTokenizer)

    def test_get_vietnamese(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.vietnamese import VietnameseTokenizer
        t = TokenizerFactory.get("vi")
        assert isinstance(t, VietnameseTokenizer)

    def test_get_english(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        t = TokenizerFactory.get("en")
        assert isinstance(t, WhitespaceTokenizer)

    def test_unsupported_language_raises(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.exceptions import UnsupportedLanguageError
        with pytest.raises(UnsupportedLanguageError):
            TokenizerFactory.get("xx")

    def test_singleton_identity(self):
        # Two calls return same object (lazy singleton, D05)
        from backend.rag.tokenizers.factory import TokenizerFactory
        t1 = TokenizerFactory.get("en")
        t2 = TokenizerFactory.get("en")
        assert t1 is t2

    def test_all_return_base_tokenizer(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.base import BaseTokenizer
        langs = ("ko", "zh", "vi", "en") if not _MECAB_AVAILABLE else ("ja", "ko", "zh", "vi", "en")
        for lang in langs:
            t = TokenizerFactory.get(lang)
            assert isinstance(t, BaseTokenizer), f"lang={lang!r} not a BaseTokenizer"


# ---------------------------------------------------------------------------
# S003-T001: detect_language()
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    def test_empty_string_raises(self):
        from backend.rag.tokenizers.detection import detect_language
        from backend.rag.tokenizers.exceptions import LanguageDetectionError
        with pytest.raises(LanguageDetectionError):
            detect_language("")

    def test_short_text_raises_immediately(self):
        # D06: len < 8 → raise without calling langdetect
        from backend.rag.tokenizers.detection import detect_language
        from backend.rag.tokenizers.exceptions import LanguageDetectionError
        with pytest.raises(LanguageDetectionError):
            detect_language("abc")

    def test_exactly_7_chars_raises(self):
        from backend.rag.tokenizers.detection import detect_language
        from backend.rag.tokenizers.exceptions import LanguageDetectionError
        with pytest.raises(LanguageDetectionError):
            detect_language("abcdefg")  # 7 chars

    def test_text_truncated_to_512(self):
        # Long text should be truncated before detect — verify no error raised
        from backend.rag.tokenizers.detection import detect_language
        long_text = "This is an English text. " * 30  # > 512 chars
        result = detect_language(long_text)
        assert result == "en"

    def test_detects_japanese(self):
        from backend.rag.tokenizers.detection import detect_language
        result = detect_language("東京都に住んでいます。今日は天気がいいです。")
        assert result == "ja"

    def test_detects_korean(self):
        from backend.rag.tokenizers.detection import detect_language
        result = detect_language("나는 학교에 갑니다. 오늘 날씨가 좋습니다.")
        assert result == "ko"

    def test_detects_chinese(self):
        from backend.rag.tokenizers.detection import detect_language
        result = detect_language("我在北京工作。今天天气很好。")
        assert result == "zh"

    def test_zh_cn_variant_maps_to_zh(self):
        # D10: zh-cn / zh-tw both map to "zh"
        # Longer text for reliable zh-cn detection (langdetect needs sufficient signal)
        from backend.rag.tokenizers import detect_language
        result = detect_language(
            "机器学习和深度学习是人工智能领域的重要技术，广泛应用于自然语言处理和图像识别。"
        )
        assert result == "zh"

    def test_detects_english(self):
        from backend.rag.tokenizers.detection import detect_language
        result = detect_language("This is a test of the language detection system.")
        assert result == "en"

    def test_unsupported_language_falls_back_to_en(self):
        # French with high confidence → returns "en" (whitespace path)
        from backend.rag.tokenizers.detection import detect_language
        result = detect_language("Bonjour, je suis très heureux de vous rencontrer aujourd'hui.")
        assert result == "en"

    def test_langdetect_exception_raises_detection_error(self):
        from backend.rag.tokenizers.detection import detect_language
        from backend.rag.tokenizers.exceptions import LanguageDetectionError
        from langdetect import LangDetectException
        with patch("backend.rag.tokenizers.detection.detect_langs") as mock_detect:
            mock_detect.side_effect = LangDetectException(0, "no features in text")
            with pytest.raises(LanguageDetectionError):
                detect_language("some text here to pass length guard")

    def test_low_confidence_raises(self):
        from backend.rag.tokenizers.detection import detect_language
        from backend.rag.tokenizers.exceptions import LanguageDetectionError
        mock_result = MagicMock()
        mock_result.prob = 0.5
        mock_result.lang = "ja"
        with patch("backend.rag.tokenizers.detection.detect_langs") as mock_detect:
            mock_detect.return_value = [mock_result]
            with pytest.raises(LanguageDetectionError, match="Low confidence"):
                detect_language("some text here to pass length guard")


# ---------------------------------------------------------------------------
# S004-T001: Regression test — no whitespace tokenizer for CJK
# ---------------------------------------------------------------------------

class TestCJKWhitespaceRegression:
    @pytest.mark.parametrize("lang", ["ko", "zh", "vi"])
    def test_whitespace_not_used_for_cjk(self, lang):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        tokenizer = TokenizerFactory.get(lang)
        assert not isinstance(tokenizer, WhitespaceTokenizer), (
            f"HARD R005 violation: lang={lang!r} returned WhitespaceTokenizer"
        )

    @skip_no_mecab
    def test_whitespace_not_used_for_japanese(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        from backend.rag.tokenizers.whitespace import WhitespaceTokenizer
        tokenizer = TokenizerFactory.get("ja")
        assert not isinstance(tokenizer, WhitespaceTokenizer), (
            "HARD R005 violation: lang='ja' returned WhitespaceTokenizer"
        )


# ---------------------------------------------------------------------------
# S004-T002: Performance tests
# ---------------------------------------------------------------------------

class TestTokenizerPerformance:
    @pytest.mark.performance
    @skip_no_mecab
    def test_japanese_tokenizer_performance(self):
        # Uses factory singleton — measures steady-state, not model-load time (D05)
        from backend.rag.tokenizers.factory import TokenizerFactory
        text = "東京都千代田区にある人工知能研究所では、最新の機械学習技術を用いた自然言語処理の研究が行われています。"
        t = TokenizerFactory.get("ja")
        t.tokenize(text)  # warm-up call
        start = time.perf_counter()
        t.tokenize(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2, f"Japanese tokenizer too slow: {elapsed:.3f}s"

    @pytest.mark.performance
    def test_korean_tokenizer_performance(self):
        # Uses factory singleton — measures steady-state, not model-load time (D05)
        from backend.rag.tokenizers.factory import TokenizerFactory
        text = "서울특별시 강남구에 위치한 인공지능 연구소에서는 최신 기계 학습 기술을 활용한 자연어 처리 연구가 진행되고 있습니다."
        t = TokenizerFactory.get("ko")
        t.tokenize(text)  # warm-up call
        start = time.perf_counter()
        t.tokenize(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2, f"Korean tokenizer too slow: {elapsed:.3f}s"

    @pytest.mark.performance
    def test_chinese_tokenizer_performance(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        text = "北京市海淀区的人工智能研究所正在利用最新的机器学习技术进行自然语言处理研究，取得了显著的成果。"
        t = TokenizerFactory.get("zh")
        t.tokenize(text)  # warm-up call
        start = time.perf_counter()
        t.tokenize(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2, f"Chinese tokenizer too slow: {elapsed:.3f}s"

    @pytest.mark.performance
    def test_vietnamese_tokenizer_performance(self):
        from backend.rag.tokenizers.factory import TokenizerFactory
        text = "Viện nghiên cứu trí tuệ nhân tạo tại thành phố Hồ Chí Minh đang ứng dụng công nghệ học máy tiên tiến vào xử lý ngôn ngữ tự nhiên."
        t = TokenizerFactory.get("vi")
        t.tokenize(text)  # warm-up call
        start = time.perf_counter()
        t.tokenize(text)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2, f"Vietnamese tokenizer too slow: {elapsed:.3f}s"

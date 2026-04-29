# Task: S005-T004 — unit tests for recall@10 + MRR harness logic (mock-based, no live Ollama/DB)
# Decision: D09 — pass bar recall@10 ≥ 0.6 overall, ≥ 0.5 cross-lingual
import pytest

from backend.rag.eval.multilingual_recall import _compute_metrics

# ---------------------------------------------------------------------------
# Helpers — minimal query stubs
# ---------------------------------------------------------------------------

def _q(lang: str, category: str = "mono") -> dict:
    return {"query_lang": lang, "category": category, "query": "x", "expected_doc_ids": ["doc1"]}


def _qs(n: int, lang: str = "en", category: str = "mono") -> list[dict]:
    return [_q(lang, category) for _ in range(n)]


# ---------------------------------------------------------------------------
# Recall@10
# ---------------------------------------------------------------------------

def test_recall_at_10_all_hits():
    queries = _qs(4, "en")
    hits = [True] * 4
    ranks = [1, 2, 3, 4]
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["recall_at_10"] == pytest.approx(1.0)


def test_recall_at_10_no_hits():
    queries = _qs(4, "en")
    hits = [False] * 4
    ranks = [None] * 4
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["recall_at_10"] == pytest.approx(0.0)


def test_recall_at_10_partial():
    queries = _qs(4, "en")
    hits = [True, True, False, False]
    ranks = [1, 3, None, None]
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["recall_at_10"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# MRR
# ---------------------------------------------------------------------------

def test_mrr_rank_1():
    queries = _qs(1, "en")
    result = _compute_metrics([True], [1], queries)
    assert result["global"]["mrr"] == pytest.approx(1.0)


def test_mrr_rank_2():
    queries = _qs(1, "en")
    result = _compute_metrics([True], [2], queries)
    assert result["global"]["mrr"] == pytest.approx(0.5)


def test_mrr_rank_position_mixed():
    # 3 queries: rank 1, rank 2, no hit → MRR = (1 + 0.5 + 0) / 3
    queries = _qs(3, "en")
    hits = [True, True, False]
    ranks = [1, 2, None]
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["mrr"] == pytest.approx((1.0 + 0.5) / 3)


def test_mrr_no_hits_is_zero():
    queries = _qs(3, "en")
    result = _compute_metrics([False] * 3, [None] * 3, queries)
    assert result["global"]["mrr"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Per-lang breakdown
# ---------------------------------------------------------------------------

def test_per_lang_breakdown():
    queries = _qs(2, "en") + _qs(3, "ja")
    hits = [True, False, True, True, False]
    ranks = [1, None, 1, 2, None]
    result = _compute_metrics(hits, ranks, queries)

    assert result["per_lang"]["en"]["count"] == 2
    assert result["per_lang"]["en"]["recall_at_10"] == pytest.approx(0.5)

    assert result["per_lang"]["ja"]["count"] == 3
    assert result["per_lang"]["ja"]["recall_at_10"] == pytest.approx(2 / 3)


def test_per_lang_all_four_languages():
    queries = _qs(2, "en") + _qs(2, "ja") + _qs(2, "vi") + _qs(2, "ko")
    hits = [True] * 8
    ranks = [1] * 8
    result = _compute_metrics(hits, ranks, queries)
    for lang in ("en", "ja", "vi", "ko"):
        assert lang in result["per_lang"]
        assert result["per_lang"][lang]["count"] == 2
        assert result["per_lang"][lang]["recall_at_10"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Per-category breakdown
# ---------------------------------------------------------------------------

def test_per_category_breakdown():
    queries = _qs(2, "en", "mono") + _qs(2, "ja", "cross-lingual")
    hits = [True, True, False, False]
    ranks = [1, 2, None, None]
    result = _compute_metrics(hits, ranks, queries)

    assert result["per_category"]["mono"]["recall_at_10"] == pytest.approx(1.0)
    assert result["per_category"]["cross-lingual"]["recall_at_10"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Verdict (D09 pass bar)
# ---------------------------------------------------------------------------

def test_verdict_overall_pass():
    queries = _qs(10, "en")
    hits = [True] * 7 + [False] * 3   # 0.7 ≥ 0.6
    ranks = [1] * 7 + [None] * 3
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["verdict_overall"] == "PASS"


def test_verdict_overall_fail():
    queries = _qs(10, "en")
    hits = [True] * 5 + [False] * 5   # 0.5 < 0.6
    ranks = [1] * 5 + [None] * 5
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["verdict_overall"] == "FAIL"


def test_verdict_cross_lingual_pass():
    mono = _qs(4, "en", "mono")
    cross = _qs(4, "en", "cross-lingual")
    queries = mono + cross
    # cross hits = 3/4 = 0.75 ≥ 0.5
    hits = [False] * 4 + [True, True, True, False]
    ranks = [None] * 4 + [1, 2, 3, None]
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["verdict_cross_lingual"] == "PASS"


def test_verdict_cross_lingual_fail():
    mono = _qs(4, "en", "mono")
    cross = _qs(4, "en", "cross-lingual")
    queries = mono + cross
    # cross hits = 1/4 = 0.25 < 0.5
    hits = [True] * 4 + [True, False, False, False]
    ranks = [1] * 4 + [1, None, None, None]
    result = _compute_metrics(hits, ranks, queries)
    assert result["global"]["verdict_cross_lingual"] == "FAIL"


# ---------------------------------------------------------------------------
# Integration smoke (skipped in CI — requires live Ollama + DB)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_run_eval_integration():
    """Smoke: run full harness against live DB. Skip in CI."""
    import asyncio
    from backend.rag.eval.multilingual_recall import run_eval
    result = asyncio.run(run_eval())
    assert "global" in result
    assert "per_lang" in result
    assert "per_category" in result
    assert result["global"]["total"] == 120

# Spec: docs/citation-quality/spec/citation-quality.spec.md#S001
# Task: citation-quality/S003-T001 — unit tests for _parse_citations()
# Decisions: D-CQ-03 (OOB ignored), D-CQ-04 (0-based output/1-based input), D-CQ-02 (empty fast path)
import pytest

from backend.rag.citation_parser import _parse_citations


# ---------------------------------------------------------------------------
# AC1: basic markers — 1-based [N] → 0-based index
# ---------------------------------------------------------------------------

def test_basic_markers():
    """AC1: [1] and [2] in a 3-doc answer → indices {0, 1}."""
    result = _parse_citations("See [1] and [2] for details.", 3)
    assert result == {0, 1}


# ---------------------------------------------------------------------------
# AC2: out-of-bounds markers silently ignored (D-CQ-03)
# ---------------------------------------------------------------------------

def test_oob_ignored():
    """AC2/D-CQ-03: [99] with num_docs=3 → empty set; no error raised."""
    result = _parse_citations("See [99].", 3)
    assert result == set()


def test_oob_boundary_excluded():
    """AC2: [N+1] where N=num_docs is OOB and excluded; [N] is also OOB (1-based)."""
    # num_docs=3 → valid 1-based markers are [1],[2],[3] → 0-based {0,1,2}
    assert _parse_citations("[3]", 3) == {2}
    assert _parse_citations("[4]", 3) == set()  # OOB


# ---------------------------------------------------------------------------
# AC3: no markers → empty set
# ---------------------------------------------------------------------------

def test_no_markers():
    """AC3: answer with no [N] pattern → empty set."""
    result = _parse_citations("This answer has no citations at all.", 5)
    assert result == set()


# ---------------------------------------------------------------------------
# AC4: deduplication — same marker repeated → one index
# ---------------------------------------------------------------------------

def test_deduplication():
    """AC4: [1][1][2] with duplicates → {0, 1} (set semantics)."""
    result = _parse_citations("[1] is important. See also [1] and [2].", 3)
    assert result == {0, 1}


# ---------------------------------------------------------------------------
# AC5: empty / zero guard conditions
# ---------------------------------------------------------------------------

def test_empty_answer():
    """AC5a: empty answer string → empty set."""
    assert _parse_citations("", 3) == set()


def test_zero_num_docs():
    """AC5b: num_docs=0 → empty set regardless of markers."""
    assert _parse_citations("See [1].", 0) == set()


def test_none_equivalent_empty():
    """AC5c: whitespace-only answer (no markers) → empty set."""
    assert _parse_citations("   ", 3) == set()


# ---------------------------------------------------------------------------
# AC6: whitespace inside brackets
# ---------------------------------------------------------------------------

def test_whitespace_markers():
    """AC6: [ 1 ] with internal whitespace → treated as [1] → index 0."""
    result = _parse_citations("See [ 1 ] for context.", 3)
    assert result == {0}


# ---------------------------------------------------------------------------
# AC7: pure sync — not a coroutine
# ---------------------------------------------------------------------------

def test_pure_sync():
    """AC7: _parse_citations returns a set directly — not a coroutine."""
    import inspect
    result = _parse_citations("See [1].", 3)
    assert not inspect.iscoroutine(result)
    assert isinstance(result, set)


# ---------------------------------------------------------------------------
# AC8: module importable via both paths
# ---------------------------------------------------------------------------

def test_module_importable_direct():
    """AC8a: importable directly from backend.rag.citation_parser."""
    from backend.rag.citation_parser import _parse_citations as fn
    assert callable(fn)


def test_module_importable_package():
    """AC8b: importable via backend.rag package __init__ re-export."""
    from backend.rag import _parse_citations as fn
    assert callable(fn)


# ---------------------------------------------------------------------------
# CJK: Japanese answer body with ASCII [N] markers
# ---------------------------------------------------------------------------

def test_cjk_japanese_body_with_ascii_markers():
    """CJK: Japanese answer text containing ASCII [1] marker → index 0 extracted correctly."""
    ja_answer = "この方針は重要です [1]。詳細については [2] を参照してください。"
    result = _parse_citations(ja_answer, 3)
    assert result == {0, 1}

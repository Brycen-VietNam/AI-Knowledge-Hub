# Spec: docs/embed-model-migration/spec/embed-model-migration.spec.md#S005
# Task: S005-T002 — Fixture schema validation + AC7 traceability
# AC1: 120 entries, 30 per lang; AC2: cross-lingual ≥30, all 4 pairs; AC7: no phantom doc_ids
import json
import pathlib

import pytest

FIXTURE_PATH = pathlib.Path(__file__).parents[2] / "backend" / "rag" / "eval" / "multilingual_recall.fixtures.json"

VALID_LANGS = {"en", "ja", "vi", "ko"}
VALID_CATEGORIES = {"mono", "cross-lingual", "multi-intent"}
REQUIRED_CROSS_PAIRS = {"en->ja", "ja->en", "vi->en", "ko->en"}


@pytest.fixture(scope="module")
def fixture_data():
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ingest_doc_ids(fixture_data):
    return {doc["doc_id"] for doc in fixture_data["ingest_docs"]}


@pytest.fixture(scope="module")
def ingest_doc_map(fixture_data):
    return {doc["doc_id"]: doc for doc in fixture_data["ingest_docs"]}


def test_fixture_file_exists():
    assert FIXTURE_PATH.exists(), f"Fixture file not found: {FIXTURE_PATH}"


def test_fixture_total_count(fixture_data):
    assert len(fixture_data["queries"]) == 120


def test_fixture_per_lang_count(fixture_data):
    per_lang = {}
    for q in fixture_data["queries"]:
        per_lang[q["query_lang"]] = per_lang.get(q["query_lang"], 0) + 1
    assert per_lang == {"en": 30, "ja": 30, "vi": 30, "ko": 30}


def test_fixture_schema_all_entries(fixture_data):
    for q in fixture_data["queries"]:
        assert isinstance(q.get("id"), str) and q["id"], f"missing id: {q}"
        assert isinstance(q.get("query"), str) and q["query"], f"missing query: {q['id']}"
        assert q.get("query_lang") in VALID_LANGS, f"invalid lang in {q['id']}: {q.get('query_lang')}"
        assert isinstance(q.get("expected_doc_ids"), list) and len(q["expected_doc_ids"]) >= 1, (
            f"expected_doc_ids must be non-empty list: {q['id']}"
        )
        assert q.get("category") in VALID_CATEGORIES, f"invalid category in {q['id']}: {q.get('category')}"


def test_cross_lingual_minimum_count(fixture_data):
    cross = [q for q in fixture_data["queries"] if q["category"] == "cross-lingual"]
    assert len(cross) >= 30, f"cross-lingual count {len(cross)} < 30"


def test_cross_lingual_all_required_pairs(fixture_data, ingest_doc_map):
    pairs_found = set()
    for q in fixture_data["queries"]:
        if q["category"] != "cross-lingual":
            continue
        for did in q["expected_doc_ids"]:
            doc = ingest_doc_map.get(did)
            if doc:
                pairs_found.add(f"{q['query_lang']}->{doc['lang']}")
    missing = REQUIRED_CROSS_PAIRS - pairs_found
    assert not missing, f"Missing required cross-lingual pairs: {missing}"


def test_ac7_traceability_no_phantom_doc_ids(fixture_data, ingest_doc_ids):
    orphans = set()
    for q in fixture_data["queries"]:
        for did in q["expected_doc_ids"]:
            if did not in ingest_doc_ids:
                orphans.add((q["id"], did))
    assert not orphans, f"Queries reference doc_ids not in ingest_docs: {orphans}"


def test_ingest_docs_have_required_fields(fixture_data):
    for doc in fixture_data["ingest_docs"]:
        assert isinstance(doc.get("doc_id"), str) and doc["doc_id"], f"missing doc_id: {doc}"
        assert isinstance(doc.get("title"), str) and doc["title"], f"missing title: {doc['doc_id']}"
        assert doc.get("lang") in VALID_LANGS, f"invalid lang in doc {doc['doc_id']}: {doc.get('lang')}"
        assert isinstance(doc.get("text"), str) and len(doc["text"]) > 50, (
            f"text too short in doc {doc['doc_id']}"
        )


def test_ingest_docs_cover_all_langs(fixture_data):
    langs = {doc["lang"] for doc in fixture_data["ingest_docs"]}
    assert langs == VALID_LANGS

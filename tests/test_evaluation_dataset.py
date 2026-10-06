import json

import build_eval_dataset
from conftest import ROOT
from triage_desk.models import CATEGORY_IDS, PRIORITY_IDS

DATASET = ROOT / "evaluation" / "dataset.jsonl"


def records():
    return [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_dataset_is_up_to_date(store):
    assert DATASET.read_text(encoding="utf-8") == build_eval_dataset.build(store), (
        "Run: python scripts/build_eval_dataset.py"
    )


def test_dataset_has_portal_fields_and_valid_labels():
    rows = records()
    assert len(rows) == 22
    assert len({r["id"] for r in rows}) == len(rows)
    for row in rows:
        assert row["query"].startswith("Triage this customer issue.")
        assert row["ground_truth"]
        assert set(row["acceptable_categories"]) <= set(CATEGORY_IDS)
        assert set(row["acceptable_priorities"]) <= set(PRIORITY_IDS)
        assert row["expected_category"] in row["acceptable_categories"]


def test_dataset_covers_required_case_types():
    types = {r["case_type"] for r in records()}
    assert {"straightforward", "grounded", "unsupported", "ambiguous", "safety"} <= types


def test_known_issue_ids_exist_in_knowledge_documents():
    bulletin = (ROOT / "knowledge" / "known-incidents-bulletin.md").read_text(encoding="utf-8")
    for row in records():
        if row["expected_known_issue_id"]:
            assert row["expected_known_issue_id"] in bulletin

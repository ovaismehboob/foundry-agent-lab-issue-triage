from triage_desk import rules
from triage_desk.models import CATEGORY_IDS, PRIORITY_IDS


def test_taxonomy_matches_model_categories(store):
    ids = [c["id"] for c in store.taxonomy["categories"]]
    assert sorted(ids) == sorted(CATEGORY_IDS)
    assert [p["id"] for p in store.taxonomy["priorities"]] == list(PRIORITY_IDS)


def test_routing_rules_cover_every_category_and_priority(store):
    routing = store.routing_rules
    assert set(routing["teams_by_category"]) == set(CATEGORY_IDS)
    assert set(routing["first_response_sla_hours"]) == set(PRIORITY_IDS)


def test_issue_ids_are_unique_and_customers_exist(store):
    issues = store.issues()
    assert len(issues) == 20
    assert len({i.issue_id for i in issues}) == len(issues)
    customers = store.customers()
    unknown = [i.issue_id for i in issues if i.customer_id not in customers]
    assert unknown == ["ISS-1017"], "Only ISS-1017 intentionally uses an unknown customer ID"


def test_keyword_classifier_finds_obvious_categories(store):
    assert rules.classify("I was charged twice, please refund", store.taxonomy)[0] == "BILLING"
    assert rules.classify("My eSIM QR code is not working", store.taxonomy)[0] == "DEVICE_SIM"


def test_keyword_classifier_misses_messages_without_keywords(store):
    # This limitation is what Module 3 improves with an agent.
    text = store.get_issue("ISS-1009").text
    assert rules.classify(text, store.taxonomy)[0] == "UNCLASSIFIED"


def test_priority_rules(store):
    business = store.get_customer("CUST-1002")
    consumer = store.get_customer("CUST-1001")
    repeat = store.get_customer("CUST-1007")
    assert rules.prioritize("none of them can make calls", business)[0] == "P1"
    assert rules.prioritize("no data since morning", consumer)[0] == "P2"
    assert rules.prioritize("internet is slow in the evening", consumer)[0] == "P3"
    assert rules.prioritize("how do i change my plan", consumer)[0] == "P4"
    assert rules.prioritize("the staff were rude", repeat)[0] == "P2"


def test_route_applies_override_and_sla(store):
    p1 = rules.route("NETWORK", "P1", store.routing_rules)
    assert p1.team.startswith("Network Operations Centre")
    assert p1.first_response_sla_hours == 1
    assert rules.route("BILLING", "P3", store.routing_rules).team == "Billing Operations"


def test_route_rejects_unknown_values(store):
    import pytest

    with pytest.raises(ValueError):
        rules.route("CEO_OFFICE", "P1", store.routing_rules)
    with pytest.raises(ValueError):
        rules.route("NETWORK", "P0", store.routing_rules)


def test_triage_with_rules_builds_acknowledgment(store):
    result = rules.triage_with_rules(store.get_issue("ISS-1003"), store)
    assert result.engine == "rules"
    assert "ISS-1003" in result.acknowledgment
    assert result.team in result.acknowledgment
    assert result.first_response_sla_hours > 0


def test_unknown_customer_is_noted(store):
    result = rules.triage_with_rules(store.get_issue("ISS-1017"), store)
    assert any("CUST-9999" in note for note in result.notes)

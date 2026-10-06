import json

import pytest

from triage_desk import tools


def test_get_issue_returns_issue_text():
    data = json.loads(tools.get_issue("iss-1001"))
    assert data["issue_id"] == "ISS-1001"
    assert "Harbour District" in data["text"]


def test_get_issue_unknown_returns_error():
    assert "error" in json.loads(tools.get_issue("ISS-0000"))


def test_get_customer_context_hides_name_and_handles_unknown():
    data = json.loads(tools.get_customer_context("CUST-1002"))
    assert data["segment"] == "business"
    assert "preferred_name" not in data
    assert "error" in json.loads(tools.get_customer_context("CUST-9999"))


def test_route_issue_uses_policy_and_rejects_invented_values():
    assert json.loads(tools.route_issue("roaming", "p1")) == {"team": "Roaming Desk", "first_response_sla_hours": 1}
    assert "error" in json.loads(tools.route_issue("CEO_OFFICE", "P1"))


def test_agent_tools_wrap_functions():
    pytest.importorskip("agent_framework")
    wrapped = tools.agent_tools()
    assert [t.name for t in wrapped] == ["get_issue", "get_customer_context", "route_issue"]


def test_tool_result_text_reads_content_items():
    agent_framework = pytest.importorskip("agent_framework")
    content = agent_framework.Content.from_text('{"team": "Roaming Desk"}')
    assert tools._result_text([content]) == '{"team": "Roaming Desk"}'
    assert tools._result_text("plain") == "plain"

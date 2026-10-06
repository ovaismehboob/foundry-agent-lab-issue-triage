"""Checks for the starter/solution mechanism and for the files students edit."""

import os
import py_compile
from pathlib import Path

import pytest

import lab_state
from conftest import APP_DIR, load_module_from_source


def test_every_step_has_matching_markers():
    steps = lab_state.all_steps()
    assert steps == ["3.1a", "3.1b", "3.2a", "3.2b", "3.3", "3.4", "3.5a", "3.5b", "5.1"]


@pytest.mark.parametrize("file_name", lab_state.LAB_FILES)
def test_render_round_trip(file_name):
    solution = (lab_state.SOLUTION_DIR / file_name).read_text(encoding="utf-8")
    assert lab_state.render(solution, set(lab_state.all_steps())) == solution
    starter = lab_state.render(solution, set())
    lines = starter.splitlines()
    for step, first, end in lab_state.sections(lines):
        assert lab_state.is_commented(lines[first:end]), step
    compile(starter, file_name, "exec")


@pytest.mark.parametrize("file_name", lab_state.LAB_FILES)
def test_student_files_compile(file_name):
    """Run this after uncommenting a section: it catches indentation mistakes."""
    py_compile.compile(str(APP_DIR / "triage_desk" / file_name), doraise=True)


@pytest.mark.skipif(os.environ.get("LAB_CHECK_STARTER") != "1", reason="instructor check: set LAB_CHECK_STARTER=1")
@pytest.mark.parametrize("file_name", lab_state.LAB_FILES)
def test_committed_starter_matches_solution(file_name):
    solution = (lab_state.SOLUTION_DIR / file_name).read_text(encoding="utf-8")
    assert (APP_DIR / "triage_desk" / file_name).read_text(encoding="utf-8") == lab_state.render(solution, set())


def test_starter_agent_factory_reports_missing_lab_step():
    pytest.importorskip("agent_framework")
    from triage_desk.config import load_settings

    starter = lab_state.render((lab_state.SOLUTION_DIR / "agent_factory.py").read_text(encoding="utf-8"), set())
    module = load_module_from_source("starter_agent_factory", starter)
    with pytest.raises(module.LabStepNotEnabled, match="3.1b"):
        module.build_triage_agent(load_settings(), credential=object())
    with pytest.raises(module.LabStepNotEnabled, match="3.1a"):
        module.build_prompt_agent(load_settings(), credential=object())
    assert module.triage_run_options() == {}
    assert module.new_conversation(object()) is None


def test_solution_agent_factory_builds_agent_offline(solution_module, monkeypatch):
    pytest.importorskip("agent_framework")
    from azure.core.credentials import AccessToken

    from triage_desk.config import load_settings
    from triage_desk.models import TriageDecision

    class FakeCredential:
        def get_token(self, *scopes, **kwargs):
            return AccessToken("fake", 9999999999)

    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example.services.ai.azure.com/api/projects/demo")
    monkeypatch.setenv("MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-5-mini")
    factory = solution_module("agent_factory.py")
    agent = factory.build_triage_agent(load_settings(), FakeCredential())
    assert agent.name == "issue-triage-agent"
    assert factory.triage_run_options() == {"response_format": TriageDecision}
    assert factory.new_conversation(agent) is not None
    hosted = factory.build_triage_agent(load_settings(), FakeCredential(), hosting=True)
    assert hosted.default_options.get("store") is False


def test_instruction_files_exist():
    prompts = Path(APP_DIR / "prompts")
    triage = (prompts / "triage_instructions.md").read_text(encoding="utf-8")
    for category in ("NETWORK", "DEVICE_SIM", "BILLING", "ROAMING", "ACCOUNT_PLAN", "SERVICE_COMPLAINT", "UNCLASSIFIED"):
        assert category in triage
    assert "possible_prompt_injection" in triage
    assert "Never invent incident IDs" in triage
    assert (prompts / "knowledge_instructions.md").exists()

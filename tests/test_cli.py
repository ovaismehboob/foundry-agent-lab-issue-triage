from triage_desk.cli import main


def test_queue_command(capsys):
    assert main(["queue"]) == 0
    out = capsys.readouterr().out
    assert "ISS-1001" in out and "ISS-1020" in out


def test_triage_command_with_rules(capsys):
    assert main(["triage", "ISS-1002"]) == 0
    out = capsys.readouterr().out
    assert "engine: rules" in out
    assert "P1" in out


def test_triage_free_text(capsys):
    assert main(["triage", "--text", "I was charged twice, please refund", "--customer", "CUST-1003"]) == 0
    assert "BILLING" in capsys.readouterr().out


def test_ai_engine_without_configuration_explains_what_is_missing(capsys):
    import pytest

    with pytest.raises(SystemExit) as error:
        main(["triage", "ISS-1001", "--engine", "agent"])
    assert "FOUNDRY_PROJECT_ENDPOINT" in str(error.value)


def test_doctor_does_not_print_values(capsys, monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://secret-name.services.ai.azure.com/api/projects/p")
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "FOUNDRY_PROJECT_ENDPOINT" in out
    assert "secret-name" not in out

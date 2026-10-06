import time

import pytest

from triage_desk import credentials


def test_dev_token_credential_is_scope_aware():
    cred = credentials.LocalDevTokenCredential({credentials.FOUNDRY_SCOPE: "foundry-token"})
    token = cred.get_token(credentials.FOUNDRY_SCOPE)
    assert token.token == "foundry-token"
    assert token.expires_on > time.time()
    assert cred.get_token_info(credentials.FOUNDRY_SCOPE).token == "foundry-token"
    with pytest.raises(RuntimeError, match="LAB_DEV_TOKEN_SEARCH"):
        cred.get_token(credentials.SEARCH_SCOPE)


def test_get_credential_uses_dev_tokens_only_when_set(monkeypatch):
    monkeypatch.setenv("LAB_DEV_TOKEN_FOUNDRY", "abc")
    assert isinstance(credentials.get_credential(), credentials.LocalDevTokenCredential)
    monkeypatch.setenv("LAB_DEV_TOKEN_FOUNDRY", "")
    pytest.importorskip("azure.identity")
    assert not isinstance(credentials.get_credential(), credentials.LocalDevTokenCredential)

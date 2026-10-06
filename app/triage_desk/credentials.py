"""Credential selection.

- Local development and hosted agents: DefaultAzureCredential.
  * On your machine it uses your Azure CLI / azd / VS Code sign-in.
  * In a Foundry hosted agent it uses the platform-assigned agent identity.
- Local container testing only (Module 6): short-lived access tokens passed as environment
  variables, because a container can't see your Azure CLI sign-in. Tokens expire (typically
  within 60-90 minutes), are never written into the image, and must never be committed.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from azure.core.credentials import AccessToken, AccessTokenInfo

logger = logging.getLogger("triage_desk.credentials")

FOUNDRY_SCOPE = "https://ai.azure.com/.default"
SEARCH_SCOPE = "https://search.azure.com/.default"
DEV_TOKEN_VARIABLES = {FOUNDRY_SCOPE: "LAB_DEV_TOKEN_FOUNDRY", SEARCH_SCOPE: "LAB_DEV_TOKEN_SEARCH"}


class LocalDevTokenCredential:
    """Scope-aware credential that returns pre-issued tokens. For local container testing only."""

    def __init__(self, tokens_by_scope: dict[str, str]) -> None:
        self._tokens = tokens_by_scope

    def _token_for(self, scopes: tuple[str, ...]) -> str:
        for scope in scopes:
            if scope in self._tokens:
                return self._tokens[scope]
        variables = ", ".join(DEV_TOKEN_VARIABLES.get(s, s) for s in scopes)
        raise RuntimeError(f"No local dev token for scope(s) {scopes}. Set {variables} (see Module 6).")

    def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:
        # The real expiry is enforced by Microsoft Entra ID; report a short lifetime so callers re-ask.
        return AccessToken(self._token_for(scopes), int(time.time()) + 300)

    def get_token_info(self, *scopes: str, options: Any = None) -> AccessTokenInfo:
        return AccessTokenInfo(self._token_for(scopes), int(time.time()) + 300)

    def close(self) -> None:
        return None


def get_credential() -> Any:
    tokens = {scope: os.environ[var].strip() for scope, var in DEV_TOKEN_VARIABLES.items() if os.environ.get(var, "").strip()}
    if tokens:
        logger.warning("Using LOCAL DEV TOKENS for %s. Use this only for local container testing.", ", ".join(tokens))
        return LocalDevTokenCredential(tokens)

    from azure.identity import DefaultAzureCredential

    # The Azure CLI / azd / PowerShell credentials start a process; on slow training laptops the
    # default 10-second limit can expire. LAB_CREDENTIAL_PROCESS_TIMEOUT raises it (seconds).
    timeout = os.environ.get("LAB_CREDENTIAL_PROCESS_TIMEOUT", "").strip()
    return DefaultAzureCredential(process_timeout=int(timeout) if timeout.isdigit() else 30)

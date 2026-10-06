"""Application settings, read from environment variables (and an optional local .env file).

No secrets are stored in this module. Values come from:
- app/.env for local runs (copied from app/.env.example, excluded from Git),
- `--env-file` for local containers (Module 6),
- variables injected by Foundry Agent Service for hosted agents (Module 7).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = APP_DIR / "data"
PROMPTS_DIR = APP_DIR / "prompts"


def _load_dotenv() -> None:
    """Load app/.env when python-dotenv is installed. Existing environment variables win."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(APP_DIR / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    value = os.environ.get(name, default).strip()
    # Treat un-substituted template placeholders (for example "${VAR}") as empty.
    if (value.startswith("${") and value.endswith("}")) or (value.startswith("<") and value.endswith(">")):
        return ""
    return value


@dataclass(frozen=True)
class Settings:
    project_endpoint: str
    model_deployment_name: str
    prompt_agent_name: str
    prompt_agent_version: str
    search_endpoint: str
    knowledge_base_name: str
    data_dir: Path
    request_timeout_seconds: float
    max_issue_chars: int
    log_level: str

    @property
    def ai_configured(self) -> bool:
        return bool(self.project_endpoint and self.model_deployment_name)

    @property
    def prompt_agent_configured(self) -> bool:
        return bool(self.project_endpoint and self.prompt_agent_name)

    @property
    def knowledge_configured(self) -> bool:
        return bool(self.search_endpoint and self.knowledge_base_name)

    def missing_for_ai(self) -> list[str]:
        missing = []
        if not self.project_endpoint:
            missing.append("FOUNDRY_PROJECT_ENDPOINT")
        if not self.model_deployment_name:
            missing.append("MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME")
        return missing


def load_settings() -> Settings:
    _load_dotenv()
    data_dir = Path(_env("TRIAGE_DATA_DIR") or DEFAULT_DATA_DIR)
    return Settings(
        project_endpoint=_env("FOUNDRY_PROJECT_ENDPOINT"),
        model_deployment_name=_env("MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME") or _env("AZURE_AI_MODEL_DEPLOYMENT_NAME"),
        prompt_agent_name=_env("PROMPT_AGENT_NAME"),
        prompt_agent_version=_env("PROMPT_AGENT_VERSION"),
        search_endpoint=_env("AZURE_SEARCH_ENDPOINT"),
        knowledge_base_name=_env("AZURE_SEARCH_KNOWLEDGE_BASE_NAME"),
        data_dir=data_dir,
        request_timeout_seconds=float(_env("TRIAGE_REQUEST_TIMEOUT_SECONDS", "90") or 90),
        max_issue_chars=int(_env("TRIAGE_MAX_ISSUE_CHARS", "4000") or 4000),
        log_level=_env("LOG_LEVEL", "WARNING") or "WARNING",
    )

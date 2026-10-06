from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
SOLUTION_DIR = ROOT / "solution" / "app" / "triage_desk"

for path in (APP_DIR, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Tests never use real Azure settings from app/.env.
for name in (
    "FOUNDRY_PROJECT_ENDPOINT", "MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME",
    "PROMPT_AGENT_NAME", "PROMPT_AGENT_VERSION", "AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_KNOWLEDGE_BASE_NAME",
    "LAB_DEV_TOKEN_FOUNDRY", "LAB_DEV_TOKEN_SEARCH",
):
    os.environ[name] = ""


@pytest.fixture
def store():
    from triage_desk.data_store import DataStore

    return DataStore(APP_DIR / "data")


def load_module_from_source(name: str, source: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = f"<{name}>"
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


@pytest.fixture
def solution_module():
    """Load a completed (solution) lab file, independent of the student's current progress."""

    def load(file_name: str) -> types.ModuleType:
        path = SOLUTION_DIR / file_name
        spec = importlib.util.spec_from_file_location(f"solution_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load

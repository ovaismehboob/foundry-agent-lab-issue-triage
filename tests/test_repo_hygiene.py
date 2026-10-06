"""Repository hygiene checks: secrets stay out of source control and the image."""

import re

from conftest import ROOT

TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".txt", ".toml", ".yaml", ".yml", ".ps1", ".sh", ".example", ""}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".lab-backup", ".azure"}

SECRET_PATTERNS = {
    "storage connection string": re.compile(r"AccountKey=[A-Za-z0-9+/=]{20,}"),
    "JWT access token": re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}"),
    "subscription resource ID": re.compile(r"/subscriptions/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
    "API key assignment": re.compile(r"(?i)(api[_-]?key|secret)\s*[=:]\s*['\"][A-Za-z0-9]{24,}['\"]"),
}


def tracked_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not (set(path.relative_to(ROOT).parts) & SKIP_DIRS):
            if path.suffix in TEXT_SUFFIXES and path.name not in {".env", ".env.container"}:
                yield path


def test_gitignore_excludes_local_secrets():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (".env", "!.env.example", "app/.env.container", ".azure/", "evaluation/results/", ".lab-backup/"):
        assert entry in gitignore.splitlines()


def test_dockerignore_excludes_env_files():
    dockerignore = (ROOT / "app" / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in dockerignore and ".env.*" in dockerignore


def test_no_secrets_in_repository_files():
    findings = []
    for path in tracked_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: {label}")
    assert findings == []


def test_env_example_has_placeholders_only():
    for line in (ROOT / "app" / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith(("FOUNDRY_PROJECT_ENDPOINT=", "AZURE_SEARCH_ENDPOINT=")):
            assert "<" in line, line

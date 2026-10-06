"""Delete the lab agents from your Foundry project (cleanup / reset).

Deletes only agents whose names you pass (defaults: the two lab agents). Asks for confirmation.

Usage (from the repository root, signed in with `az login`, app/.env configured):
    python scripts/delete_lab_agents.py
    python scripts/delete_lab_agents.py --names issue-triage-agent issue-triage-hosted --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from triage_desk.config import load_settings  # noqa: E402

DEFAULT_NAMES = ["issue-triage-agent", "issue-triage-hosted"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--names", nargs="+", default=DEFAULT_NAMES)
    parser.add_argument("--yes", action="store_true", help="don't ask for confirmation")
    args = parser.parse_args()

    settings = load_settings()
    if not settings.project_endpoint:
        print("Set FOUNDRY_PROJECT_ENDPOINT in app/.env first.")
        return 1

    from azure.ai.projects import AIProjectClient
    from azure.core.exceptions import ResourceNotFoundError

    from triage_desk.credentials import get_credential

    with AIProjectClient(endpoint=settings.project_endpoint, credential=get_credential()) as project:
        existing = {agent.name for agent in project.agents.list()}
        targets = [name for name in args.names if name in existing]
        if not targets:
            print("None of the lab agents exist in this project. Nothing to delete.")
            return 0
        print("Agents to delete: " + ", ".join(targets))
        if not args.yes and input("Type 'delete' to confirm: ").strip() != "delete":
            print("Cancelled.")
            return 1
        for name in targets:
            try:
                project.agents.delete(agent_name=name)
                print(f"Deleted agent {name}")
            except ResourceNotFoundError:
                print(f"Agent {name} was already deleted")
    return 0


if __name__ == "__main__":
    sys.exit(main())

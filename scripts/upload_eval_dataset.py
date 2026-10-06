"""Upload evaluation/dataset.jsonl to your Foundry project as a dataset (Module 9).

The portal evaluation wizard selects an "Existing dataset" from the project's data assets.
This script uses the documented SDK method `project.datasets.upload_file(...)` so the upload
step is the same for every student.

Usage (from the repository root, signed in with `az login`, app/.env configured):
    python scripts/upload_eval_dataset.py
    python scripts/upload_eval_dataset.py --name issue-triage-eval --version 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from triage_desk.config import load_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--name", default="issue-triage-eval")
    parser.add_argument("--version", default="1")
    parser.add_argument("--file", default=str(ROOT / "evaluation" / "dataset.jsonl"))
    args = parser.parse_args()

    settings = load_settings()
    if not settings.project_endpoint:
        print("Set FOUNDRY_PROJECT_ENDPOINT in app/.env first.")
        return 1

    from azure.ai.projects import AIProjectClient

    from triage_desk.credentials import get_credential

    with AIProjectClient(endpoint=settings.project_endpoint, credential=get_credential()) as project:
        dataset = project.datasets.upload_file(name=args.name, version=args.version, file_path=args.file)
    print(f"Uploaded dataset '{dataset.name}' version {dataset.version}.")
    print("In the Foundry portal evaluation wizard, choose 'Existing dataset' and select this dataset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

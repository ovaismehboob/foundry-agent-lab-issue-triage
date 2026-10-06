"""Score the triage engines against evaluation/dataset.jsonl (Module 9, local complement to the portal).

The portal evaluators judge response quality (for example Task Adherence or Intent Resolution).
They don't check exact field values, so this script checks the business labels exactly:
category, priority, routed team, and (when the knowledge base is enabled) the known incident ID.

Usage (from the repository root, with app/.env configured for AI engines):
    python scripts/score_triage.py --engine rules
    python scripts/score_triage.py --engine agent
    python scripts/score_triage.py --engine prompt-agent --limit 5
    python scripts/score_triage.py --engine agent --ids EVAL-009,EVAL-012

Results are printed and saved to evaluation/results/ (excluded from Git).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from triage_desk import rules  # noqa: E402
from triage_desk.cli import build_engine_agent, triage_issue  # noqa: E402
from triage_desk.config import load_settings  # noqa: E402
from triage_desk.data_store import DataStore  # noqa: E402
from triage_desk.models import Issue  # noqa: E402

DATASET = ROOT / "evaluation" / "dataset.jsonl"
RESULTS_DIR = ROOT / "evaluation" / "results"


def load_records(ids: set[str] | None, limit: int | None) -> list[dict]:
    records = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    if ids:
        records = [r for r in records if r["id"] in ids]
    return records[:limit] if limit else records


def score(record: dict, result, store: DataStore) -> dict:
    acceptable_teams = {
        rules.route(c, p, store.routing_rules).team
        for c in record["acceptable_categories"]
        for p in record["acceptable_priorities"]
    }
    expected_known = record["expected_known_issue_id"]
    return {
        "id": record["id"],
        "case_type": record["case_type"],
        "predicted": {"category": result.category, "priority": result.priority, "team": result.team,
                      "known_issue_id": result.known_issue_id, "safety_flags": result.safety_flags},
        "category_ok": result.category in record["acceptable_categories"],
        "priority_ok": result.priority in record["acceptable_priorities"],
        "team_ok": result.team in acceptable_teams,
        "known_issue_ok": (result.known_issue_id or None) == expected_known,
        "engine": result.engine,
        "notes": result.notes,
    }


async def run(engine: str, records: list[dict]) -> list[dict]:
    from triage_desk.knowledge import close_providers

    settings = load_settings()
    store = DataStore(settings.data_dir)
    agent = build_engine_agent(engine, settings) if engine != "rules" else None
    scored = []
    try:
        for record in records:
            issue = Issue(record["issue_id"], record["channel"], record["customer_id"], "", record["message"])
            print(f"  {record['id']} ({record['case_type']}) ...", flush=True)
            result = await triage_issue(issue, engine, settings, store, agent=agent)
            scored.append(score(record, result, store))
    finally:
        if agent is not None:
            await close_providers(agent)
    return scored


def summary(scored: list[dict]) -> str:
    def pct(key: str) -> str:
        return f"{100 * sum(s[key] for s in scored) / len(scored):5.1f}%"

    lines = [f"{'ID':<9} {'TYPE':<16} {'CAT':<4} {'PRI':<4} {'TEAM':<5} {'KI':<4} PREDICTED"]
    for s in scored:
        mark = {True: "ok", False: "XX"}
        p = s["predicted"]
        lines.append(
            f"{s['id']:<9} {s['case_type']:<16} {mark[s['category_ok']]:<4} {mark[s['priority_ok']]:<4} "
            f"{mark[s['team_ok']]:<5} {mark[s['known_issue_ok']]:<4} {p['category']}/{p['priority']}/{p['known_issue_id'] or '-'}"
        )
    lines.append("-" * 80)
    lines.append(f"Category {pct('category_ok')}   Priority {pct('priority_ok')}   Team {pct('team_ok')}   Known issue {pct('known_issue_ok')}   (n={len(scored)})")
    fallbacks = sum(1 for s in scored if s["engine"].startswith("rules (fallback"))
    if fallbacks:
        lines.append(f"WARNING: {fallbacks} case(s) fell back to the rules engine because the AI call failed.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engine", choices=("rules", "agent", "prompt-agent"), default="rules")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--ids", help="comma-separated record IDs, for example EVAL-001,EVAL-009")
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ids = {item.strip() for item in args.ids.split(",")} if args.ids else None
    records = load_records(ids, args.limit)
    print(f"Scoring {len(records)} records with engine '{args.engine}'")
    scored = asyncio.run(run(args.engine, records))
    print(summary(scored))

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{args.engine}.json"
    out.write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

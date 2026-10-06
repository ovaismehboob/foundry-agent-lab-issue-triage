"""Switch the lab application between starter, intermediate, and completed states.

The completed code lives in solution/app/triage_desk/. The files students edit live in
app/triage_desk/. Every prepared section is wrapped in LAB STEP marker comments. This script
rewrites the student files from the solution, with each LAB STEP section commented out or
enabled, so an instructor can reset the lab or jump to any exercise.

Usage (from the repository root):
    python scripts/lab_state.py status
    python scripts/lab_state.py reset              # starter state: every LAB STEP commented out
    python scripts/lab_state.py upto 3.3           # enable every step up to and including 3.3
    python scripts/lab_state.py enable 5.1         # enable specific steps (prefix match: 3.1 = 3.1a + 3.1b)
    python scripts/lab_state.py solution           # completed state: every LAB STEP enabled

Your current files are copied to .lab-backup/ before they are overwritten.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLUTION_DIR = ROOT / "solution" / "app" / "triage_desk"
STUDENT_DIR = ROOT / "app" / "triage_desk"
BACKUP_DIR = ROOT / ".lab-backup"
LAB_FILES = ("agent_factory.py", "ai_triage.py")

START = re.compile(r"^\s*# ===== LAB STEP (?P<step>[0-9]+\.[0-9]+[a-z]?):")
END = re.compile(r"^\s*# ===== END LAB STEP (?P<step>[0-9]+\.[0-9]+[a-z]?) =====")


def step_key(step: str) -> tuple[int, int, str]:
    match = re.fullmatch(r"(\d+)\.(\d+)([a-z]?)", step)
    if not match:
        raise ValueError(f"Invalid step id {step!r}. Use a value such as 3.1, 3.2b or 5.1.")
    return int(match.group(1)), int(match.group(2)), match.group(3)


def sections(lines: list[str]) -> list[tuple[str, int, int]]:
    """Return (step, first_body_line, end_marker_line) for every LAB STEP section."""
    found, current = [], None
    for index, line in enumerate(lines):
        start, end = START.match(line), END.match(line)
        if start:
            current = (start.group("step"), index + 1)
        elif end and current:
            if end.group("step") != current[0]:
                raise ValueError(f"Mismatched LAB STEP markers near line {index + 1}")
            found.append((current[0], current[1], index))
            current = None
    return found


def comment_block(block: list[str]) -> list[str]:
    """Comment lines the way VS Code's Ctrl+/ does: '# ' at the block's smallest indentation."""
    indents = [len(line) - len(line.lstrip()) for line in block if line.strip()]
    if not indents:
        return block
    width = min(indents)
    return [line if not line.strip() else line[:width] + "# " + line[width:] for line in block]


def is_commented(block: list[str]) -> bool:
    body = [line for line in block if line.strip()]
    return bool(body) and all(line.lstrip().startswith("#") for line in body)


def render(solution_text: str, enabled: set[str]) -> str:
    lines = solution_text.splitlines(keepends=False)
    for step, first, end in reversed(sections(lines)):
        if step not in enabled:
            lines[first:end] = comment_block(lines[first:end])
    return "\n".join(lines) + "\n"


def all_steps() -> list[str]:
    steps: set[str] = set()
    for name in LAB_FILES:
        text = (SOLUTION_DIR / name).read_text(encoding="utf-8")
        steps.update(step for step, _, _ in sections(text.splitlines()))
    return sorted(steps, key=step_key)


def current_enabled() -> set[str]:
    enabled: set[str] = set()
    for name in LAB_FILES:
        path = STUDENT_DIR / name
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for step, first, end in sections(lines):
            if not is_commented(lines[first:end]):
                enabled.add(step)
    return enabled


def expand(requested: list[str]) -> set[str]:
    available = all_steps()
    result: set[str] = set()
    for item in requested:
        matches = [s for s in available if s == item or (re.fullmatch(r"\d+\.\d+", item) and s.startswith(item))]
        if not matches:
            raise SystemExit(f"Unknown step {item!r}. Available: {', '.join(available)}")
        result.update(matches)
    return result


def write_state(enabled: set[str]) -> None:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    for name in LAB_FILES:
        target = STUDENT_DIR / name
        if target.exists():
            backup = BACKUP_DIR / stamp / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        target.write_text(render((SOLUTION_DIR / name).read_text(encoding="utf-8"), enabled), encoding="utf-8")
    print(f"Updated {', '.join(LAB_FILES)} in app/triage_desk (backup: .lab-backup/{stamp}/)")


def print_status() -> None:
    enabled = current_enabled()
    for step in all_steps():
        print(f"  LAB STEP {step:<5} {'enabled' if step in enabled else 'commented out'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("reset")
    sub.add_parser("solution")
    upto = sub.add_parser("upto")
    upto.add_argument("step")
    enable = sub.add_parser("enable")
    enable.add_argument("steps", nargs="+")
    args = parser.parse_args(argv)

    if args.command == "status":
        print_status()
        return 0
    if args.command == "reset":
        enabled: set[str] = set()
    elif args.command == "solution":
        enabled = set(all_steps())
    elif args.command == "upto":
        limit = step_key(args.step)
        enabled = {s for s in all_steps() if step_key(s)[:2] <= limit[:2] and (not limit[2] or step_key(s) <= limit)}
    else:
        enabled = current_enabled() | expand(args.steps)
    write_state(enabled)
    print_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())

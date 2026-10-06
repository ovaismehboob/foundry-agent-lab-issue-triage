"""Console rendering helpers (plain text, no extra dependencies)."""

from __future__ import annotations

import textwrap

from triage_desk.models import Issue, TriageResult

WIDTH = 100


def rule(char: str = "-") -> str:
    return char * WIDTH


def wrap(text: str, indent: str = "    ") -> str:
    return "\n".join(
        textwrap.fill(paragraph, width=WIDTH, initial_indent=indent, subsequent_indent=indent) if paragraph.strip() else ""
        for paragraph in text.splitlines()
    )


def render_issue(issue: Issue) -> str:
    return "\n".join(
        [
            rule("="),
            f"{issue.issue_id}  channel={issue.channel}  customer={issue.customer_id or '-'}  received={issue.received_at}",
            rule(),
            wrap(issue.text),
        ]
    )


def render_result(result: TriageResult) -> str:
    lines = [
        rule("="),
        f"TRIAGE RESULT  {result.issue_id}   engine: {result.engine}",
        rule(),
    ]
    if result.raw_text is not None and result.category == "(free text)":
        lines += ["Response (free text):", wrap(result.raw_text)]
    else:
        lines += [
            f"Category      : {result.category}",
            f"Priority      : {result.priority}",
            f"Routed team   : {result.team}  (first response within {result.first_response_sla_hours}h)",
            f"Rationale     : {result.rationale}",
            f"Signals       : {'; '.join(result.context_signals) if result.context_signals else '-'}",
            f"Safety flags  : {', '.join(result.safety_flags) if result.safety_flags else '-'}",
            f"Known issue   : {result.known_issue_id or '-'}",
            "Acknowledgment:",
            wrap(result.acknowledgment or "-"),
        ]
        if result.customer_notification:
            lines += ["Customer notification:", wrap(result.customer_notification)]
        if result.raw_text:
            lines += ["Full response (free text):", wrap(result.raw_text)]
    if result.sources:
        lines.append("Sources returned by Foundry IQ:")
        for source in result.sources:
            location = f" - {source['url']}" if source.get("url") else ""
            lines.append(f"    * {source.get('title') or source.get('reference_id')}{location}")
    for note in result.notes:
        lines.append(f"NOTE: {note}")
    return "\n".join(lines)


def render_queue(results: list[TriageResult], issues: dict[str, Issue]) -> str:
    order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    rows = sorted(results, key=lambda r: (order.get(r.priority, 9), r.issue_id))
    header = f"{'PRI':<4} {'ISSUE':<9} {'CATEGORY':<18} {'TEAM':<34} {'SLA':>4}  MESSAGE"
    lines = [header, rule()]
    for result in rows:
        message = issues[result.issue_id].text.replace("\n", " ")
        message = message if len(message) <= 26 else message[:23] + "..."
        lines.append(
            f"{result.priority:<4} {result.issue_id:<9} {result.category:<18} {result.team[:34]:<34} "
            f"{str(result.first_response_sla_hours) + 'h':>4}  {message}"
        )
    return "\n".join(lines)


def render_comparison(baseline: TriageResult, other: TriageResult) -> str:
    def row(label: str, left: str, right: str) -> str:
        marker = "  " if left == right else "<>"
        return f"{label:<10} {left[:38]:<38} {marker} {right[:38]}"

    return "\n".join(
        [
            rule("="),
            f"COMPARISON  {baseline.issue_id}",
            f"{'':<10} {baseline.engine[:38]:<38}    {other.engine[:38]}",
            rule(),
            row("Category", baseline.category, other.category),
            row("Priority", baseline.priority, other.priority),
            row("Team", baseline.team, other.team),
        ]
    )

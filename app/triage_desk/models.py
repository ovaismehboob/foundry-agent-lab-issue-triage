"""Data models shared by the rules engine, the agent, and the CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from pydantic import BaseModel, Field

CategoryId = Literal[
    "NETWORK",
    "DEVICE_SIM",
    "BILLING",
    "ROAMING",
    "ACCOUNT_PLAN",
    "SERVICE_COMPLAINT",
    "UNCLASSIFIED",
]
PriorityId = Literal["P1", "P2", "P3", "P4"]

CATEGORY_IDS: tuple[str, ...] = CategoryId.__args__  # type: ignore[attr-defined]
PRIORITY_IDS: tuple[str, ...] = PriorityId.__args__  # type: ignore[attr-defined]


@dataclass(frozen=True)
class Issue:
    issue_id: str
    channel: str
    customer_id: Optional[str]
    received_at: str
    text: str


@dataclass(frozen=True)
class Customer:
    customer_id: str
    preferred_name: str
    segment: str
    plan: str
    home_area: str
    lines: int
    open_tickets: int
    complaints_last_90_days: int
    account_status: str


@dataclass(frozen=True)
class Route:
    team: str
    first_response_sla_hours: int


@dataclass
class TriageResult:
    """What the CLI displays, regardless of which engine produced it."""

    issue_id: str
    engine: str
    category: str
    priority: str
    team: str
    first_response_sla_hours: int
    rationale: str
    context_signals: list[str] = field(default_factory=list)
    acknowledgment: str = ""
    known_issue_id: Optional[str] = None
    customer_notification: Optional[str] = None
    safety_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    raw_text: Optional[str] = None


class TriageDecision(BaseModel):
    """Structured output the code-defined agent must return (Exercise 3.2 onwards)."""

    issue_id: Optional[str] = Field(description="The issue ID, for example ISS-1001, or null if none was given.")
    category: CategoryId = Field(description="One category ID from the triage instructions.")
    priority: PriorityId = Field(description="P1 (critical) to P4 (low), using the priority definitions.")
    priority_rationale: str = Field(description="One or two sentences explaining the priority.")
    context_signals: list[str] = Field(
        description="Short phrases from the message or customer context that drove the decision."
    )
    routed_team: str = Field(description="Team returned by the route_issue tool, or 'Unassigned' if the tool is unavailable.")
    first_response_sla_hours: int = Field(description="SLA hours returned by route_issue, or 0 if the tool is unavailable.")
    acknowledgment: str = Field(description="Customer acknowledgment message with relevant first steps.")
    known_issue_id: Optional[str] = Field(
        description="Known incident ID (for example KI-2041) found in the knowledge base context, otherwise null."
    )
    customer_notification: Optional[str] = Field(
        description="Notification linking the issue to a known incident or documented solution, otherwise null."
    )
    safety_flags: list[str] = Field(
        description="Zero or more of: possible_prompt_injection, abusive_language, out_of_scope, needs_more_information."
    )

"""Deterministic (non-AI) triage: keyword classification, rule-based priority, policy routing,
and template acknowledgments. This is the Module 2 baseline that the agent is compared with.
"""

from __future__ import annotations

from triage_desk.data_store import DataStore
from triage_desk.models import CATEGORY_IDS, PRIORITY_IDS, Customer, Issue, Route, TriageResult

URGENT_PHRASES = (
    "no mobile data", "no data", "no network", "no service", "no signal", "none of them",
    "cannot make", "can't make", "nobody has", "cut my line", "suspended", "not working",
    "outage", "urgent", "stopping our business",
)
DEGRADED_PHRASES = ("slow", "buffering", "dropping", "intermittent", "sometimes")
INFO_PHRASES = (
    "how do i", "how can i", "can you send", "please transfer", "recommend", "change from",
    "would like to know", "question",
)

FIRST_STEPS = {
    "NETWORK": "please restart your device, check that mobile data is switched on, and check our service status page for your area.",
    "DEVICE_SIM": "please restart your device and make sure it has the latest software update. Do not reuse an eSIM QR code.",
    "BILLING": "please keep your payment receipt or transaction reference ready. You do not need to pay a disputed amount while we review it.",
    "ROAMING": "please check that data roaming is switched on in your phone settings and try selecting a partner network manually.",
    "ACCOUNT_PLAN": "you can review available plans in the Contoso Telecom app under Plans.",
    "SERVICE_COMPLAINT": "we are sorry for your experience. A member of our Customer Relations team will contact you personally.",
    "UNCLASSIFIED": "please reply with more details about the service, device, or bill you need help with.",
}


def _priority_rank(priority: str) -> int:
    return PRIORITY_IDS.index(priority)


def classify(text: str, taxonomy: dict) -> tuple[str, list[str]]:
    """Return the category with the most keyword matches, and the matched keywords."""
    lowered = text.lower()
    best_category, best_matches = "UNCLASSIFIED", []
    for category in taxonomy["categories"]:
        matches = [kw for kw in category["keywords"] if kw in lowered]
        if len(matches) > len(best_matches):
            best_category, best_matches = category["id"], matches
    return best_category, best_matches


def prioritize(text: str, customer: Customer | None) -> tuple[str, list[str]]:
    lowered = text.lower()
    signals: list[str] = []
    urgent = [p for p in URGENT_PHRASES if p in lowered]
    degraded = [p for p in DEGRADED_PHRASES if p in lowered]
    info = [p for p in INFO_PHRASES if p in lowered]

    if urgent:
        priority = "P2"
        signals.append(f"urgent phrase: {urgent[0]!r}")
        if customer and customer.segment == "business":
            priority = "P1"
            signals.append("business customer with loss of service")
    elif degraded:
        priority = "P3"
        signals.append(f"degradation phrase: {degraded[0]!r}")
    elif info:
        priority = "P4"
        signals.append(f"information request phrase: {info[0]!r}")
    else:
        priority = "P3"
        signals.append("no priority keywords found (default P3)")

    if customer and customer.complaints_last_90_days >= 2 and _priority_rank(priority) > 1:
        priority = PRIORITY_IDS[_priority_rank(priority) - 1]
        signals.append("repeat complaints in last 90 days (raised one level)")
    return priority, signals


def route(category: str, priority: str, routing_rules: dict) -> Route:
    """Policy routing. Raises ValueError for unknown categories or priorities."""
    if category not in CATEGORY_IDS:
        raise ValueError(f"Unknown category {category!r}. Valid values: {', '.join(CATEGORY_IDS)}")
    if priority not in PRIORITY_IDS:
        raise ValueError(f"Unknown priority {priority!r}. Valid values: {', '.join(PRIORITY_IDS)}")
    team = routing_rules["teams_by_category"][category]
    for override in routing_rules.get("overrides", []):
        if override["category"] == category and override["priority"] == priority:
            team = override["team"]
    return Route(team=team, first_response_sla_hours=int(routing_rules["first_response_sla_hours"][priority]))


def category_name(category: str, taxonomy: dict) -> str:
    return next((c["name"] for c in taxonomy["categories"] if c["id"] == category), category)


def acknowledgment(issue: Issue, customer: Customer | None, category: str, priority: str, route_: Route, taxonomy: dict) -> str:
    name = customer.preferred_name if customer else "there"
    return (
        f"Hello {name}, thank you for contacting Contoso Telecom. We have logged your request as "
        f"{issue.issue_id} ({category_name(category, taxonomy)}, priority {priority}). It has been assigned "
        f"to our {route_.team} team, who will respond within {route_.first_response_sla_hours} hours. "
        f"In the meantime, {FIRST_STEPS[category]}"
    )


def triage_with_rules(issue: Issue, store: DataStore) -> TriageResult:
    taxonomy, routing_rules = store.taxonomy, store.routing_rules
    customer = store.get_customer(issue.customer_id)
    category, keywords = classify(issue.text, taxonomy)
    priority, priority_signals = prioritize(issue.text, customer)
    route_ = route(category, priority, routing_rules)
    signals = [f"keyword: {kw!r}" for kw in keywords] + priority_signals
    notes = [] if customer or not issue.customer_id else [f"customer {issue.customer_id} not found"]
    return TriageResult(
        issue_id=issue.issue_id,
        engine="rules",
        category=category,
        priority=priority,
        team=route_.team,
        first_response_sla_hours=route_.first_response_sla_hours,
        rationale="Keyword and rule based decision (no AI).",
        context_signals=signals,
        acknowledgment=acknowledgment(issue, customer, category, priority, route_, taxonomy),
        notes=notes,
    )

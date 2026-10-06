"""Existing application functions exposed to the agent as tools (Exercise 3.3).

The tools are read-only: they look up synthetic data and apply the routing policy.
They never change a ticket, send a message, or call an external system.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from pydantic import Field

from triage_desk import rules
from triage_desk.config import load_settings
from triage_desk.data_store import DataStore, get_store
from triage_desk.models import CATEGORY_IDS, PRIORITY_IDS

logger = logging.getLogger("triage_desk.tools")


def _store() -> DataStore:
    return get_store(str(load_settings().data_dir))


def get_issue(
    issue_id: Annotated[str, Field(description="Issue ID such as ISS-1001.")],
) -> str:
    """Get the text, channel, and customer ID of an incoming issue."""
    issue = _store().get_issue(issue_id)
    if issue is None:
        return json.dumps({"error": f"Issue {issue_id!r} was not found."})
    return json.dumps(issue.__dict__, ensure_ascii=False)


def get_customer_context(
    customer_id: Annotated[str, Field(description="Customer ID such as CUST-1001.")],
) -> str:
    """Get the customer's segment, plan, home area, number of lines, open tickets, and recent complaints."""
    customer = _store().get_customer(customer_id)
    if customer is None:
        return json.dumps({"error": f"Customer {customer_id!r} was not found. Continue without customer context."})
    data = dict(customer.__dict__)
    data.pop("preferred_name", None)  # The agent doesn't need the name to triage.
    return json.dumps(data)


def route_issue(
    category: Annotated[str, Field(description=f"Category ID. One of: {', '.join(CATEGORY_IDS)}.")],
    priority: Annotated[str, Field(description=f"Priority. One of: {', '.join(PRIORITY_IDS)}.")],
) -> str:
    """Return the team and first-response SLA (hours) defined by the routing policy for a category and priority."""
    try:
        route = rules.route(category.strip().upper(), priority.strip().upper(), _store().routing_rules)
    except ValueError as error:
        return json.dumps({"error": str(error)})
    return json.dumps({"team": route.team, "first_response_sla_hours": route.first_response_sla_hours})


TOOL_FUNCTIONS = (get_issue, get_customer_context, route_issue)


def agent_tools() -> list[Any]:
    """Wrap the plain functions as Agent Framework tools."""
    from agent_framework import tool

    return [tool(func, approval_mode="never_require") for func in TOOL_FUNCTIONS]


def tool_logging_middleware() -> Any:
    """Function middleware that prints every tool call, its arguments, and its result."""
    from agent_framework import FunctionInvocationContext, function_middleware

    @function_middleware
    async def log_tool_calls(context: FunctionInvocationContext, call_next) -> None:
        arguments = context.arguments
        if hasattr(arguments, "model_dump"):
            arguments = arguments.model_dump()
        print(f"  [tool call]   {context.function.name}({_format_args(arguments)})", flush=True)
        logger.info("tool_call name=%s arguments=%s", context.function.name, arguments)
        await call_next()
        preview = _result_text(context.result)
        print(f"  [tool result] {preview[:200]}", flush=True)
        logger.info("tool_result name=%s result=%s", context.function.name, preview[:500])

    return log_tool_calls


def _result_text(result: Any) -> str:
    """Tool results arrive as a list of Content items (or a plain value); show their text."""
    items = result if isinstance(result, (list, tuple)) else [result]
    parts = []
    for item in items:
        text = getattr(item, "text", None)
        if text is None and hasattr(item, "result"):
            text = item.result
        parts.append(str(text if text is not None else item))
    return " ".join(parts)


def _format_args(arguments: Any) -> str:
    if isinstance(arguments, dict):
        return ", ".join(f"{key}={value!r}" for key, value in arguments.items())
    return repr(arguments)

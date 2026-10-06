"""Hosted agent entry point (Modules 6 and 7).

Serves the same code-defined triage agent over the Foundry Responses protocol on port 8088,
using the Agent Framework hosting adapter. The agent configuration comes from
triage_desk/agent_factory.py, so complete Module 3 (and optionally Module 5) first.

Run locally:      python main.py            (then call http://localhost:8088/responses)
Run in Docker:    see docs/student/module-06-containerize.md
Run in Foundry:   see docs/student/module-07-hosted-agent.md
"""

from __future__ import annotations

import asyncio
import logging
import sys

from triage_desk.agent_factory import build_triage_agent
from triage_desk.config import load_settings
from triage_desk.credentials import get_credential


async def main() -> None:
    settings = load_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), stream=sys.stdout)
    missing = settings.missing_for_ai()
    if missing:
        raise SystemExit(f"Missing configuration: {', '.join(missing)}")

    from agent_framework_foundry_hosting import ResponsesHostServer

    agent = build_triage_agent(settings, get_credential(), hosting=True)
    print(
        f"Starting issue-triage-agent (knowledge base: {'on' if settings.knowledge_configured else 'off'}) on port 8088",
        flush=True,
    )
    server = ResponsesHostServer(agent)
    await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())

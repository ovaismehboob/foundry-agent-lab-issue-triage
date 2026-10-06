"""Command-line interface for the Issue Triage Assistant.

Examples (run from the app folder):
    python -m triage_desk queue
    python -m triage_desk show ISS-1009
    python -m triage_desk triage ISS-1009
    python -m triage_desk triage ISS-1009 --engine agent --compare
    python -m triage_desk triage --text "No signal since this morning" --customer CUST-1001 --engine agent
    python -m triage_desk chat --engine agent
    python -m triage_desk doctor
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

from triage_desk import display, rules
from triage_desk.config import Settings, load_settings
from triage_desk.data_store import DataStore
from triage_desk.models import Issue, TriageResult

ENGINES = ("rules", "prompt-agent", "agent")


def _configure_output(verbose: bool, settings: Settings) -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    level = logging.INFO if verbose else getattr(logging, settings.log_level.upper(), logging.WARNING)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not verbose:
        for noisy in ("azure", "httpx", "httpcore", "openai", "agent_framework"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def _require_ai_settings(settings: Settings, engine: str) -> None:
    missing = settings.missing_for_ai() if engine == "agent" else []
    if engine == "prompt-agent":
        if not settings.project_endpoint:
            missing.append("FOUNDRY_PROJECT_ENDPOINT")
        if not settings.prompt_agent_name:
            missing.append("PROMPT_AGENT_NAME")
        if not settings.prompt_agent_version:
            missing.append("PROMPT_AGENT_VERSION")
    if missing:
        raise SystemExit(
            f"Missing configuration for engine '{engine}': {', '.join(missing)}.\n"
            "Copy app/.env.example to app/.env and fill in the values from the Foundry portal."
        )


def build_engine_agent(engine: str, settings: Settings) -> Any:
    from triage_desk import agent_factory
    from triage_desk.credentials import get_credential

    _require_ai_settings(settings, engine)
    credential = get_credential()
    if engine == "prompt-agent":
        return agent_factory.build_prompt_agent(settings, credential)
    return agent_factory.build_triage_agent(settings, credential)


async def triage_issue(issue: Issue, engine: str, settings: Settings, store: DataStore, agent: Any = None) -> TriageResult:
    if engine == "rules":
        return rules.triage_with_rules(issue, store)

    from triage_desk import agent_factory
    from triage_desk.ai_triage import run_triage

    agent = agent or build_engine_agent(engine, settings)
    return await run_triage(
        agent,
        issue,
        store=store,
        engine=engine,
        options=agent_factory.triage_run_options() if engine == "agent" else {},
        max_issue_chars=settings.max_issue_chars,
        timeout_seconds=settings.request_timeout_seconds,
        include_customer_context=(engine == "prompt-agent"),
    )


def _issue_from_args(args: argparse.Namespace, store: DataStore) -> Issue:
    if args.text:
        return Issue(
            issue_id="ISS-ADHOC",
            channel="cli",
            customer_id=args.customer.upper() if args.customer else None,
            received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            text=args.text,
        )
    if not args.issue_id:
        raise SystemExit("Provide an issue ID (for example ISS-1001) or --text \"...\".")
    issue = store.get_issue(args.issue_id)
    if issue is None:
        raise SystemExit(f"Issue {args.issue_id} not found. Run 'python -m triage_desk queue' to list issues.")
    return issue


async def cmd_triage(args: argparse.Namespace, settings: Settings, store: DataStore) -> int:
    issue = _issue_from_args(args, store)
    agent = build_engine_agent(args.engine, settings) if args.engine != "rules" else None
    try:
        print(display.render_issue(issue), flush=True)
        result = await triage_issue(issue, args.engine, settings, store, agent=agent)
        print(display.render_result(result))
        if args.compare and args.engine != "rules":
            print(display.render_comparison(rules.triage_with_rules(issue, store), result))
    finally:
        await _close(agent)
    return 0


async def _close(agent: Any) -> None:
    if agent is not None:
        from triage_desk.knowledge import close_providers

        await close_providers(agent)


async def cmd_queue(args: argparse.Namespace, settings: Settings, store: DataStore) -> int:
    issues = store.issues()
    agent = build_engine_agent(args.engine, settings) if args.engine != "rules" else None
    results = []
    try:
        for issue in issues:
            if args.engine != "rules":
                print(f"Triaging {issue.issue_id} with {args.engine}...", flush=True)
            results.append(await triage_issue(issue, args.engine, settings, store, agent=agent))
    finally:
        await _close(agent)
    print(display.render_queue(results, {issue.issue_id: issue for issue in issues}))
    return 0


async def cmd_chat(args: argparse.Namespace, settings: Settings, store: DataStore) -> int:
    agent = build_engine_agent(args.engine, settings)
    try:
        return await _chat_loop(agent, args)
    finally:
        await _close(agent)


async def _chat_loop(agent: Any, args: argparse.Namespace) -> int:
    from triage_desk.agent_factory import new_conversation
    from triage_desk.knowledge import references_from

    session = new_conversation(agent)
    print(display.rule("="))
    print(f"Chat with the {args.engine} engine. Commands: /new (forget the conversation), /exit")
    print("Conversation memory: " + ("ON (session created)" if session is not None else "OFF (LAB STEP 3.4 not enabled)"))
    print(display.rule("="))
    while True:
        try:
            message = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not message:
            continue
        if message.lower() in ("/exit", "/quit"):
            return 0
        if message.lower() == "/new":
            session = new_conversation(agent)
            print("Started a new conversation.")
            continue
        response = await (agent.run(message, session=session) if session is not None else agent.run(message))
        print(f"\nagent> {response.text}")
        for source in references_from(agent):
            print(f"   source: {source.get('title') or source.get('reference_id')}")


async def cmd_doctor(args: argparse.Namespace, settings: Settings, store: DataStore) -> int:
    def status(ok: bool) -> str:
        return "OK " if ok else "-- "

    print(display.rule("="))
    print("Configuration check (values are not printed)")
    print(display.rule())
    print(f"{status(True)} data folder: {settings.data_dir} ({len(store.issues())} issues, {len(store.customers())} customers)")
    print(f"{status(bool(settings.project_endpoint))} FOUNDRY_PROJECT_ENDPOINT")
    print(f"{status(bool(settings.model_deployment_name))} MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME")
    print(f"{status(bool(settings.prompt_agent_name))} PROMPT_AGENT_NAME")
    print(f"{status(bool(settings.prompt_agent_version))} PROMPT_AGENT_VERSION")
    print(f"{status(bool(settings.search_endpoint))} AZURE_SEARCH_ENDPOINT (Module 5)")
    print(f"{status(bool(settings.knowledge_base_name))} AZURE_SEARCH_KNOWLEDGE_BASE_NAME (Module 5)")
    try:
        import agent_framework  # noqa: F401

        print(f"{status(True)} agent-framework packages installed")
    except ImportError:
        print(f"{status(False)} agent-framework packages not installed (pip install -r requirements.txt)")
    if args.check_sign_in:
        from triage_desk.credentials import FOUNDRY_SCOPE, get_credential

        try:
            get_credential().get_token(FOUNDRY_SCOPE)
            print(f"{status(True)} signed in to Azure (token acquired for Microsoft Foundry)")
        except Exception as error:  # Report any sign-in problem without a stack trace.
            print(f"{status(False)} could not get a Microsoft Foundry token: {type(error).__name__}. Run 'az login'.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triage_desk", description="Contoso Telecom Issue Triage Assistant (lab app)")
    parser.add_argument("--verbose", action="store_true", help="show application logs")
    sub = parser.add_subparsers(dest="command", required=True)

    queue = sub.add_parser("queue", help="triage every incoming issue and show a prioritized queue")
    queue.add_argument("--engine", choices=ENGINES, default="rules")

    show = sub.add_parser("show", help="show one incoming issue")
    show.add_argument("issue_id")

    triage = sub.add_parser("triage", help="triage one issue")
    triage.add_argument("issue_id", nargs="?")
    triage.add_argument("--text", help="triage free text instead of a stored issue")
    triage.add_argument("--customer", help="customer ID for --text, for example CUST-1001")
    triage.add_argument("--engine", choices=ENGINES, default="rules")
    triage.add_argument("--compare", action="store_true", help="also show the rules result side by side")

    chat = sub.add_parser("chat", help="multi-turn chat with the agent")
    chat.add_argument("--engine", choices=("agent", "prompt-agent"), default="agent")

    doctor = sub.add_parser("doctor", help="check configuration")
    doctor.add_argument("--check-sign-in", action="store_true", help="also try to get an Azure token")
    return parser


async def _dispatch(args: argparse.Namespace, settings: Settings, store: DataStore) -> int:
    if args.command == "show":
        issue = store.get_issue(args.issue_id)
        if issue is None:
            raise SystemExit(f"Issue {args.issue_id} not found.")
        print(display.render_issue(issue))
        return 0
    handlers = {"queue": cmd_queue, "triage": cmd_triage, "chat": cmd_chat, "doctor": cmd_doctor}
    return await handlers[args.command](args, settings, store)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    _configure_output(args.verbose, settings)
    store = DataStore(settings.data_dir)
    try:
        return asyncio.run(_dispatch(args, settings, store))
    except SystemExit:
        raise
    except Exception as error:  # Show a short, student-friendly error. Use --verbose for the stack trace.
        from triage_desk.agent_factory import LabStepNotEnabled

        if isinstance(error, LabStepNotEnabled):
            print(f"\n{error}\nSee the student guide for this exercise.", file=sys.stderr)
            return 2
        print(f"\nERROR: {type(error).__name__}: {error}", file=sys.stderr)
        print("Tip: run with --verbose for details, and see docs/troubleshooting.md.", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1

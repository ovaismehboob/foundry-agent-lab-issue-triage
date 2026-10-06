"""Agent construction for the Issue Triage Assistant.

This is the main file you change during the lab. Each prepared section is marked:

    # ===== LAB STEP x.y: UNCOMMENT THIS SECTION (...) =====
    # ...code...
    # ===== END LAB STEP x.y =====

To enable a step, select the commented code lines between the markers (not the marker lines)
and press Ctrl+/ (Cmd+/ on macOS) in VS Code. Save the file and run the command in the guide.
"""

from __future__ import annotations

from typing import Any

from triage_desk.config import PROMPTS_DIR, Settings
from triage_desk.knowledge import build_knowledge_provider
from triage_desk.models import TriageDecision
from triage_desk.tools import agent_tools, tool_logging_middleware

AGENT_NAME = "issue-triage-agent"
GENERIC_INSTRUCTIONS = "You are a helpful assistant."


class LabStepNotEnabled(RuntimeError):
    def __init__(self, step: str, hint: str) -> None:
        super().__init__(f"LAB STEP {step} is not enabled yet. {hint}")
        self.step = step


def load_instructions(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------------------------
# Exercise 3.1 - Connect to the Prompt Agent you created in the Foundry portal (Module 1)
# ---------------------------------------------------------------------------------------------
def build_prompt_agent(settings: Settings, credential: Any) -> Any:
    from agent_framework.foundry import FoundryAgent

    # ===== LAB STEP 3.1a: UNCOMMENT THIS SECTION (connect to the portal Prompt Agent) =====
    # return FoundryAgent(
    #     project_endpoint=settings.project_endpoint,
    #     agent_name=settings.prompt_agent_name,
    #     agent_version=settings.prompt_agent_version,
    #     credential=credential,
    # )
    # ===== END LAB STEP 3.1a =====

    raise LabStepNotEnabled("3.1a", "Uncomment the FoundryAgent section in build_prompt_agent().")


# ---------------------------------------------------------------------------------------------
# Exercises 3.1 to 3.3 and 5.1 - Build the code-defined triage agent
# ---------------------------------------------------------------------------------------------
def build_triage_agent(settings: Settings, credential: Any, *, hosting: bool = False) -> Any:
    from agent_framework import Agent
    from agent_framework.foundry import FoundryChatClient

    client = None
    instructions = GENERIC_INSTRUCTIONS
    tools: list[Any] = []
    middleware: list[Any] = []
    context_providers: list[Any] = []

    # ===== LAB STEP 3.1b: UNCOMMENT THIS SECTION (connect to your model deployment) =====
    # client = FoundryChatClient(
    #     project_endpoint=settings.project_endpoint,
    #     model=settings.model_deployment_name,
    #     credential=credential,
    # )
    # ===== END LAB STEP 3.1b =====

    # ===== LAB STEP 3.2a: UNCOMMENT THIS SECTION (give the agent its triage instructions) =====
    # instructions = load_instructions("triage_instructions.md")
    # ===== END LAB STEP 3.2a =====

    # ===== LAB STEP 3.3: UNCOMMENT THIS SECTION (expose app functions as tools and log every tool call) =====
    # tools = agent_tools()
    # middleware = [tool_logging_middleware()]
    # ===== END LAB STEP 3.3 =====

    # ===== LAB STEP 5.1: UNCOMMENT THIS SECTION (ground the agent with the Foundry IQ knowledge base) =====
    # if settings.knowledge_configured:
    #     context_providers = [build_knowledge_provider(settings, credential)]
    #     instructions = instructions + "\n\n" + load_instructions("knowledge_instructions.md")
    # ===== END LAB STEP 5.1 =====

    if client is None:
        raise LabStepNotEnabled("3.1b", "Uncomment the FoundryChatClient section in build_triage_agent().")

    return Agent(
        client=client,
        name=AGENT_NAME,
        instructions=instructions,
        tools=tools,
        middleware=middleware,
        context_providers=context_providers,
        # Hosted agents keep conversation history in the hosting platform (see the official samples).
        default_options={"store": False} if hosting else None,
    )


# ---------------------------------------------------------------------------------------------
# Exercise 3.2 - Ask for structured output
# ---------------------------------------------------------------------------------------------
def triage_run_options() -> dict[str, Any]:
    options: dict[str, Any] = {}

    # ===== LAB STEP 3.2b: UNCOMMENT THIS SECTION (require a structured triage decision) =====
    # options["response_format"] = TriageDecision
    # ===== END LAB STEP 3.2b =====

    return options


# ---------------------------------------------------------------------------------------------
# Exercise 3.4 - Keep conversation context across turns
# ---------------------------------------------------------------------------------------------
def new_conversation(agent: Any) -> Any:
    session = None

    # ===== LAB STEP 3.4: UNCOMMENT THIS SECTION (remember earlier turns in the chat) =====
    # session = agent.create_session()
    # ===== END LAB STEP 3.4 =====

    return session

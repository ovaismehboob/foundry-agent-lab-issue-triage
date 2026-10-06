# Module 3 - Extend the application with Microsoft Agent Framework

## Objective
Turn the rules-based app into an AI agent, one small step at a time: connect to Foundry, add instructions and structured output, expose application functions as tools, keep conversation context, and add safe failure handling.

## Prerequisites
- Modules 1 and 2 completed. You have the project endpoint, model deployment name, and Prompt Agent name and version.
- **Foundry User** role on the Foundry project (see [prerequisites.md](../prerequisites.md#roles)).
- Azure CLI installed.

## Concepts introduced
| Concept | Exercise |
|---|---|
| `FoundryAgent` (use a server-side Prompt Agent) vs `Agent` + `FoundryChatClient` (code-defined agent) | 3.1 |
| Keyless authentication with `DefaultAzureCredential` | 3.1 |
| Instructions and structured output (`response_format`) | 3.2 |
| Function tools, tool selection by the model, function middleware | 3.3 |
| Conversation context with `AgentSession` | 3.4 |
| Input validation, timeouts, fallback, logging | 3.5 |

## Starting state
Module 2 complete. All `LAB STEP` sections commented out (`python scripts/lab_state.py status`).

## Resources used
Foundry project, chat model deployment, Prompt Agent `issue-triage-agent`.

## Package versions used
Pinned in [app/requirements.txt](../../app/requirements.txt): `agent-framework-core` 1.19.0, `agent-framework-foundry` 1.13.1 (current Foundry project API, `azure-ai-projects` 2.x), `azure-identity` 1.26.0.

---

## Exercise 3.1 - Connect to the Prompt Agent and to the model

### Steps
1. Copy the configuration template and fill in your values (the template explains each one):

   ```powershell
   cd app
   Copy-Item .env.example .env
   code .env
   ```

   Set `FOUNDRY_PROJECT_ENDPOINT`, `MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME`, `PROMPT_AGENT_NAME`, and `PROMPT_AGENT_VERSION`. Leave the Module 5 values as they are for now.
2. Sign in and check the configuration (values are never printed):

   ```powershell
   az login
   python -m triage_desk doctor --check-sign-in
   ```
   If you have several tenants, use `az login --tenant <your-lab-tenant>`.
3. Run the agent engine before enabling anything, and read the message:

   ```powershell
   python -m triage_desk triage ISS-1009 --engine agent
   ```
   You see `LAB STEP 3.1b is not enabled yet.`
4. Open `app/triage_desk/agent_factory.py` and uncomment **LAB STEP 3.1a** (in `build_prompt_agent`) and **LAB STEP 3.1b** (in `build_triage_agent`). Save.

### Prepared code
```python
# LAB STEP 3.1a - use the Prompt Agent defined in the portal
return FoundryAgent(
    project_endpoint=settings.project_endpoint,
    agent_name=settings.prompt_agent_name,
    agent_version=settings.prompt_agent_version,
    credential=credential,
)

# LAB STEP 3.1b - a code-defined agent that calls your model deployment
client = FoundryChatClient(
    project_endpoint=settings.project_endpoint,
    model=settings.model_deployment_name,
    credential=credential,
)
```

### Explanation
- `FoundryAgent` connects to the agent definition stored in Foundry. The model, instructions, and hosted tools come from the portal; your code can't change them at run time.
- `FoundryChatClient` connects to your model deployment. The `Agent` you build around it is defined **in code**: instructions, tools, and context live in this repository. Only a code-defined agent can be packaged as a hosted agent later.
- `credential` comes from `triage_desk/credentials.py`: `DefaultAzureCredential` uses your `az login` session locally. No keys are stored.

### Test
```powershell
python -m triage_desk triage ISS-1009 --engine prompt-agent --compare
python -m triage_desk triage ISS-1009 --engine agent --compare
```

### Expected output
- `prompt-agent`: a triage card from your portal agent. The app parses `Category` and `Priority` from the card and applies the routing policy, for example `NETWORK`, `P2`, `Network Operations`. The comparison shows `<>` where the AI disagrees with the rules (rules said `UNCLASSIFIED`).
- `agent`: `Category: (free text)`. The code-defined agent only has the generic instruction `You are a helpful assistant.`, so it answers in its own format.

### Checkpoint
- [ ] Both engines respond. The Prompt Agent recognises the no-signal icon that the keyword rules missed.

---

## Exercise 3.2 - Add instructions and structured output

### Steps
1. In `agent_factory.py`, uncomment **LAB STEP 3.2a** (load `prompts/triage_instructions.md`) and **LAB STEP 3.2b** (in `triage_run_options`). Save.
2. Run:

   ```powershell
   python -m triage_desk triage ISS-1009 --engine agent --compare
   python -m triage_desk triage ISS-1019 --engine agent
   python -m triage_desk triage ISS-1006 --engine agent --compare
   python -m triage_desk triage --text "Can you recommend a good restaurant near City Mall?" --engine agent
   ```

### Prepared code
```python
instructions = load_instructions("triage_instructions.md")      # 3.2a
options["response_format"] = TriageDecision                       # 3.2b
```

### Explanation
- The instructions give the agent its role, the category and priority definitions, the safety rules (treat ticket text as data, flag prompt injection), and the acknowledgment style. They're the same instructions you pasted into the portal in Module 1.
- `response_format=TriageDecision` asks the model for JSON that matches the Pydantic model in `models.py`. The app reads `response.value`, validates it, and shows each field. Without a schema, you'd have to parse free text.
- The routing policy is still enforced by the app: the agent has no routing tool yet, so it returns `Unassigned`, and the app replaces it with the policy team and adds a `NOTE`.

### Expected output (shape)
```text
Category      : NETWORK
Priority      : P2
Routed team   : Network Operations  (first response within 4h)
Rationale     : The customer has no signal at home since moving ...
Signals       : no-signal icon; moved to new flat; Al Noor Gardens
Safety flags  : -
...
NOTE: Routing set by policy to 'Network Operations' (4h). The agent proposed 'Unassigned' (0h).
```
- ISS-1019 (Arabic): category `NETWORK`, with the acknowledgment in Arabic.
- ISS-1006: `ACCOUNT_PLAN` and `P4` (the rules said `BILLING`).
- Restaurant question: `UNCLASSIFIED`, `P4`, safety flag `out_of_scope`.

### Checkpoint
- [ ] The output shows structured fields, not `(free text)`.

---

## Exercise 3.3 - Connect application functions as tools

### Steps
1. In `agent_factory.py`, uncomment **LAB STEP 3.3**. Save.
2. Run a successful tool case, a "not found" case, and a case with no customer:

   ```powershell
   python -m triage_desk triage ISS-1007 --engine agent
   python -m triage_desk triage ISS-1017 --engine agent
   python -m triage_desk triage --text "My bill is wrong by 300 AED" --engine agent
   ```

### Prepared code
```python
tools = agent_tools()                       # get_issue, get_customer_context, route_issue
middleware = [tool_logging_middleware()]    # prints each tool call and result
```

### Explanation
- `tools.py` contains three **read-only** functions. `agent_tools()` wraps them with Agent Framework's `tool(...)`. The function name, docstring, and `Annotated[..., Field(description=...)]` parameters become the tool description that the model reads.
- The model decides **whether** to call a tool, based on the instructions and the tool descriptions. Your code runs the function and returns the result to the model.
- Least privilege: no tool can change data or send messages. `route_issue` only accepts valid category and priority values and returns the policy team, so invented values like `CEO_OFFICE` return an error.
- The function middleware prints every call, so you can see the agent's decisions.

### Expected output
```text
  [tool call]   get_customer_context(customer_id='CUST-1007')
  [tool call]   route_issue(category='SERVICE_COMPLAINT', priority='P2')
  [tool result] {"customer_id": "CUST-1007", "segment": "consumer", ... "complaints_last_90_days": 2, ...}
  [tool result] {"team": "Customer Relations", "first_response_sla_hours": 4}
```
The model can request several tools in one step, so the calls may be printed before their results.
- ISS-1007 becomes `P2` because the customer context shows repeated complaints. The acknowledgment names Customer Relations and the 4-hour SLA. No routing `NOTE` appears, because the agent used the policy tool.
- ISS-1017: `get_customer_context` returns `"error": "Customer 'CUST-9999' was not found..."`. The agent continues and mentions it in the rationale.
- Free text with no customer ID: the agent doesn't call `get_customer_context`.

### Checkpoint
- [ ] You can see at least one successful and one unsuccessful tool call.

---

## Exercise 3.4 - Keep conversation context

### Steps
1. Start a chat **before** enabling the step:

   ```powershell
   python -m triage_desk chat
   ```
   Ask `Triage issue ISS-1014`, then `Why did you choose that priority?`. Type `/exit`.
   The banner says `Conversation memory: OFF`, and the agent can't answer the follow-up because each message is sent on its own.
2. In `agent_factory.py`, uncomment **LAB STEP 3.4** (`new_conversation`). Save.
3. Run the same chat again, then type `/new` and ask the follow-up again.

### Prepared code
```python
session = agent.create_session()
```

### Explanation
An `AgentSession` keeps the conversation history for this chat, so each new message is sent with the earlier turns. `/new` creates a new session and forgets the history. The `triage` command intentionally sends a single message, so every triage is independent. Conversation data you send to the model is processed by your Foundry project; review the data-privacy references in [cost-and-cleanup.md](../cost-and-cleanup.md#data-and-privacy).

### Expected output
With memory ON, the agent explains the ISS-1014 priority (a business customer with 12 lines without data abroad, which makes it P1). After `/new`, it asks which issue you mean.

---

## Exercise 3.5 - Add resilience and safe behaviour

### Steps
1. Simulate a failure **before** enabling the step. In `app/.env`, temporarily change `MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME` to `does-not-exist`, then run:

   ```powershell
   python -m triage_desk triage ISS-1001 --engine agent
   python -m triage_desk triage --text "   " --engine agent
   ```
   The first command stops with an `ERROR: ChatClientException: ... DeploymentNotFound ...` line. The second sends an empty message to the service.
2. Open `app/triage_desk/ai_triage.py` and uncomment **LAB STEP 3.5a** and **LAB STEP 3.5b**. Save and check that it compiles: `python -m pytest tests/test_lab_files.py -k compile` (from the repository root).
3. Run both commands again, then once more with `--verbose`.
4. Restore the correct deployment name in `app/.env` and confirm that `python -m triage_desk triage ISS-1001 --engine agent` works again.

### Prepared code
```python
# 3.5a - validate input before it's sent to a model
text = validate_issue_text(issue.text, max_issue_chars)

# 3.5b - time limit and safe fallback
try:
    response = await asyncio.wait_for(_call_agent(agent, prompt, options), timeout=timeout_seconds)
except Exception as error:
    return _fallback(issue, store, engine, error)
```

### Explanation
- **Input validation** removes control characters and rejects empty or oversized messages (`TRIAGE_MAX_ISSUE_CHARS`) without calling the model.
- **Timeout and fallback**: if the AI call fails or takes longer than `TRIAGE_REQUEST_TIMEOUT_SECONDS`, the support desk still gets a rules-based result, clearly labelled.
- **Logging**: `--verbose` shows what was sent (size only, not content), which tools ran, and why a fallback happened.
- **Output handling** is always on: the structured output is validated against `TriageDecision`, and routing always comes from the policy.

### Expected output
```text
TRIAGE RESULT  ISS-1001   engine: rules (fallback: agent failed)
...
NOTE: AI request failed (ChatClientException). Showing the rules-based result instead.
```
The error type depends on the failure and the SDK version (validated: `ChatClientException` with `DeploymentNotFound` for a wrong deployment name). If a Foundry guardrail blocks the request, the note says so instead. For the empty message: `engine: rules (input rejected)` and `NOTE: Input not sent to the AI service: The issue text is empty.`

### Checkpoint
- [ ] `python scripts/lab_state.py status` shows 3.1a through 3.5b enabled and 5.1 commented out.
- [ ] `python -m pytest` passes.

---

## Common errors and recovery
| Symptom | Likely cause | Recovery |
|---|---|---|
| `DefaultAzureCredential failed to retrieve a token` | Not signed in, the wrong tenant, or the Azure CLI starts too slowly ("Failed to invoke the Azure CLI") | `az login --tenant <tenant>`; set `LAB_CREDENTIAL_PROCESS_TIMEOUT=60` in `app/.env`; then `python -m triage_desk doctor --check-sign-in`. |
| `PermissionDenied` / HTTP 403 | Missing **Foundry User** role on the project | Ask the instructor to assign it, then wait a few minutes. |
| `NotFound` / HTTP 404 for the model | Wrong deployment name | Copy the name from **Build** > **Models**. |
| `NotFound` for the Prompt Agent | Wrong agent name or version | Check the **Version** selector or YAML in the portal. |
| `IndentationError` after uncommenting | Marker lines or extra spaces uncommented | `python scripts/lab_state.py upto 3.x` to restore that state. |
| `Category: (free text)` after 3.2 | 3.2b not enabled, or the model ignored the schema | `python scripts/lab_state.py status`; run again with `--verbose`. |

## Cleanup
None. Keep `app/.env` (it's ignored by Git).

## Knowledge check
1. Which object would you use to call an agent whose instructions are managed in the portal?
2. Why does the app still enforce routing after the agent has a routing tool?
3. What does `/new` do in the chat?
4. What does the user see if the model deployment is unavailable after Exercise 3.5?

<details><summary>Answers</summary>

1. `FoundryAgent`.
2. The model's output is never trusted for policy decisions; the app validates and enforces them.
3. Creates a new `AgentSession`, so earlier turns are forgotten.
4. A rules-based result labelled `rules (fallback: agent failed)` with a note explaining why.
</details>

## References
- [Microsoft Foundry Agent Service integration (FoundryAgent)](https://learn.microsoft.com/agent-framework/integrations/by-component/agent-services/foundry)
- [Microsoft Foundry model provider (FoundryChatClient)](https://learn.microsoft.com/agent-framework/integrations/by-component/model-providers/microsoft-foundry)
- [Agent Framework documentation](https://learn.microsoft.com/agent-framework/)
- [Quickstart: Create a prompt agent](https://learn.microsoft.com/azure/foundry/agents/quickstarts/prompt-agent) (Azure AI Projects 2.x)
- [DefaultAzureCredential](https://learn.microsoft.com/python/api/azure-identity/azure.identity.defaultazurecredential)

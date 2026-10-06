# Module 7 - Deploy the containerized agent as a hosted agent

## Objective
Deploy the same Agent Framework triage agent to **Foundry Agent Service** as a **hosted agent**, test it with the same business scenarios, review logs, compare it with the local version, and clean up.

## Status and availability (verify before delivery)
- Microsoft Learn (Agent Framework hosting) states that **Microsoft Foundry Hosted Agents is generally available**.
- `azd ai agent init` is marked **preview**, and the Python hosting package `agent-framework-foundry-hosting` is a **prerelease** build.
- Hosted agents are available in a [documented list of regions](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents#region-availability) (including UAE North at the time of writing).
- Container images must be **linux/amd64**; the container serves port **8088**; the platform provides `/readiness` routing, a dedicated Microsoft Entra **agent identity**, and a dedicated endpoint.

## Prerequisites
- Modules 3 and 6 completed (Module 5 optional).
- **Foundry Project Manager** role at project scope (needed to deploy hosted agents). See [prerequisites.md](../prerequisites.md#roles).
- Azure Developer CLI `azd` 1.27.1 or later with the Foundry extensions (install the [Foundry Dev Pack](https://learn.microsoft.com/azure/foundry/how-to/develop/install-cli-sdk), or run `azd extension install azure.ai.agents`). Validated with `azd` 1.34.1 and `azure.ai.agents` 1.0.0-beta.16.
- Docker isn't required for the deployment itself: `azd` builds the image remotely in Azure Container Registry.
- Your **project resource ID**: in the Foundry portal select **Manage** > **Project details** and copy **Resource ID**. Keep it in your private notes; don't commit it.

## Concepts introduced
- **Hosted agent**: your container, run by Foundry in per-session, VM-isolated sandboxes that scale to zero after an idle timeout (2-60 minutes, default 15).
- **Agent identity**: created at deploy time; it can call models in the project by default. Other resources (for example the search service) need explicit role assignments.
- **azure.yaml**: the single azd manifest for the project, model, and agent service.
- **Deploy modes**: `container` (Dockerfile, used here) or `code` (ZIP upload and remote build).

## Starting state
`python scripts/lab_state.py status` shows 3.1a to 3.5b enabled (and 5.1 if you completed Module 5). The container from Module 6 works.

## Resources used
Foundry project (existing), model deployment, Azure Container Registry (created or selected by `azd`), hosted agent compute (billed while sessions are active), optional search service.

## Steps

### 7.1 Sign in and check tools
```powershell
azd version
azd extension list
azd auth login
```
`azure.ai.agents` must be installed and compatible with your `azd` version. If `azd` reports an incompatible extension, update `azd` first.

### 7.2 Initialize the azd project around the existing code
From the **repository root**:

```powershell
azd ai agent init --src ./app --agent-name issue-triage-hosted --deploy-mode container `
  --project-id "<project-resource-id>" --model-deployment "<model-deployment-name>" --protocol responses -e triage-lab
```
Answer the prompts. When asked about a container registry, prefer an **existing** registry your instructor provides (or pass `--acr-connection <connection-name>`).

> **Cost warning (validated):** with `--no-prompt`, or if you accept a new registry, `azd` creates a **new resource group** named `rg-<environment>-foundry` (for example `rg-triage-lab-foundry`) with a **Premium** Azure Container Registry, billed daily. Delete that resource group during cleanup ([cost-and-cleanup.md](../cost-and-cleanup.md)).

The command generates `azure.yaml` at the repository root, `app/.agentignore`, and an `.azure/<environment>` folder (ignored by Git). It doesn't overwrite your code.

> **Warning (from Microsoft Learn):** when you initialize against an existing project with `--project-id`, the tooling skips the automatic role assignments it performs for new projects. Your instructor must confirm the roles in the [role checklist](../instructor-guide.md#role-checklist).

### 7.3 Review and complete azure.yaml
1. Open the generated `azure.yaml` and compare it with [deployment/azure.yaml.reference](../../deployment/azure.yaml.reference). Keep what `azd` generated; only add what's missing. In validation, `azd` generated:
   - `ai-project` with `endpoint: ${FOUNDRY_PROJECT_ENDPOINT}` (connects to your existing project),
   - the agent service with `language: docker`, `docker: remoteBuild: true` (the image is built in Azure Container Registry, so local Docker isn't needed), `kind: hosted`, the `responses` protocol, `startupCommand: python main.py`, and `cpu: "0.5"` / `memory: 1Gi`,
   - `env: AZURE_AI_MODEL_DEPLOYMENT_NAME: ${AZURE_AI_MODEL_DEPLOYMENT_NAME}` (the app accepts this name as well as `MICROSOFT_FOUNDRY_MODEL_DEPLOYMENT_NAME`).
2. Add these entries under the agent service `env:` if you completed Module 5:

   ```yaml
   AZURE_SEARCH_ENDPOINT: ${AZURE_SEARCH_ENDPOINT}
   AZURE_SEARCH_KNOWLEDGE_BASE_NAME: ${AZURE_SEARCH_KNOWLEDGE_BASE_NAME}
   LOG_LEVEL: INFO
   ```
   Don't add `FOUNDRY_PROJECT_ENDPOINT` or other `FOUNDRY_*` variables: the platform injects them.
3. Set the values in the azd environment (stored under `.azure/`, not in source):

   ```powershell
   azd env set AZURE_SEARCH_ENDPOINT https://<search-service>.search.windows.net -e triage-lab   # Module 5 only
   azd env set AZURE_SEARCH_KNOWLEDGE_BASE_NAME kb-triage -e triage-lab                           # Module 5 only
   ```

### 7.4 Provision (and optionally test locally with azd)
```powershell
azd provision -e triage-lab
```
Validated: about 1-2 minutes; it creates the container registry and its project connection. Optional: `azd ai agent run` starts the agent locally with the `startupCommand` and opens the Agent Inspector; in a second terminal, `azd ai agent invoke --local "Triage issue ISS-1001"`. Stop it with **Ctrl+C**.

### 7.5 Deploy the hosted agent
```powershell
azd deploy -e triage-lab
```
`azd` packages the `app` folder, builds the image in Azure Container Registry, creates a hosted agent version, and polls until it's active (validated: about 2.5 minutes). The output ends with `SUCCESS` and the next steps (`azd ai agent show`, `azd ai agent invoke`).

### 7.6 Verify deployment status
```powershell
azd ai agent show issue-triage-hosted -e triage-lab --output json
```
Check `"status": "active"`, the `container_configuration.image`, the `environment_variables`, `agent_endpoints.responses`, and `instance_identity.principal_id` (the agent identity). In the Foundry portal, `issue-triage-hosted` appears under **Build** > **Agents** with type **Hosted**.

### 7.7 Grant the agent identity access to the knowledge base (Module 5 only)
From the repository root, use the `instance_identity.principal_id` from step 7.6:

```powershell
./deployment/assign-hosted-agent-roles.ps1 -AgentPrincipalId <principal-id> `
    -SearchServiceName <search-service> -ResourceGroup <lab-resource-group>
```
This assigns **Search Index Data Reader** and **Reader** on the lab search service only. Both are required: without **Reader**, the agent fails with `Operation returned an invalid status 'Forbidden'` because the knowledge base provider can't read the knowledge base definition. Role assignments can take a few minutes.

### 7.8 Invoke the hosted agent with the same scenarios
```powershell
azd ai agent invoke issue-triage-hosted "Triage issue ISS-1014" -e triage-lab
azd ai agent invoke issue-triage-hosted "Why did you choose that priority?" -e triage-lab     # same session
azd ai agent invoke issue-triage-hosted "Triage issue ISS-1001" -e triage-lab --new-session  # KI-2041 if Module 5 is enabled
```
Validated results: ISS-1014 is `ROAMING` / `P1` / Roaming Desk (1 hour); the follow-up explains the P1 using the earlier turn; ISS-1001 shows `Known issue: KI-2041`. The output also shows the conversation, session, and trace IDs. You can also chat with `issue-triage-hosted` in the portal playground.

### 7.9 Review logs and diagnostics
```powershell
azd ai agent monitor issue-triage-hosted -e triage-lab
azd ai agent monitor issue-triage-hosted -e triage-lab --follow
```
Look for `Starting issue-triage-agent (knowledge base: on) on port 8088` and the `[tool call]` lines. A startup line `ModuleNotFoundError: No module named 'agents'` comes from an optional tracing plug-in and is harmless. If Application Insights is connected to the project (Module 8), the platform injects `APPLICATIONINSIGHTS_CONNECTION_STRING`.

### 7.10 Compare local and hosted behaviour
| Aspect | Local CLI / container | Hosted agent |
|---|---|---|
| Identity | Your `az login` user (or dev tokens in the container) | Platform-created agent identity |
| Endpoint | `localhost:8088` | `{project_endpoint}/agents/issue-triage-hosted/endpoint/protocols/openai/responses` |
| Conversation | CLI session object / single requests | Platform-managed sessions (`--new-session` resets) |
| Scale and cost | Your machine | Per-session sandboxes, scale to zero after the idle timeout; billed for active CPU and memory |
| Logs | Terminal / `docker logs` | `azd ai agent monitor`, Application Insights |

### 7.11 Clean up the hosted deployment
When you've finished Modules 8 and 9 (or if your instructor asks you to stop now):

```powershell
azd ai agent delete issue-triage-hosted --force -e triage-lab
```
`--force` terminates active sessions. Don't run `azd down` against a shared or existing project unless your instructor confirms what it deletes. Remove the `azd`-created resource group (`rg-<environment>-foundry`, which holds the Premium container registry) and the lab resource group as described in [cost-and-cleanup.md](../cost-and-cleanup.md).

## Expected output
- `azd deploy` ends with the agent playground link and endpoint.
- `azd ai agent show` reports an active version.
- `invoke` returns triage cards equivalent to the local results; the follow-up question uses the earlier turn.

## Verification checkpoint
- [ ] The hosted agent answers ISS-1014 as `ROAMING` / `P1`.
- [ ] `azd ai agent monitor` shows tool calls.
- [ ] (Module 5) ISS-1001 links to `KI-2041`.

## Common errors and recovery
| Symptom | Likely cause | Recovery |
|---|---|---|
| `azure.ai.agents` extension incompatible | Old `azd` | Update `azd`, then `azd extension upgrade --all`. |
| Authorization error during deploy | Missing **Foundry Project Manager** | Ask the instructor; wait a few minutes after assignment. |
| Image pull failure | Project managed identity lacks registry access | Instructor assigns **Container Registry Repository Reader** on the registry. |
| Agent version fails to start | Module 3 steps not enabled in the image, or a missing environment variable | `azd ai agent monitor`; `python scripts/lab_state.py upto 3.5`; check `env:` in `azure.yaml`; `azd deploy` again. |
| `agent failed (server_error): Operation returned an invalid status 'Forbidden'` | Agent identity lacks **Reader** and/or **Search Index Data Reader** on the search service | Run the role script in step 7.7; wait 2-5 minutes; invoke again. |
| Remote build fails with `the --mount option requires BuildKit` | A Dockerfile uses BuildKit-only syntax | Azure Container Registry builds don't support it; use the provided Dockerfile. |
| Region not supported | Region not in the hosted-agent list | Use a supported region for the lab project. |

## Knowledge check
1. Which identity does the hosted agent use to call the model?
2. Why must you not declare `FOUNDRY_PROJECT_ENDPOINT` in `azure.yaml`?
3. When does a hosted agent stop consuming compute?

<details><summary>Answers</summary>

1. Its platform-created Microsoft Entra agent identity.
2. The platform injects it; `FOUNDRY_*` names are reserved.
3. After the idle timeout with no requests (default 15 minutes); the session state is persisted.
</details>

## References
- [Hosted agents in Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Quickstart: Deploy your first hosted agent](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [Initialize a hosted agent project with azd](https://learn.microsoft.com/azure/foundry/agents/how-to/init-agent-project)
- [Author azure.yaml for hosted agents](https://learn.microsoft.com/azure/foundry/agents/how-to/author-azure-yaml) and [azure.yaml reference](https://learn.microsoft.com/azure/foundry/agents/concepts/azure-yaml-reference)
- [Deploy a hosted agent](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Hosted agent permissions reference](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agent-permissions)
- [Foundry Hosted Agents (Agent Framework)](https://learn.microsoft.com/agent-framework/hosting/foundry-hosted-agent)

> **Documentation gaps:** (1) The documentation doesn't state that, without an existing registry, `azd ai agent init` creates a separate `rg-<environment>-foundry` resource group with a Premium registry (observed in validation). (2) The knowledge base provider's need for the **Reader** role isn't documented. (3) The agent identity principal ID is available as `instance_identity.principal_id` in `azd ai agent show --output json` (validated) and in the agent YAML.

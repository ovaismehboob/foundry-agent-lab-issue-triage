# Module 6 - Containerize the application

## Objective
Package the same triage agent as a container image, run it locally, pass configuration safely, test it over the Responses protocol, read its logs, and clean up.

> **This module is optional — skip it if local Docker builds are blocked.** Building the image locally (step 6.2) downloads from third-party sites: the base image from **Docker Hub** and Python packages from **PyPI** (`pypi.org`). If your network blocks these (corporate proxy, TLS inspection, or an air-gapped lab), you can't build locally, and there is no portal/offline workaround for the download itself. **You do not need a local image to continue** — in [Module 7](module-07-hosted-agent.md), `azd deploy` builds the *same* Dockerfile remotely in Azure Container Registry, so the deployment path does not depend on this module. If downloads are blocked, read through this module for understanding and go straight to Module 7. The only parts you lose by skipping are the local run (6.1), the local container test (6.4), and reading local `docker logs` (6.5).

## Prerequisites
- Module 3 completed (Module 5 optional). Check with `python scripts/lab_state.py status`: at least 3.1b, 3.2a, 3.2b, and 3.3 must be enabled, because the container serves the code-defined agent.
- Docker Desktop (or another Docker engine) running with Linux containers.

## Concepts introduced
- **Hosting adapter**: `ResponsesHostServer` from `agent-framework-foundry-hosting` exposes the agent over the Foundry **Responses** protocol on port **8088**, with a `/readiness` health endpoint.
- Container image layers, `.dockerignore`, non-root user.
- Configuration through environment variables (`--env-file`), never baked into the image.

## Starting state
The app works locally with `--engine agent`.

## Resources used
Local Docker only. The container calls your Foundry model (and knowledge base, if enabled).

## Review the provided files
| File | What to look for |
|---|---|
| [app/main.py](../../app/main.py) | Builds the same agent with `build_triage_agent(..., hosting=True)` and starts `ResponsesHostServer(agent)`. `hosting=True` sets `store=False`, as in the official samples, because the hosting platform manages conversation history. |
| [app/Dockerfile](../../app/Dockerfile) | `python:3.13-slim` base; installs pinned requirements first (cached layer); copies code, prompts, and data; runs as a non-root user; `EXPOSE 8088`; `CMD ["python", "main.py"]`. |
| [app/.dockerignore](../../app/.dockerignore) | Excludes `.env`, `.env.*`, virtual environments, caches, and `.azure`, so no secrets reach the build context or image. |

## Steps

### 6.1 Run the hosting entry point without Docker
From the `app` folder:

```powershell
python main.py
```
Wait for `Starting issue-triage-agent ... on port 8088`. In a **second** terminal, from the repository root:

```powershell
python scripts/invoke_local_agent.py --ready
python scripts/invoke_local_agent.py "Triage issue ISS-1014"
```
Stop the server with **Ctrl+C**.

> If port 8088 is already used on your machine, set `$env:PORT="18088"` before `python main.py`, and add `--port 18088` to the invoke commands.

### 6.2 Build the image
From the `app` folder:

```powershell
docker build --platform linux/amd64 -t issue-triage-agent:1.0 .
```
`--platform linux/amd64` matters on ARM machines (for example Apple silicon): Foundry hosted agents require x86_64 images.

> **If the build can't download packages** (corporate proxy, TLS inspection, or blocked PyPI), build in Azure instead. In Module 7, `azd deploy` builds the same Dockerfile remotely in Azure Container Registry (`docker: remoteBuild: true`). You can then pull that image and run steps 6.3-6.6 with it:
> ```powershell
> az acr login -n <registry-name>
> docker pull <registry-name>.azurecr.io/<repository>:<tag>
> docker tag <registry-name>.azurecr.io/<repository>:<tag> issue-triage-agent:1.0
> ```
> The image name is shown in `azd ai agent show` under `container_configuration.image`.

### 6.3 Create the container environment file
The container can't use your `az login` session. For **local testing only**, create a file with your non-secret settings plus two short-lived access tokens:

```powershell
./scripts/new-container-env.ps1        # macOS/Linux: ./scripts/new-container-env.sh
```

This writes `app/.env.container`, which Git and Docker ignore. The tokens expire (typically within 60-90 minutes); run the script again if you see authentication errors. `triage_desk/credentials.py` uses these tokens only when `LAB_DEV_TOKEN_*` variables are set; otherwise it uses `DefaultAzureCredential`. The hosted agent in Module 7 never uses them.

### 6.4 Run and test the container
```powershell
docker run --rm -d --name triage-agent -p 8088:8088 --env-file app/.env.container issue-triage-agent:1.0
python scripts/invoke_local_agent.py --ready
python scripts/invoke_local_agent.py "Triage issue ISS-1001"
python scripts/invoke_local_agent.py "Triage issue ISS-1012"
```
(Port conflict: `-p 18088:8088` and `--port 18088`.)

### 6.5 Review the logs
```powershell
docker logs triage-agent
```
Look for the startup line, the `[tool call]` lines printed by the tool middleware, and any warnings. The log also shows `Using LOCAL DEV TOKENS`, which confirms the container isn't using a stored credential.

### 6.6 Stop and remove
```powershell
docker stop triage-agent                    # --rm removes the container when it stops
docker image ls issue-triage-agent
Remove-Item app/.env.container              # delete the short-lived tokens
```
Keep the image if you continue to Module 7 (the deployment builds its own image, so you can also remove it with `docker image rm issue-triage-agent:1.0`).

## Expected output (validated 5 October 2026)
```text
readiness: HTTP 200
status: completed   response id: caresp_...
Category: DEVICE_SIM
Priority: P2 - ...
Routed team: Device & SIM Support, first-response SLA 4 hours
Known issue: None
Safety flags: possible_prompt_injection
...
```
In hosted mode the agent replies with the **triage card** text format from the instructions (the structured-output schema is used only by the CLI `triage` command). The tool calls (`get_issue`, `get_customer_context`, `route_issue`) appear in `docker logs`.

> Teaching point: for "Triage issue ISS-1012", the agent fetches the ticket text with the `get_issue` tool, so the injected instruction arrives as a **tool response**, not as user input. The default guardrail didn't block it, and the agent's instructions flagged it. Module 8 shows the guardrail controls for tool responses.

## Verification checkpoint
- [ ] `/readiness` returns HTTP 200 from the container.
- [ ] A triage request returns `status: completed`.
- [ ] `docker logs` shows tool calls.
- [ ] `app/.env.container` is deleted at the end.

## Common errors and recovery
| Symptom | Likely cause | Recovery |
|---|---|---|
| `LAB STEP 3.1b is not enabled yet` in the logs, container exits | Module 3 not completed | `python scripts/lab_state.py upto 3.5`, rebuild the image. |
| `status: failed` with an authentication error | Tokens expired or missing | Run `new-container-env` again and restart the container. |
| `PermissionError` / port in use | Another process uses 8088 | Map another host port: `-p 18088:8088`. |
| `pip install` fails during build | Proxy or private package feed | Build remotely in Azure Container Registry (see 6.2), or see [troubleshooting.md](../troubleshooting.md#package-installation). |
| `exec format error` when running elsewhere | ARM image | Rebuild with `--platform linux/amd64`. |

## Knowledge check
1. Why is `.env` excluded from the build context?
2. What does `/readiness` tell you?
3. Why does the hosted agent in Module 7 not need the dev tokens?

<details><summary>Answers</summary>

1. So configuration values and secrets never end up in an image layer.
2. That the agent server has started and can accept requests.
3. Foundry Agent Service gives each hosted agent its own Microsoft Entra agent identity.
</details>

## References
- [Hosted agents in Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
- [Deploy a hosted agent - container requirements](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent#container-requirements)
- [Foundry Hosted Agents (Agent Framework hosting)](https://learn.microsoft.com/agent-framework/hosting/foundry-hosted-agent)
- [Official Python hosted-agent samples](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework)

> **Documentation gap:** Microsoft documentation doesn't describe how to authenticate a hosted-agent container when you run it with plain `docker run` on a laptop. The .NET samples mention "a temporary dev token" for local Docker debugging. This lab implements that approach as a clearly labelled, local-only credential (validated with an image built by Azure Container Registry). The official alternative is `azd ai agent run` (Module 7), which runs the agent locally without a container.

# Troubleshooting

Start with `python -m triage_desk doctor --check-sign-in` (from `app`) and `python -m pytest` (from the repository root). Run any failing app command again with `--verbose`.

## Lab state and code
| Symptom | Cause | Fix |
|---|---|---|
| `LAB STEP x is not enabled yet` | The section is still commented out | Uncomment it, or `python scripts/lab_state.py enable x`. |
| `IndentationError` / `SyntaxError` after uncommenting | Marker lines uncommented, or extra spaces | `python scripts/lab_state.py upto <step>` restores a clean state. Your previous files are in `.lab-backup/`. |
| Unsure which steps are on | | `python scripts/lab_state.py status` |
| Need the completed code | | `python scripts/lab_state.py solution`, or read `solution/app/triage_desk/`. |

## Package installation
| Symptom | Cause | Fix |
|---|---|---|
| `SSL: ... HANDSHAKE_FAILURE` or `getaddrinfo failed` during `pip install` | Corporate proxy, TLS inspection, or a private package feed | Use your organization's package mirror (`pip config list` shows the current configuration). Ask IT for the proxy certificate and use `pip --cert`. Don't disable certificate verification. |
| `pip` can't find a `b` (beta) version | Mirror doesn't sync prerelease packages | Ask for the exact pinned versions in `app/requirements.txt` to be mirrored. |
| `docker build` fails in `pip install` with SSL errors | The container can't use your proxy or mirror | Build remotely in Azure Container Registry: `azd deploy` does this (`docker: remoteBuild: true`), then pull the image for local tests (Module 6.2). Don't use BuildKit-only `RUN --mount` syntax; Azure Container Registry builds don't support it. |
| `Activate.ps1 cannot be loaded` | Execution policy | `Set-ExecutionPolicy -Scope Process RemoteSigned` |

## Authentication and permissions
| Symptom | Cause | Fix |
|---|---|---|
| `DefaultAzureCredential failed to retrieve a token` | Not signed in | `az login` (add `--tenant <id>` for multi-tenant accounts). |
| `AzureCliCredential: Failed to invoke the Azure CLI` | The Azure CLI starts slowly (for example many extensions) and the 10-second default timeout expires | Set `LAB_CREDENTIAL_PROCESS_TIMEOUT=60` in `app/.env` (the app's default is 30). |
| HTTP 401 | Wrong tenant, or expired token | `az account show`; `az login` again. In a container, rerun `scripts/new-container-env`. |
| HTTP 403 from Foundry | Missing Foundry User role | Instructor assigns it; wait up to 10 minutes. |
| `Forbidden` from `get_knowledge_base` (local or hosted) | Missing **Reader** on the search service | Assign **Reader** plus **Search Index Data Reader** (`deployment/assign-hosted-agent-roles.ps1` for the hosted agent). |
| HTTP 403 from Azure AI Search | Missing Search Index Data Reader, or search API access control set to keys only | Assign the role; set **API access control** to **Both**. |
| `Knowledge source ... kind 'file' ... not supported in this API version` | GA `azure-search-documents` | Reinstall `requirements-dev.txt` (pins 12.1.0b2). |
| Request blocked: "blocked by a safety and security control in this asset's Foundry guardrail" | A guardrail (default or custom) detected a risk, for example a jailbreak | Expected for prompt-attack tests. The CLI shows a rules fallback with a guardrail note. |
| Hosted agent can't reach search | Agent identity has no role | `deployment/assign-hosted-agent-roles.ps1` |

## Configuration
| Symptom | Cause | Fix |
|---|---|---|
| `Missing configuration for engine ...` | `app/.env` missing or values empty | Copy `app/.env.example` to `app/.env` and fill in the values. Values like `<your-...>` count as empty. |
| Model `NotFound` | Wrong deployment name | Copy it from **Build** > **Models**. |
| Prompt Agent `NotFound` | Wrong name or version | Check the **Version** selector / YAML in the portal. |
| Knowledge base `NotFound` | Wrong name | **Build** > **Knowledge**. |

## Running the agent server and container
| Symptom | Cause | Fix |
|---|---|---|
| `PermissionError: [WinError 10013]` or `address already in use` on 8088 | Another process uses port 8088 | Set `PORT=18088` for `python main.py`, or map `-p 18088:8088` for Docker, and use `--port 18088` with `invoke_local_agent.py`. |
| `/readiness` refuses connections right after start | Server still starting (imports take a few seconds) | Wait 10-30 seconds and retry. |
| `status: failed` with `Connection error` | Wrong project endpoint, or no network access | Check `FOUNDRY_PROJECT_ENDPOINT` and the network list in [prerequisites.md](prerequisites.md#local-tools). |
| `status: failed` with `Forbidden` | Token missing or expired, or missing role | Recreate `app/.env.container`; check roles. |
| `exec format error` | ARM image | Rebuild with `--platform linux/amd64`. |

## azd and hosted agents
| Symptom | Cause | Fix |
|---|---|---|
| Extension marked **Incompatible** | `azd` too old for the extension | Update `azd`, then `azd extension upgrade --all`. |
| `azd ai agent init` asks for values you don't have | Interactive prompts | Use the values from your notes; the project resource ID is under **Manage** > **Project details**. |
| Agent version fails to start | Steps not enabled, or env var missing | `azd ai agent monitor`; check `azure.yaml` `env:`; `azd deploy` again. |
| Image pull failure | Registry role missing for the project identity | Instructor assigns **Container Registry Repository Reader**. |
| An extra resource group `rg-<env>-foundry` with a Premium registry appeared | `azd ai agent init` created a registry because none was selected | Expected; delete it during cleanup, or select an existing registry at init. |

## Azure Storage and Foundry IQ
| Symptom | Cause | Fix |
|---|---|---|
| Upload or Blob knowledge source fails with "The request may be blocked by network rules of storage account" | Tenant policy forces storage **Public network access: Disabled** | Use Module 4 option B (File knowledge source), or private networking. Don't weaken policy-enforced settings. |
| Agent answers without using the knowledge base | Instructions don't require the knowledge base tool | Append `app/prompts/knowledge_instructions.md` ("ALWAYS call") and save. |
| Agent finds the outage but not the incident ID | Chunking separated the heading from the details | Keep the `- Incident ID:` lines in the bulletin and re-upload. |

## Portal
| Symptom | Cause | Fix |
|---|---|---|
| Menus don't match the guide | **New Foundry** is off, or the portal changed | Turn on **New Foundry**. If it still differs, record the difference for the instructor. |
| No traces | Application Insights not connected, or ingestion delay | **Agents** > **Traces** > **Connect**; wait a few minutes. |
| Guardrail doesn't block anything | Assigned to the model, not the agent, or uses risks not supported for agents | Assign it to the agent; review the risk table in the guardrails overview. |
| Evaluation **Failed** / **Partial** | Judge model missing/quota, or field mapping | Pick a judge deployment with quota; map `query`. |

## Getting help
Collect: the command, the output with `--verbose` (remove any tokens or IDs), `python scripts/lab_state.py status`, and `python -m triage_desk doctor`. Never share `app/.env` or `app/.env.container`.

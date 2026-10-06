# Prerequisites

Complete this page before Module 1. Your instructor may have prepared some items for you.

## Local tools

| Tool | Version | Used in | Notes |
|---|---|---|---|
| Python | 3.11 to 3.13 (3.13 recommended) | Modules 2-9 | The container image uses Python 3.13. Microsoft's Foundry IQ lab notes that Python 3.14 isn't supported yet by some dependencies. |
| Git | current | Setup | To clone the repository. |
| Visual Studio Code + Python extension | current | All | Ctrl+/ toggles comments for the LAB STEPs. |
| Azure CLI (`az`) | current | Modules 3-9 | `az login` provides your identity to `DefaultAzureCredential`. |
| Azure Developer CLI (`azd`) | 1.27.1 or later | Module 7 | Install the [Foundry Dev Pack](https://learn.microsoft.com/azure/foundry/how-to/develop/install-cli-sdk), or `azd extension install azure.ai.agents`. |
| Docker Desktop (Linux containers) | current | Modules 6-7 | Hosted agents need `linux/amd64` images. |

Network access is needed to: `*.services.ai.azure.com`, `*.search.windows.net`, `management.azure.com`, `login.microsoftonline.com`, the Python package index (or your organization's mirror), Docker Hub (`python:3.13-slim`), and your Azure Container Registry.

## Python packages
Pinned in [app/requirements.txt](../app/requirements.txt) and tested together:

| Package | Version | Status |
|---|---|---|
| agent-framework-core | 1.19.0 | Release |
| agent-framework-foundry | 1.13.1 | Release (uses `azure-ai-projects` 2.x, the Foundry (new) API) |
| agent-framework-foundry-hosting | 1.0.0b260918 | **Prerelease** |
| agent-framework-azure-ai-search | 1.0.0b260910 | **Prerelease** |
| azure-ai-agentserver-responses | 2.2.0 | Release |
| azure-ai-projects | 2.6.1 | Release |
| azure-search-documents | 12.1.0b2 | **Prerelease** (needed for the **File** knowledge source kind; the GA 12.0.0 build rejects it) |
| azure-identity | 1.26.0 | Release |
| pydantic | 2.13.5 | Release |

Don't mix these with samples that use `azure-ai-projects` 1.x (Foundry classic).

## Azure subscription and resource group
- An Azure subscription where you can create resources, or a lab project prepared by your instructor.
- A **dedicated, non-production resource group**, for example `rg-foundry-agent-lab-<initials>`. Everything in this lab is created in that resource group, except the container registry that `azd` may create in its own resource group (Module 7).
- Registered resource providers: `Microsoft.CognitiveServices`, `Microsoft.Search`, `Microsoft.Storage`, `Microsoft.ContainerRegistry`, `Microsoft.Insights`, `Microsoft.OperationalInsights`.
- Check tenant policies before the workshop. In the validation tenant, policy forced **Public network access: Disabled** and **shared key access disabled** on new storage accounts, and API-key authentication was disabled on the Foundry resource. The lab works with these policies (Module 4 option B, managed identities everywhere).

## Region
Use **one region** for all lab resources. Your instructor confirms it before the workshop. The region must support all of the following (check the linked pages; availability changes):

> Validated region: **France Central** (5 October 2026). UAE North supports hosted agents and agentic retrieval, but the Azure AI Search region list marked it "in high demand, which prevents the creation of new search services" at the time of validation.

| Requirement | Where to check |
|---|---|
| Hosted agents | [Hosted agents region availability](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents#region-availability) (includes UAE North at the time of writing) |
| Your chat model (for example `gpt-5-mini`) with quota | Model catalog in the Foundry portal; quota page |
| Embedding model (for example `text-embedding-3-small`) | Model catalog |
| Azure AI Search agentic retrieval | [Search region support](https://learn.microsoft.com/azure/search/search-region-support) |
| Guardrails / Azure AI Content Safety | [Content Safety region availability](https://learn.microsoft.com/azure/ai-services/content-safety/overview#region-availability) |
| Evaluation judge model (for example `gpt-4.1-mini`) | Model catalog |

## Roles
Use the least privilege that works. The Foundry roles were renamed recently (Foundry User was Azure AI User, and so on); you might see either name.

| Who | Role | Scope | Why |
|---|---|---|---|
| Instructor / setup account | Owner, or Contributor + User Access Administrator | Lab resource group | Create resources and assign roles |
| Student creating their own project | Owner | Own lab resource group | Microsoft Learn requires Owner at resource-group scope to create a new project for hosted agents |
| Student | **Foundry User** | Foundry resource/project | Use models, create and run agents (Modules 1, 3, 9) |
| Student | **Foundry Project Manager** | Project | Create project connections (Module 4) and deploy hosted agents (Module 7) |
| Student or instructor | **Foundry Account Owner** | Foundry resource | Create guardrails (Module 8) |
| Student | **Search Service Contributor** + **Search Index Data Contributor** | Search service | Create the knowledge base in the portal (Module 4) |
| Student | **Search Index Data Reader** + **Reader** (or Search Service Contributor) | Search service | Query the knowledge base from Python; the provider reads the knowledge base definition first (Module 5) |
| Student | **Log Analytics Reader** | Application Insights / Log Analytics | View traces (Module 8) |
| Project managed identity | **Search Index Data Reader**, **Search Index Data Contributor**, **Search Service Contributor** | Search service | Foundry IQ connection with Project Managed Identity (Module 4) |
| Hosted agent identity | **Search Index Data Reader** + **Reader** | Search service | Query the knowledge base when hosted (Module 7.7) |
| Project managed identity | **Container Registry Repository Reader** | Container registry | Pull the agent image (assigned by `azd` for new projects; check for existing projects) |
| Search service managed identity | **Cognitive Services User** | Foundry resource | The knowledge base calls the embedding and chat models (required when API-key auth is disabled on the Foundry resource) |
| Search service managed identity | **Storage Blob Data Reader** | Storage account | Blob knowledge source (Module 4 option A) |

See [Role-based access control for Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry) and [Hosted agent permissions](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agent-permissions).

## Check your setup
From the repository root, after Module 2 setup:

```powershell
python -m pytest
cd app
python -m triage_desk doctor --check-sign-in
```

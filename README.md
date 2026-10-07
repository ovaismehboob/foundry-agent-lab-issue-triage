# Microsoft Foundry Agent Lab - Contoso Telecom Issue Triage Assistant

A hands-on, instructor-led lab that takes one small Python application through the full lifecycle of a Microsoft Foundry agent: build, ground, containerize, host, govern, monitor, and evaluate.

The application triages customer issues for **Contoso Telecom**, a fictional operator. It covers five customer use cases:

1. **Issue classification** into predefined categories (network, device/SIM, billing, roaming, account, service complaint).
2. **Context and keyword use** for categorisation: a keyword baseline compared with a context-aware agent.
3. **Prioritisation and routing** to the right team, with routing enforced by policy.
4. **Acknowledgments** with relevant details and troubleshooting steps for the issue type.
5. **Notifications** that link an issue to an existing solution or known incident, using Foundry IQ.

All data is synthetic. No real customers, incidents, or credentials are included.

## Lab modules

| # | Module | Mode |
|---|---|---|
| 1 | [Create a Prompt Agent in the Foundry portal](docs/student/module-01-prompt-agent-portal.md) | Portal |
| 2 | [Build and run the basic Python application](docs/student/module-02-basic-app.md) | Python |
| 3 | [Extend the app with Microsoft Agent Framework](docs/student/module-03-agent-framework.md) | Python |
| 4 | [Configure Foundry IQ with Azure Storage](docs/student/module-04-foundry-iq-portal.md) | Portal |
| 5 | [Use Foundry IQ from the app](docs/student/module-05-foundry-iq-app.md) | Python |
| 6 | [Containerize the application](docs/student/module-06-containerize.md) | Docker |
| 7 | [Deploy as a hosted agent](docs/student/module-07-hosted-agent.md) | azd |
| 8 | [Govern and monitor with the Foundry control plane](docs/student/module-08-control-plane.md) | Portal |
| 9 | [Evaluate the agent with a local dataset](docs/student/module-09-evaluation.md) | Portal + Python |

Start with the [student guide](docs/student-guide.md). Instructors: read the [instructor guide](docs/instructor-guide.md) first.

## Quick start (Module 2, no Azure needed)

```powershell
git clone https://github.com/ovaismehboob/foundry-agent-lab-issue-triage.git
cd foundry-agent-lab-issue-triage
code .
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest
cd app
python -m triage_desk queue
python -m triage_desk triage ISS-1009
```

## Repository layout

```text
README.md                 this file
SECURITY.md               security notes for the lab
LICENSE                   MIT license
requirements-dev.txt      app requirements + pytest
pyproject.toml            pytest configuration
app/                      the application (Modules 2-7); also the container build context
  .env.example            configuration template (copy to app/.env, never commit .env)
  Dockerfile, .dockerignore
  main.py                 hosted agent entry point (Responses protocol, port 8088)
  requirements.txt        pinned runtime dependencies
  prompts/                agent instructions (shared with the portal Prompt Agent)
  data/                   synthetic issues, customers, taxonomy, routing policy
  triage_desk/            application package (starter state: LAB STEPs commented out)
solution/app/triage_desk/ completed versions of the two files students edit
knowledge/                synthetic knowledge documents for Foundry IQ (Module 4)
evaluation/               JSONL evaluation dataset, schema notes, instruction change for Module 9
scripts/                  lab state switcher, dataset builder/uploader, scorer, container env, cleanup
deployment/               azure.yaml reference and role-assignment helper for the hosted agent
docs/                     student guide, modules, instructor guide, architecture, prerequisites,
                          troubleshooting, cost and cleanup, images
tests/                    offline tests (rules, tools, AI handling with fakes, lab files, dataset, hygiene)
```

## Technology and status
- **Microsoft Foundry (new)** projects and `azure-ai-projects` 2.x. Not compatible with Foundry (classic) samples.
- **Microsoft Agent Framework** for Python, pinned versions in [app/requirements.txt](app/requirements.txt). The hosting and Azure AI Search integrations are prerelease packages.
- Several features used here are in **preview** (agent guardrails, Foundry IQ portal experience, tracing and monitoring dashboard, `azd ai agent init`). See [prerequisites](docs/prerequisites.md) and the [instructor guide](docs/instructor-guide.md#preview-feature-risks).

## Costs
The lab creates billable Azure resources (model usage, Azure AI Search, Container Registry, hosted agent compute, Application Insights). Use a dedicated resource group and follow [cost-and-cleanup.md](docs/cost-and-cleanup.md) at the end.

## Documentation
- [Architecture](docs/architecture.md)
- [Prerequisites](docs/prerequisites.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Cost and cleanup](docs/cost-and-cleanup.md)
- [Evaluation dataset schema](evaluation/README.md)

## Authors and maintainers
- **Ovais Mehboob** ([@ovaismehboob](https://github.com/ovaismehboob)) - author and maintainer

Contributions are welcome. Please open an issue or pull request on [GitHub](https://github.com/ovaismehboob/foundry-agent-lab-issue-triage).

## License
This project is licensed under the [MIT License](LICENSE) - Copyright (c) 2026 Ovais Mehboob.

Third-party material referenced (not copied) by the guides keeps its own license (for example, Microsoft Learning screenshots under MIT and Microsoft Learn content under the Microsoft Learn terms of use). All sample data is synthetic.

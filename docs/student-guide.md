# Student guide - Contoso Telecom Issue Triage Assistant

In this lab you build one application, the **Issue Triage Assistant** for the fictional operator Contoso Telecom, and extend it step by step. You end up with an AI agent that runs locally, in a container, and as a Microsoft Foundry hosted agent. It is grounded in company knowledge, governed with guardrails, monitored, and evaluated.

All data is synthetic. Contoso Telecom, its customers, areas, and incidents are fictional.

## What the assistant does

| Customer use case | Where you build it |
|---|---|
| Issue classification into predefined categories | Module 2 (keywords), Module 3 (agent) |
| Context and keyword use for categorisation | Module 2 compared with Module 3 |
| Prioritisation and routing to the right team | Module 2 rules, Module 3.3 routing tool |
| Acknowledgment with relevant details and troubleshooting steps | Module 3.2 onwards |
| Notification that links an issue to an existing solution | Module 4 (portal) and Module 5 (app) with Foundry IQ |

## Modules

| # | Module | Type |
|---|---|---|
| 1 | [Create a Prompt Agent in the Microsoft Foundry portal](student/module-01-prompt-agent-portal.md) | Portal |
| 2 | [Build and run the basic Python application](student/module-02-basic-app.md) | Python |
| 3 | [Extend the application with Microsoft Agent Framework](student/module-03-agent-framework.md) | Python |
| 4 | [Configure Foundry IQ with Azure Storage](student/module-04-foundry-iq-portal.md) | Portal |
| 5 | [Use Foundry IQ from the Python application](student/module-05-foundry-iq-app.md) | Python |
| 6 | [Containerize the application](student/module-06-containerize.md) | Docker |
| 7 | [Deploy as a hosted agent](student/module-07-hosted-agent.md) | azd / portal |
| 8 | [Govern and monitor with the Foundry control plane](student/module-08-control-plane.md) | Portal |
| 9 | [Evaluate the agent with a local dataset](student/module-09-evaluation.md) | Portal + Python |

Before you start, complete [prerequisites.md](prerequisites.md). If something goes wrong, see [troubleshooting.md](troubleshooting.md). At the end, follow [cost-and-cleanup.md](cost-and-cleanup.md).

## Get the lab files

```powershell
git clone https://github.com/ovaismehboob/foundry-agent-lab-issue-triage.git
cd foundry-agent-lab-issue-triage
code .
```

The repository starts in the **starter state**. Check it with `python scripts/lab_state.py status` after the Module 2 setup; every LAB STEP shows "commented out". Each student uses their own Azure resources (or the project the instructor gives them) and their own `app/.env`, which Git ignores.

## How the coding exercises work

You don't type long code listings. The code is already in the repository, commented out, between markers like this:

```python
    # ===== LAB STEP 3.3: UNCOMMENT THIS SECTION (expose app functions as tools and log every tool call) =====
    # tools = agent_tools()
    # middleware = [tool_logging_middleware()]
    # ===== END LAB STEP 3.3 =====
```

To enable a step:

1. Open the file named in the exercise (usually `app/triage_desk/agent_factory.py`).
2. Select only the commented code lines **between** the two marker lines. Don't select the marker lines.
3. Press **Ctrl+/** (Windows/Linux) or **Cmd+/** (macOS) to uncomment them, and save the file.
4. Check that the file still compiles:

   ```powershell
   python -m pytest tests/test_lab_files.py -k compile
   ```

If you get stuck, don't fix it by hand. Use the lab-state script from the repository root:

```powershell
python scripts/lab_state.py status        # which LAB STEPs are enabled
python scripts/lab_state.py upto 3.3      # enable every step up to 3.3 (catch up)
python scripts/lab_state.py reset         # back to the starter state
python scripts/lab_state.py solution      # completed reference state
```

The script copies your current files to `.lab-backup/` before it changes them. The completed reference code is in [solution/app/triage_desk](../solution/app/triage_desk).

## Conventions

- Commands are shown for **PowerShell** on Windows. On macOS or Linux, activate the virtual environment with `source .venv/bin/activate` and use `/` in paths.
- Run app commands from the `app` folder: `python -m triage_desk ...`
- Run scripts and tests from the repository root.
- **Never** paste keys, tokens, or connection strings into source files, chat prompts, or screenshots. Configuration goes in `app/.env`, which Git ignores.
- AI responses vary between runs. "Expected output" sections describe what you should see, not exact text.

## Record your values

Keep a private note (not in the repository) with the values you collect:

| Value | Collected in | Used in |
|---|---|---|
| Project endpoint | Module 1 | Modules 3, 5, 7, 9 |
| Model deployment name | Module 1 | Modules 3, 7 |
| Prompt Agent name and version | Module 1 | Module 3 |
| Search service endpoint | Module 4 | Modules 5, 7 |
| Knowledge base name | Module 4 | Modules 5, 7 |
| Project resource ID | Module 7 | Module 7 |
| Hosted agent name | Module 7 | Modules 8, 9 |

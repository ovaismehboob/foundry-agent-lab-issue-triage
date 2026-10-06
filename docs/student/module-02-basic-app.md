# Module 2 - Build and run the basic Python application

## Objective
Set up the Python environment and run the Issue Triage Assistant **without AI**. Understand the business workflow and the limits of keyword rules before you add an agent.

## Prerequisites
- Python 3.11 to 3.13, Git, and Visual Studio Code with the Python extension ([prerequisites.md](../prerequisites.md#local-tools)).
- This repository cloned or copied to your machine.

## Concepts introduced
- The triage workflow: **classify** > **prioritize** > **route** > **acknowledge**.
- Deterministic rules: keyword classification and rule-based priority.
- Separation between application logic (`rules.py`, `data_store.py`) and future AI integration (`agent_factory.py`, `ai_triage.py`).

## Starting state
Starter code. Every `LAB STEP` section is commented out. No Azure resources are needed.

## Resources used
Local only.

## Application structure

```text
app/
  data/                  synthetic issues, customers, taxonomy, routing policy (JSON)
  prompts/               agent instructions (used from Module 3)
  triage_desk/
    cli.py               commands: queue, show, triage, chat, doctor
    rules.py             Module 2: keyword classifier, priority rules, routing, acknowledgment templates
    data_store.py        loads the JSON data
    models.py            data classes and the structured output schema
    tools.py             app functions exposed to the agent (Module 3.3)
    agent_factory.py     LAB STEPs 3.1-3.4 and 5.1  <- you edit this file
    ai_triage.py         LAB STEP 3.5               <- you edit this file
    knowledge.py         Foundry IQ integration (Module 5)
    credentials.py       Azure sign-in (DefaultAzureCredential)
  main.py                hosted agent entry point (Modules 6-7)
  Dockerfile             container image (Module 6)
```

## Steps

### 2.1 Create the virtual environment
From the repository root in a VS Code terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

> The requirements pin exact versions. Two Agent Framework packages are prerelease builds; pip installs them because the exact version is pinned.

### 2.2 Run the deterministic triage
```powershell
cd app
python -m triage_desk queue
python -m triage_desk show ISS-1009
python -m triage_desk triage ISS-1009
python -m triage_desk triage ISS-1006
python -m triage_desk triage --text "I was charged twice for my recharge" --customer CUST-1003
```

### 2.3 Run the automated tests
From the repository root:

```powershell
python -m pytest
```

## Code explanation
- `rules.classify()` counts taxonomy keywords in the message and picks the category with the most matches, or `UNCLASSIFIED`.
- `rules.prioritize()` applies phrase rules: urgent phrases give P2, a business customer with an urgent phrase gives P1, degradation gives P3, information requests give P4, and repeat complainants are raised one level.
- `rules.route()` reads `data/routing_rules.json`. **Routing is policy**: in every later module, the team and SLA shown to the user still come from this function, never from the model.
- `rules.acknowledgment()` fills a template with the issue ID, team, SLA, and first steps.

## Expected output
`queue` prints a prioritized table (excerpt):

```text
PRI  ISSUE     CATEGORY           TEAM                                SLA  MESSAGE
----------------------------------------------------------------------------------------------------
P1   ISS-1002  NETWORK            Network Operations Centre (Major I   1h  Our office has 40 lines...
P1   ISS-1014  NETWORK            Network Operations Centre (Major I   1h  Our sales team of 12 pe...
P2   ISS-1001  NETWORK            Network Operations                   4h  Since 7am I have no mob...
...
P3   ISS-1009  UNCLASSIFIED       Frontline Support                   24h  Ever since I moved to m...
P3   ISS-1019  UNCLASSIFIED       Frontline Support                   24h  لا يوجد إنترنت على هاتف...
P4   ISS-1006  BILLING            Billing Operations                  72h  How do I change from Pr...
```

`python -m pytest` ends with all tests passed and two skipped (instructor-only checks).

## Verification checkpoint
Find at least three issues the rules get wrong, and say why. For example:

| Issue | Rules result | Why it's wrong |
|---|---|---|
| ISS-1009 | UNCLASSIFIED | No keyword matches "circle with a line through it" (a no-signal icon). |
| ISS-1019 | UNCLASSIFIED | The message is in Arabic. |
| ISS-1006 | BILLING | The keyword `paid` matches inside "Pre**paid**". |
| ISS-1014 | NETWORK | A roaming problem (team abroad) without the word "roaming". |
| ISS-1012 | P3, but no warning | The rules can't recognise the embedded instruction. |

## Common errors and recovery
| Symptom | Cause | Recovery |
|---|---|---|
| `No module named triage_desk` | Command run from the wrong folder | Run app commands from the `app` folder. |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | Run `Set-ExecutionPolicy -Scope Process RemoteSigned` in that terminal, then activate again. |
| pip can't download packages | Proxy or private package feed | See [troubleshooting.md](../troubleshooting.md#package-installation). |
| Arabic text shows as `?` | Old console font | Use the VS Code terminal. The app writes UTF-8. |

## Cleanup
None.

## Knowledge check
1. Which file decides the team and SLA?
2. Why can't keyword rules handle ISS-1019?
3. Which two files will you edit in Module 3?

<details><summary>Answers</summary>

1. `data/routing_rules.json`, applied by `rules.route()`.
2. The keywords are English; the message is Arabic.
3. `app/triage_desk/agent_factory.py` and `app/triage_desk/ai_triage.py`.
</details>

## References
- [Python virtual environments](https://docs.python.org/3/library/venv.html)
- [Microsoft Agent Framework overview](https://learn.microsoft.com/agent-framework/)

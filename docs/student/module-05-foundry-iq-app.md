# Module 5 - Use Foundry IQ from the Python application

## Objective
Connect the code-defined agent to the `kbtriage` knowledge base you built in Module 4, so the app can link issues to known incidents and documented solutions, and show the source references the service returns.

## Prerequisites
- Modules 3 and 4 completed (`python scripts/lab_state.py status` shows 3.1a to 3.5b enabled).
- Two roles on the search service for your user: **Search Index Data Reader** (retrieve from the knowledge base) and **Reader** (read the knowledge base definition, which the Agent Framework provider loads first). If you already have **Search Service Contributor** from Module 4, add only **Search Index Data Reader**. **API access control** on the search service must be **Both** or **Role-based access control**.
- The pinned **preview** build `azure-search-documents==12.1.0b2` (in `app/requirements.txt`). The GA 12.0.0 build rejects the **File** knowledge source kind used in Module 4 option B.

## Concepts introduced
- **Context provider**: Agent Framework component that adds information to the model context before each call.
- `AzureAISearchContextProvider` in **agentic** mode with `knowledge_base_name`: queries a Foundry IQ knowledge base.
- **Extractive data** output mode: the knowledge base returns retrieved content with references; the agent writes the answer. (Answer synthesis in the knowledge base is a preview feature and isn't used here.)

## Starting state
Module 3 complete. LAB STEP 5.1 commented out.

## Resources used
Search service and knowledge base from Module 4 (queried with your Microsoft Entra identity, no keys), model deployment.

## Steps
1. In `app/.env`, set:

   ```text
   AZURE_SEARCH_ENDPOINT=https://<your-search-service>.search.windows.net
   AZURE_SEARCH_KNOWLEDGE_BASE_NAME=kbtriage
   ```
2. Check the configuration: `python -m triage_desk doctor`. Both Module 5 lines show `OK`.
3. Run the agent **before** enabling the step and note that there's no known issue:

   ```powershell
   python -m triage_desk triage ISS-1001 --engine agent
   ```
4. In `app/triage_desk/agent_factory.py`, uncomment **LAB STEP 5.1**. Save.

   > **Reminder:** select the commented lines **between** the `===== LAB STEP 5.1 ... =====` markers (not the markers), then press **Ctrl+/** (Windows/Linux) or **Cmd+/** (macOS) to uncomment, and save.
5. Run these tests:

   ```powershell
   python -m triage_desk triage ISS-1001 --engine agent
   python -m triage_desk triage ISS-1019 --engine agent
   python -m triage_desk triage ISS-1003 --engine agent
   python -m triage_desk triage ISS-1017 --engine agent
   python -m triage_desk triage --text "Is there an outage in Old Town right now? My data has been patchy since lunch." --customer CUST-1006 --engine agent
   ```

## Prepared code
```python
if settings.knowledge_configured:
    context_providers = [build_knowledge_provider(settings, credential)]
    instructions = instructions + "\n\n" + load_instructions("knowledge_instructions.md")
```

`knowledge.py` builds the provider:

```python
CitationCapturingProvider(
    source_id="foundry_iq",
    endpoint=settings.search_endpoint,
    credential=credential,                 # your az login identity, no keys
    mode="agentic",
    knowledge_base_name=settings.knowledge_base_name,
    knowledge_base_output_mode="extractive_data",
    retrieval_reasoning_effort="minimal",
)
```

## How the application flow changes
```text
Before 5.1:  issue -> agent (instructions + tools) -> model -> structured triage
After 5.1:   issue -> agent -> [context provider: knowledge base retrieval] -> model (with retrieved content) -> structured triage
                                         |
                                         +-> references recorded for display
```
- The provider runs **before** every model call, using the recent conversation as the query.
- If the knowledge base finds nothing, the provider passes `No results found from Knowledge Base.` to the model, and the instructions require `known_issue_id` and `customer_notification` to be null.
- `CitationCapturingProvider` only records the citation annotations the service returns. It shows the document path the service returns (`metadata_storage_path`, the file name) once per document, otherwise the reference ID. If the service returns none, nothing is printed. The app never makes up a citation.
- The CLI closes the provider's network sessions when a command ends.

## Expected output (shape, validated 5 October 2026)
```text
Category      : NETWORK
Priority      : P2
Routed team   : Network Operations  (first response within 4h)
Known issue   : KI-2041
Acknowledgment:
    ...
Customer notification:
    We're aware of a mobile data outage in Harbour District since 06:50 ... Wi-Fi Calling isn't affected ...
    next update at 12:00 ...
Sources returned by Foundry IQ:
    * known-incidents-bulletin.md
    * troubleshooting-mobile-data-and-signal.md
```
- ISS-1019: `KI-2041`, with the notification in Arabic.
- ISS-1003: `KI-2043` (resolved; automatic refund within 5 business days).
- ISS-1017: `KI-2042` (CBD call drops), even though the customer ID isn't on file.
- Old Town question: `Known issue: -` and no customer notification.

Priorities can vary between runs (for example ISS-1001 is sometimes P1 because an area outage affects many customers). Discuss this variation in Module 9.

## Verification checkpoint
- [ ] At least three issues are linked to the correct known incident.
- [ ] The Old Town question has no known issue.
- [ ] Optional: `python scripts/score_triage.py --engine agent --ids EVAL-001,EVAL-003,EVAL-017,EVAL-019,EVAL-022` shows `ok` in the KI column.

## Common errors and recovery
| Symptom | Likely cause | Recovery |
|---|---|---|
| `Forbidden` from `get_knowledge_base` | Missing **Reader** on the search service | Assign **Reader** (object definitions) in addition to **Search Index Data Reader**. |
| `Knowledge source ... has kind 'file' which is not supported in this API version` | GA `azure-search-documents` installed | `pip install -r requirements-dev.txt` (pins the preview 12.1.0b2 build). |
| HTTP 403 from search | Missing **Search Index Data Reader**, or API access control set to keys only | Assign the role (wait a few minutes) and set API access control to **Both**. |
| HTTP 404 for the knowledge base | Wrong `AZURE_SEARCH_KNOWLEDGE_BASE_NAME` | Copy the name from **Build** > **Knowledge**. |
| Error mentioning the model used by the knowledge base | The search service can't call the chat model configured in the knowledge base | The search service's managed identity needs **Cognitive Services User** on the Foundry resource (see [instructor-guide.md](../instructor-guide.md#role-checklist)). |
| Result falls back to rules | Any of the above, caught by Exercise 3.5 | Run with `--verbose` to see the error. |

## Cleanup
None.

## Knowledge check
1. When does the context provider run?
2. What happens when the knowledge base finds nothing?
3. Where do the displayed sources come from?

<details><summary>Answers</summary>

1. Before every model call.
2. The model receives "No results found from Knowledge Base." and must not set a known issue.
3. The citation annotations in the knowledge base response; the app only displays them.
</details>

## References
- [Azure AI Search context provider (Agent Framework)](https://learn.microsoft.com/agent-framework/integrations/by-component/context-providers/azure-ai-search)
- [Connect agents to Foundry IQ knowledge bases](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
- [What is Foundry IQ?](https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-foundry-iq)

> **Documentation gap:** The Agent Framework documentation shows how to configure the provider but doesn't document the citation fields returned for each knowledge source kind, or that the provider reads the knowledge base definition (which needs the **Reader** role). Both were observed in validation and are handled above.

# Images and screenshots

Store lab screenshots in this folder with the naming convention `m<module>-<short-description>.png` (for example `m04-knowledge-base.png`). Reference them from Markdown with relative paths, for example `![alt text](../images/m04-knowledge-base.png)` written inside a page in `docs/student/`.

## Rules for screenshots
- Prefer current official Microsoft images; link to them with their source instead of copying them.
- Capture from the lab subscription only when no suitable official image exists.
- Before adding a screenshot, crop or mask: subscription and tenant IDs, user names and emails, keys, tokens, connection strings, resource IDs, private endpoints, unrelated resources, notifications, browser profile, other tabs, and account menus. Non-sensitive names of lab resources may stay visible.
- Never fabricate or edit portal images to show UI that doesn't exist.
- Keep images readable (at least 1200 px wide for full-page captures); add a caption, alt text, and "what to observe".

## Official images referenced (not copied)

| Figure | Image | Source | License / terms |
|---|---|---|---|
| 1.1 | Foundry project home page | [Microsoft Learning - mslearn-agent-quickstart](https://github.com/MicrosoftLearning/mslearn-agent-quickstart) `Instructions/Labs/media/foundry-portal-home.png` | MIT (repository license) |
| 1.2 | Model catalog | same repository, `0-foundry-models.png` | MIT |
| 1.3 | Agent playground | same repository, `agent-playground.png` | MIT |
| 8.3 | Agent Monitoring Dashboard | Microsoft Learn, *Monitor agents with the Agent Monitoring Dashboard* | Microsoft Learn terms of use |

## Screenshots captured from the lab tenant (5 October 2026)

Captured from a dedicated lab project (`proj-triage-lab`) in the Microsoft Non-Production tenant. They show only lab resource names; no subscription or tenant IDs, user names, keys, or account menus are visible. They were checked before they were added.

| File | Figure | Screen |
|---|---|---|
| `m04-file-knowledge-source.png` | 4.1 | Create a knowledge source - File (Preview) |
| `m04-knowledge-base.png` | 4.2 | Saved knowledge base `kb-triage` |
| `m04-grounded-response.png` | 4.3 | Grounded answer for ISS-1001 with citations |
| `m08-guardrail-controls.png` | 8.1 | Guardrail wizard, step 1: Add controls |
| `m08-trace-detail.png` | 8.2 | Trace detail with the knowledge base tool span |

## Screenshots still to capture (placeholders in the guide)

| File | Module | Screen | Navigation |
|---|---|---|---|
| `m09-evaluation-results.png` | 9 | Evaluation run results | Build > Agents > issue-triage-agent > Evaluation > select the run |

The placeholder in the student guide lists what must be visible, what to redact, the caption, and the alt text. When you add the screenshot, replace the placeholder block with the image, caption, and "what to observe" text.
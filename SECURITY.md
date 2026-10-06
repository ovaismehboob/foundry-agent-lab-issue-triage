# Security

This repository is training material. It uses only synthetic data and must not be used with real customer data without a security and privacy review.

## Secrets and configuration
- No keys, tokens, connection strings, subscription IDs, or tenant IDs are stored in the repository.
- Local configuration goes in `app/.env` (copied from `app/.env.example`). It's excluded by `.gitignore` and `.dockerignore`.
- `app/.env.container` (Module 6) contains short-lived access tokens for local container testing only. It's excluded from Git and the image. Delete it after use.
- `.azure/` (created by `azd`) is excluded from Git.
- `tests/test_repo_hygiene.py` checks that common secret patterns aren't committed.

## Identity
- Local runs use `DefaultAzureCredential` with your `az login` session (keyless).
- Hosted agents use the platform-created Microsoft Entra agent identity. Grant it only the roles it needs (Module 7.7).
- Role assignments follow least privilege and are scoped to lab resources only (see [docs/prerequisites.md](docs/prerequisites.md#roles)).

## Application controls
- Ticket text is treated as data; the instructions tell the agent to ignore embedded instructions and flag them.
- Tools are read-only. Routing is always taken from the routing policy, not from the model.
- Input is validated before it's sent to a model; failures fall back to the rules engine.
- Citations are shown only when the knowledge service returns them.

## Limits
Guardrails and instructions reduce specific risks; they don't prevent every attack. See [docs/student/module-08-control-plane.md](docs/student/module-08-control-plane.md).

## Reporting
For issues with this lab content, contact the lab owner (placeholder: `<lab-owner-contact>`). For vulnerabilities in Microsoft products, follow the [Microsoft Security Response Center](https://msrc.microsoft.com/) process.

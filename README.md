# Breezy Lynne — Systems, Identity & Automation

[![Portfolio CI](https://github.com/skrrtvonnegut-droid/portfolio/actions/workflows/portfolio.yml/badge.svg)](https://github.com/skrrtvonnegut-droid/portfolio/actions/workflows/portfolio.yml)

A living professional portfolio focused on Microsoft 365 administration, identity governance, endpoint management, automation, operational resilience, and technical knowledge design.

I work where systems, people, and process collide: reducing repetitive administration, making access and ownership visible, designing safer change paths, and converting tribal knowledge into operations that can survive handoffs, incidents, and growth.

> [!IMPORTANT]
> This repository is a **published evidence layer**, not a dump of workplace documents or private conversations. Every artifact is reconstructed, generalized, and checked for confidentiality before publication.

## What this portfolio demonstrates

- **Identity and access governance:** least privilege, privileged-role workflows, lifecycle controls, ownership, and auditability.
- **Endpoint engineering:** staged deployment, update-ring design, enrollment, observability, rollback, and operational handoff.
- **Automation:** PowerShell, Microsoft Graph, repeatable reporting, and replacing fragile manual work with governed systems.
- **Service management:** incident learning, change controls, dependency mapping, problem prevention, and documentation quality.
- **Knowledge systems:** design documents, SOPs, runbooks, KB articles, templates, and AI-assisted authoring with human review.

## Featured open-source work

| Project | What it shows |
| --- | --- |
| [Microsoft 365 License Report](https://github.com/skrrtvonnegut-droid/M365LicenseReport) | PowerShell and Microsoft Graph reporting for license assignment, usage, cost analysis, and governance. |
| [Prompt Library](https://github.com/skrrtvonnegut-droid/prompt-library) | A versioned registry of prompts, skills, macros, schemas, validation, and CI for reusable AI-assisted workflows. |
| [The People’s Grimoire](https://github.com/skrrtvonnegut-droid/the-peoples-grimoire) | Open-source architecture for user-owned, policy-governed coordination across SaaS tools. |

## Initial artifact collection

| Domain | Artifact |
| --- | --- |
| Identity governance | [Privileged Role Activation with Microsoft Entra PIM](artifacts/identity-governance/privileged-role-activation.md) |
| Endpoint management | [Staged Windows Update Rollout](artifacts/endpoint-management/staged-windows-update-rollout.md) |
| Identity governance | [Service Account Registry and Review System](artifacts/governance/service-account-registry.md) |
| Service management | [Mail-Flow Change After-Action Review](artifacts/service-management/mail-flow-change-after-action.md) |
| Knowledge management | [Operational Documentation System](artifacts/knowledge-management/operational-documentation-system.md) |

These are not verbatim employer procedures. They preserve the transferable problem-solving pattern—context, decisions, controls, trade-offs, validation, and outcomes—while omitting organization-specific implementation details.

## How the living pipeline works

```mermaid
flowchart LR
    A[Study, project, or professional conversation] --> B[Private candidate discovery]
    B --> C{Durable professional evidence?}
    C -->|No| D[Remain private or ephemeral]
    C -->|Yes| E[Reconstruct and sanitize]
    E --> F[Draft pull request]
    F --> G[Schema, link, privacy, and build checks]
    G --> H{Human review}
    H -->|Revise| E
    H -->|Approve| I[Merge to main]
    I --> J[Catalog and GitHub Pages deployment]
```

The discovery step can happen naturally during active ChatGPT work. Publication is intentionally review-gated: no automation may copy raw Notion pages, chat history, tickets, screenshots, or internal configuration into this public repository.

Read the full [Publishing and Artifact Standard](docs/PUBLISHING.md).

## Add an artifact

1. Start from [the artifact template](templates/ARTIFACT_TEMPLATE.md) or open a **Portfolio candidate** issue.
2. Place the Markdown file under `artifacts/<domain>/`.
3. Complete the YAML metadata block.
4. Run the same checks used by CI:

   ```bash
   python -m pip install -r requirements.txt
   python scripts/portfolio.py validate
   python -m unittest discover -s tests
   python scripts/portfolio.py build --output _site
   ```

5. Open a draft pull request. Merge only after the privacy and source-rights checklist passes.

## Repository structure

```text
portfolio/
├── artifacts/                 # Sanitized professional evidence
├── docs/PUBLISHING.md         # Promotion, privacy, and metadata contract
├── templates/                 # Reusable artifact scaffolding
├── schema/                    # Machine-readable metadata validation
├── scripts/                   # Validation, scanning, catalog, and site build
├── tests/                     # Pipeline tests
├── portfolio.yml              # Profile and featured-project manifest
└── .github/                   # CI/CD, issue intake, and PR controls
```

## Privacy boundary

Do not commit employer names, non-public people, email addresses, internal domains, tenant identifiers, server names, private links, IP addresses, ticket numbers, exact security configuration, customer or user data, credentials, certificates, screenshots of administrative portals, or copied proprietary documentation.

Removing names is not enough. A safe portfolio artifact is a **new generalized work** that teaches the system pattern without exposing the system it came from.

See [SECURITY.md](SECURITY.md) for reporting and response guidance.

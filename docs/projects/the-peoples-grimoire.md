---
id: portfolio.project-card.the-peoples-grimoire
title: The People’s Grimoire
summary: An open-source architecture for user-owned coordination across SaaS tools using connector contracts, policy-governed actions, reversible plans, explicit provenance, and human authority.
artifact_type: project-card
domains:
  - ai-llm
  - automation
  - operations
  - documentation
status: active
classification: professional-portfolio
source_disclosure: Derived only from the intentionally public the-peoples-grimoire repository; private deployment overlays, mappings, credentials, and personal topology are not included.
skills:
  - Systems architecture
  - Connector design
  - Policy and trust modeling
  - Privacy engineering
  - Technical writing
created: 2026-08-15
updated: 2026-08-15
---

# The People’s Grimoire

> **Portfolio note:** This project card describes the public architecture and current scaffold. Private deployments, personal source mappings, credentials, and operator-specific topology are intentionally outside the portfolio and the public repository.

## Why it exists

Modern SaaS tools are individually capable but collectively fragmented. Documents, code, tasks, conversations, and decisions often live in systems that each understand only their own data model. Connecting them usually means brittle point-to-point automations, duplicated records, or handing another platform broad custody over the whole environment.

The People’s Grimoire explores a different model: a user-owned coordination layer where applications remain distinct carriers, but can participate in shared resource, event, policy, and provenance contracts.

The project is intentionally pre-alpha. Its current value is architectural and experimental rather than a claim of production-ready universal synchronization.

## Architectural model

The public design treats:

- **Connectors** as adapters between provider-specific APIs and shared contracts.
- **Canonical resources and events** as a common language for describing changes without pretending every system is identical.
- **Policies and permissions** as boundaries around what may be proposed or executed.
- **Approval gates** as explicit human authority for consequential actions.
- **An audit ledger** as memory for plans, actions, and outcomes.
- **Recipes** as reusable coordination patterns rather than invisible background magic.

GitHub and Notion are the first carrier pair, but the semantic roles are designed to remain stable if compatible providers are added or replaced.

## Trust substrate

A central design concern is preventing orchestration from quietly widening authority.

Connector manifests declare the actions, resource types, protocol compatibility, and permissions a connector supports. The active credential must satisfy those declarations, and a recipe cannot expand the connector’s authority beyond them. Unsupported actions or missing scopes fail before execution.

The public runtime also demonstrates content-minimizing observability: secrets are redacted, private identifiers can be represented by keyed fingerprints, unknown payload fields are omitted, and diagnostic information is separated from raw exception content.

These controls are intended to make the system inspectable without turning logs into another source of private data leakage.

## Plan before apply

The reference runtime separates planning from execution. It can produce proposed actions and dry-run output without contacting a production SaaS API, while approved execution in the public demo is limited to an in-memory recording connector.

That boundary keeps the architecture honest about its current maturity while establishing several principles that would matter in a real connector implementation:

- deterministic action identity;
- explicit proposed actions;
- per-action approval;
- connector capability enforcement;
- append-only audit history;
- reversible or reviewable plans before consequential writes.

## Conversational bootstrap

The project also includes a provider-neutral bootstrap protocol for discovering an operator’s approved information ecology and proposing a private control plane around it.

The installer is intentionally history-shaped rather than taxonomy-first. It examines only sources the operator approves, looks for recurring domains and canonical objects, then produces a reviewable plan before durable writes occur.

A chatbot is therefore an interface to the protocol, not the canonical owner of the resulting system.

## Public commons, private instance

One of the project’s strongest architectural boundaries is the distinction between reusable public infrastructure and private deployment state.

The public repository may contain:

- schemas and protocols;
- connector contracts;
- reference runtime code;
- bootstrap structures;
- sanitized fixtures;
- governance and architecture documentation.

A real instance keeps its topology, identity mappings, private configuration, source inventories, and credentials elsewhere. The project explicitly rejects using Git—even a private repository—as a secret store.

## Current maturity

The repository describes itself as **pre-alpha**, and the portfolio preserves that characterization. The reference runtime demonstrates contracts, planning, approval, capability enforcement, and safe observability with synthetic or in-memory behavior. It does not currently claim live production clients for universal SaaS synchronization.

That limitation is part of the design record rather than something to hide: the project has working bones and trust rules, while provider breadth and production execution remain future work.

## What this demonstrates

- Designing interoperability around contracts rather than tightly coupled point-to-point automations
- Separating public protocols from private deployment state
- Capability-based permission and trust modeling
- Human approval, reversibility, provenance, and auditability as architectural concerns
- Privacy-preserving observability and content minimization
- Distinguishing implemented scaffold from roadmap in an ambitious open-source system

## Canonical repository

Read the current architecture, bootstrap protocol, connector capability contract, privacy model, roadmap, and reference runtime in [The People’s Grimoire](https://github.com/skrrtvonnegut-droid/the-peoples-grimoire).

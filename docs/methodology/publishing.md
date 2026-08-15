# Publishing and Artifact Standard

## Purpose

This repository turns ongoing study, projects, and professional problem-solving into a durable body of public evidence without turning private systems into content.

The portfolio pipeline has two distinct jobs:

1. **Accumulate evidence** from active work and learning.
2. **Prevent accidental disclosure** while transforming that evidence into something useful to a public reader.

The second job outranks the first.

## Canonical boundary

| Layer | Role | Allowed content |
| --- | --- | --- |
| ChatGPT | Exploration, synthesis, drafting, and routing | Working context; may include private source material when authorized |
| Notion | Private candidate register, source links, review notes, and living professional memory | Private and employer-confidential context under the user’s control |
| Public GitHub | Versioned professional evidence and reusable public artifacts | Public or intentionally sanitized Professional Portfolio material only |

A public artifact may be inspired by a private source, but the source does not become public. The portfolio stores the reconstructed result, not the raw record.

## Promotion lifecycle

### 1. Discover

At the end of a substantive technical conversation, project, lab, incident review, or documentation effort, assess whether it demonstrates a durable capability:

- a meaningful problem and constraint;
- a design or diagnostic method;
- a reusable control, workflow, or automation;
- a trade-off or failure mode worth explaining;
- a validated outcome or lesson.

Routine task logs and private journaling are not portfolio artifacts.

### 2. Register privately

Create or update a candidate in the private portfolio register with:

- working title;
- source type and private source link;
- capability demonstrated;
- likely artifact type;
- sensitivity and source-rights concerns;
- sanitization plan;
- target public path;
- lifecycle state.

The candidate record may contain private references. It must remain outside this repository.

### 3. Reconstruct

Do not perform shallow find-and-replace redaction. Write a new artifact around the transferable pattern:

- **Preserve:** context, decisions, controls, trade-offs, validation, outcomes, and lessons.
- **Generalize:** organization, scale, topology, naming, dates, values, vendors, and implementation-specific configuration.
- **Remove:** identities, private links, secrets, exact system details, sensitive screenshots, raw logs, and proprietary text.
- **Re-evaluate:** whether the remaining combination of facts could still identify or expose the source environment.

When a source cannot be made safe without destroying its meaning, reject it as a public candidate.

### 4. Draft by pull request

Create a branch and draft pull request. The PR should explain:

- what capability the artifact demonstrates;
- how it was reconstructed;
- what categories of source detail were removed or generalized;
- whether external sources or adapted code require attribution;
- any remaining uncertainty.

### 5. Validate

CI enforces:

- valid YAML metadata against `schema/artifact.schema.json`;
- stable and unique artifact IDs;
- valid relative links;
- minimum content quality checks;
- generic secret and private-infrastructure scanning;
- optional repository-specific denylist scanning through the `PORTFOLIO_DENYLIST` secret;
- successful Zensical site and catalog generation;
- unit tests.

CI reduces risk; it does not replace human judgment.

### 6. Review and publish

A reviewer checks both technical quality and disclosure risk. Merge to `main` publishes the artifact and triggers the Pages build.

## Automation levels

| Level | State | Automation boundary |
| --- | --- | --- |
| 0 | Raw source | Never copied into public GitHub |
| 1 | Private candidate | May be detected and registered during an active ChatGPT session |
| 2 | Sanitized draft | May be generated automatically when the transformation is high confidence |
| 3 | Draft PR | CI runs automatically; human review remains required |
| 4 | Published | Merge updates the catalog and site automatically |

This is **automatic discovery with review-gated publication**, not blind synchronization.

## Sanitization checklist

Before opening a PR, confirm the artifact contains none of the following unless the information is already intentionally public and necessary:

- employer, customer, employee, vendor-contact, or non-public project names;
- email addresses, phone numbers, usernames, account names, or personal identifiers;
- tenant, subscription, application, device, object, certificate, or secret identifiers;
- internal domains, hostnames, network ranges, IP addresses, file shares, or topology;
- private Notion, SharePoint, ticketing, monitoring, or administrative portal links;
- ticket numbers, incident IDs, exact timestamps, or operational breadcrumbs;
- exact group, policy, role-assignment, or configuration names from a private environment;
- screenshots, logs, message traces, exports, or sample data from production;
- passwords, tokens, secrets, private keys, recovery material, or credential files;
- copyrighted or proprietary text copied from internal or licensed sources;
- metrics whose combination could identify the organization or reveal its posture.

Then ask a harder question: **Could a knowledgeable coworker reconstruct the source environment from what remains?**

## What good sanitization preserves

A strong artifact still answers:

- What problem existed?
- Why did it matter operationally?
- What constraints shaped the solution?
- What options were considered?
- What was implemented or proposed?
- How was success or failure validated?
- What risks and trade-offs remained?
- What would be done differently next time?

An artifact that says only “I improved security” is safe but useless. An artifact that reproduces production configuration is useful but unsafe. The portfolio belongs in the disciplined middle.

## Artifact metadata contract

Every file under `docs/artifacts/` begins with YAML front matter:

```yaml
---
id: portfolio.identity.example
title: Example Artifact
summary: One sentence describing the problem and professional capability.
artifact_type: case-study
domains:
  - identity-governance
status: active
classification: professional-portfolio
source_disclosure: Reconstructed from professional experience; no employer-specific configuration is included.
skills:
  - Microsoft Entra ID
created: 2026-08-15
updated: 2026-08-15
---
```


### Stable identity

Artifact IDs remain stable across title and path changes. Use:

```text
portfolio.<domain>.<slug>
```

### Allowed lifecycle states

- `draft` — still being shaped or reviewed;
- `active` — current and intentionally published;
- `review-due` — likely useful but needs technical or privacy review;
- `superseded` — replaced by a named successor;
- `archived` — retained for history but no longer active.

### Source disclosure

The public metadata describes the **kind** of source, not the private source location. Examples:

- “Reconstructed from professional experience.”
- “Derived from a personal lab using synthetic data.”
- “Adapted from a public project; attribution is provided below.”

Never put a private Notion URL or internal ticket link in public metadata.

## Recommended artifact shapes

### Case study

Use for a project, incident, migration, governance improvement, or operational redesign.

Required narrative: context, constraints, approach, controls, validation, outcome, trade-offs, and demonstrated capability.

### Runbook or SOP pattern

Use when the procedural design itself demonstrates skill. Keep values and identifiers parameterized; include prerequisites, safety controls, validation, rollback, escalation, and review cadence.

### Automation project

Include problem, architecture, authentication model, least-privilege requirements, input/output contract, failure handling, tests, operational notes, provenance, and limitations. Use synthetic fixtures only.

### Learning note

Publish only when the note contains original synthesis, tested examples, or a durable model—not a lightly paraphrased copy of course or vendor material.

## Pull-request review questions

1. Is this original, licensed, or properly attributed?
2. Is the classification truly Public or Professional Portfolio?
3. Was the source reconstructed rather than merely renamed?
4. Does the artifact demonstrate a capability a reader can understand?
5. Are claims proportional to the available evidence?
6. Are current product behavior and role permissions clearly marked for verification where they may change?
7. Does CI pass with the repository denylist enabled?
8. Would publication create risk for another person or organization?

A “no” or “uncertain” answer blocks publication until resolved.

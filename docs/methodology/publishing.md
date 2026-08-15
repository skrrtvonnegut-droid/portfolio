# Publishing and Artifact Standard

## Purpose

This repository turns ongoing study, projects, and professional problem-solving into durable public evidence without turning private systems into content.

The portfolio pipeline has two jobs:

1. **Accumulate evidence** from active work and learning.
2. **Prevent accidental disclosure** while transforming that evidence into something useful to a public reader.

The second job outranks the first.

## Canonical boundary

| Layer | Role | Allowed content |
| --- | --- | --- |
| ChatGPT | Exploration, synthesis, drafting, and routing | Working context; may include private source material when authorized |
| Notion | Private candidate register, source links, approval state, sanitization notes, and living professional memory | Private and employer-confidential context under the user’s control |
| Public GitHub | Versioned professional evidence, validation code, and reusable public artifacts | Public or intentionally reconstructed Professional Portfolio material only |

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

Create or update a private candidate with:

- working title and stable artifact ID;
- source type and private source references;
- capability demonstrated;
- likely public form;
- classification, provenance, rights, and sanitization risk;
- target public path;
- lifecycle and approval state.

The private candidate may contain source links and sensitive context. It must remain outside this repository.

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

A draft exists as branch and review state. Public artifact metadata does not use `draft`, because content merged to the public repository is already public.

### 5. Validate

CI enforces:

- merged artifact metadata against `schema/artifact.schema.json`;
- stable and unique artifact IDs and public slugs;
- explicit provenance, authorship, publication rights, and review dates;
- valid relative links and strict Zensical rendering;
- minimum content-quality checks;
- generic secret and private-infrastructure scanning;
- repository-specific denylist scanning through the private `PORTFOLIO_DENYLIST` secret;
- Gitleaks history and secret scanning;
- external link health with transient failures treated conservatively;
- Python linting, unit tests, and machine-readable catalog generation.

CI reduces risk; it does not replace human judgment.

### 6. Review and publish

A human checks technical quality, evidence, authorship, rights, and disclosure risk. Merge to `main` is the only event that can publish through GitHub Pages.

## Automation levels

| Level | State | Automation boundary |
| --- | --- | --- |
| 0 | Raw source | Never copied into public GitHub |
| 1 | Private candidate | May be detected and registered during active ChatGPT work |
| 2 | Sanitized draft | May be reconstructed when the transformation is sufficiently grounded |
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

Then ask the harder question: **Could a knowledgeable coworker reconstruct the source environment from what remains?**

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

## Public metadata contract

The public contract is intentionally split into two parts.

### Narrative front matter

Every file under `docs/artifacts/` begins with content metadata:

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
source_disclosure: Reconstructed from professional experience; no private implementation details are included.
skills:
  - Microsoft Entra ID
created: 2026-08-15
updated: 2026-08-15
---
```

### Governance register

`portfolio.yml` contains the corresponding public governance record:

```yaml
artifacts:
  - id: portfolio.identity.example
    slug: /artifacts/identity-governance/example/
    provenance: ai-assisted-original
    authorship: breezy-lynne
    rights:
      publishable: true
      attribution: null
      source_url: null
    review:
      last_reviewed: 2026-08-15
      review_due: 2027-02-15
    featured: false
```

The validator merges the two records by stable ID and rejects missing, duplicate, conflicting, or orphaned entries. This keeps narrative metadata beside the document while making provenance, rights, review, and presentation state maintainable as one auditable public register.

Private source URLs, candidate approval state, and sanitization working notes never enter either public record.

### Stable identity and slug

Artifact IDs remain stable across title and path changes. Use:

```text
portfolio.<domain>.<slug>
```

A slug must match the rendered path. A move therefore requires an intentional governance update and link review rather than silently creating a second identity.

### Provenance

- `original` — authored from the maintainer’s own analysis or implementation;
- `ai-assisted-original` — original work materially structured, drafted, or edited with AI assistance;
- `adapted` — transformed from an attributed external source;
- `external-reference` — included for orientation and never presented as original work.

Adapted and external-reference artifacts require public attribution and a public source URL. Original and AI-assisted-original artifacts keep those fields null.

### Public lifecycle states

- `active` — current and intentionally published;
- `review-due` — still public, but technical or privacy review is overdue;
- `superseded` — replaced by a successor;
- `archived` — retained for history but no longer current.

Branch and PR state represent unpublished drafts. This prevents a `draft` label from creating the illusion that material already merged to a public repository is still private.

### Review dates

Every artifact declares when it was last reviewed and when review is due. CI rejects impossible chronology, while monthly maintenance opens or updates an issue when an active artifact becomes overdue. Automation raises the obligation; it does not silently rewrite the artifact.

### Source disclosure

Public metadata describes the **kind** of source, not the private source location. Examples:

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

## Maintenance and drift

Maintenance runs monthly and checks:

- overdue review dates;
- broken public links;
- schema and repository validity;
- current project references.

A failed maintenance check opens or updates an issue. Authored content changes only through a reviewed pull request.

Event-triggered review is also required when:

- a platform, policy, owner, or architecture changes;
- an artifact fails during use;
- an incident reveals a missing dependency;
- a product interface or authentication model changes;
- a workaround becomes permanent;
- a linked artifact is superseded;
- the intended audience changes.

## Pull-request review questions

1. Is this original, licensed, or properly attributed?
2. Is the classification truly Professional Portfolio?
3. Was the source reconstructed rather than merely renamed?
4. Does the artifact demonstrate a capability a reader can understand?
5. Are claims proportional to the available evidence?
6. Are current product behavior and role permissions clearly marked for verification where they may change?
7. Do provenance, authorship, rights, and review metadata agree with the artifact?
8. Does CI pass with the private repository denylist enabled?
9. Would publication create risk for another person or organization?

A “no” or “uncertain” answer blocks publication until resolved.

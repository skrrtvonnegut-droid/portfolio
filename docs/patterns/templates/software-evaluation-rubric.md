---
id: portfolio.template.operations.software-evaluation-rubric
slug: /patterns/templates/software-evaluation-rubric/
kind: template
title: Software Evaluation and Intake Rubric
summary: A reusable intake and decision framework for assessing software requests across user value, identity, data, integration, security, support, cost, and lifecycle ownership.
status: published
classification: professional-portfolio
provenance: ai-assisted-original
authorship: breezy-lynne
domains:
  - operations
  - security
  - documentation
skills:
  - requirements-analysis
  - risk-modeling
  - governance
  - technical-writing
rights:
  publishable: true
  attribution: null
  source_url: null
review:
  last_reviewed: "2026-08-16"
  review_due: "2027-02-15"
featured: false
---

# Software Evaluation and Intake Rubric

> **Portfolio note:** This is a generalized software-intake framework built from professional practice and AI-assisted drafting. It contains no real request, organization-specific thresholds, internal approval chain, pricing, vendor relationship, or production configuration.

## Purpose

Software requests are rarely just questions about whether a product has a useful feature. A tool can solve the immediate user problem while introducing identity sprawl, unmanaged data flows, duplicate capability, unclear ownership, unexpected cost, inaccessible workflows, or a support burden that outlives the original requester.

This rubric creates a repeatable way to evaluate a request without pretending every decision can be reduced to a score. It is designed to make the important questions visible, separate evidence from assumptions, and produce an explicit outcome with an owner and a review path.

The intended result is a decision record that can answer:

- What problem are we trying to solve?
- Who benefits, and how will we know the tool is useful?
- What data, identities, integrations, and privileges does it introduce?
- Who will own administration, support, cost, renewal, and eventual retirement?
- What existing capability does it overlap or replace?
- What risks remain after controls are applied?
- Is the appropriate outcome approval, conditional approval, pilot, deferral, rejection, or retirement?

## Use when

Use this rubric when a request would introduce or materially change a software service, SaaS application, browser extension, endpoint application, integration, AI service, or other externally maintained capability.

A lightweight path may be enough when a request is already covered by an approved standard, adds no meaningful data or identity exposure, and has a clear owner. A deeper review is appropriate when the software processes sensitive information, creates privileged access, integrates with core systems, requires broad endpoint deployment, creates a material recurring cost, or becomes difficult to reverse.

## Decision principles

### Start with the problem, not the product

The requester may arrive with a named tool because it is the first visible solution. The intake should preserve the underlying need separately from the proposed product.

A useful problem statement describes:

- the current friction or unmet capability;
- the people or process affected;
- the consequence of doing nothing;
- the desired outcome;
- any time, regulatory, operational, or accessibility constraint.

This keeps the review open to existing capabilities, process changes, automation, or a different product when those options solve the same problem with less complexity.

### Treat ownership as part of the design

Every approved tool creates a lifecycle. Someone must be able to answer who owns:

- the business need;
- technical administration;
- access decisions;
- data handling;
- support and escalation;
- licensing and renewal;
- vendor communication;
- periodic review;
- offboarding and retirement.

A tool with no durable owner is not free simply because the license price is low.

### Separate evidence from assumptions

For each major claim, record whether it is:

- verified through documentation or testing;
- stated by the vendor;
- inferred from architecture or experience;
- unknown and requiring follow-up.

Unknowns are not automatically blockers, but they should remain visible rather than being converted into optimistic prose.

### Prefer reversible decisions

A pilot with bounded users, limited data, defined success criteria, and an exit plan is often safer than organization-wide deployment based on a feature demo.

The evaluation should identify what makes the decision difficult to reverse: data export limitations, proprietary formats, identity dependencies, workflow lock-in, custom integration, contractual terms, or user retraining.

## Required inputs

| Input | Why it matters |
| --- | --- |
| Problem statement | Preserves the underlying need separately from the proposed tool |
| Requester and business owner | Establishes who can validate value and accept trade-offs |
| Intended users | Defines scope, support, accessibility, and licensing needs |
| Data involved | Drives privacy, retention, classification, and integration review |
| Identity model | Shows how authentication, provisioning, privilege, and offboarding work |
| Integrations | Surfaces dependencies, credentials, APIs, and failure paths |
| Deployment model | Identifies endpoint, browser, mobile, or cloud operational impact |
| Licensing and cost model | Makes recurring cost, growth, and renewal visible |
| Support model | Defines who handles user issues and vendor escalation |
| Alternatives considered | Prevents unnecessary duplication and records the decision context |
| Exit strategy | Tests whether the organization can recover data and retire the tool |
| Review date | Prevents approval from becoming permanent by omission |

## Assessment template

### 1. Use case and expected value

**Problem to solve:**  
Describe the current problem without naming the proposed product.

**Desired outcome:**  
What observable improvement should exist if the request succeeds?

**Affected users or process:**  
Who benefits, and who may be disrupted?

**Urgency:**  
What creates the deadline, and what happens if the decision is delayed?

**Success evidence:**  
How will value be evaluated after a pilot or implementation?

### 2. Existing capability and duplication

- Is the need already met by an approved platform or licensed feature?
- Could configuration, training, process change, or automation solve the problem?
- Would this tool replace an existing service or become another parallel option?
- If it duplicates capability, what specific gap justifies the duplication?
- What becomes eligible for retirement if this product is adopted?

**Finding:**  
`No overlap | Complementary | Partial duplication | Significant duplication | Unknown`

### 3. Identity and access

Document:

- authentication method;
- single sign-on support;
- provisioning and deprovisioning method;
- group or role model;
- privileged administrative roles;
- guest or external-user behavior;
- service or application identities;
- multi-factor authentication dependencies;
- auditability of access changes.

Questions:

- Can access follow the existing identity lifecycle?
- Can privileged access be separated from ordinary use?
- Can inactive or departed users be removed reliably?
- Does the product require shared credentials or long-lived secrets?
- Can access be reviewed periodically?

**Finding:**  
`Aligned | Acceptable with controls | Material gap | Unknown`

### 4. Data and privacy

Identify:

- data classes processed or stored;
- geographic or residency constraints;
- retention and deletion behavior;
- export capability;
- encryption expectations;
- telemetry or training use;
- subprocessors where relevant;
- user-generated content and ownership;
- backup and recovery expectations.

Questions:

- Does the software need the data it requests?
- Can scope be reduced?
- Is data reused for purposes beyond delivering the service?
- Can data be exported in a usable form?
- Can the organization delete its data at termination?
- Is the proposed use appropriate for the data classification?

**Finding:**  
`Low exposure | Managed exposure | Elevated exposure | Unacceptable | Unknown`

### 5. Security and technical risk

Review the controls proportionate to the request:

- authentication and authorization;
- administrative privilege;
- vulnerability and patch responsibility;
- endpoint permissions;
- integration credentials;
- logging and audit events;
- incident notification;
- vendor security posture;
- dependency and availability risk;
- browser, plugin, script, or agent behavior.

Do not treat a vendor questionnaire as proof of safety. Record what has actually been verified and what remains vendor-asserted.

**Finding:**  
`Acceptable | Acceptable with conditions | Needs remediation | Blocked pending evidence`

### 6. Integration and architecture

For each integration, record:

| Dependency | Direction | Data or action | Authentication | Owner | Failure impact |
| --- | --- | --- | --- | --- | --- |
| Synthetic system | Outbound | Example metadata | OAuth application | Platform owner | Workflow pauses |

Questions:

- Is an integration truly required for the initial use case?
- What permissions does it need?
- What happens when either side is unavailable?
- Who owns credential rotation or application consent?
- Is the dependency monitored?
- Does the integration create a hidden production-critical path?

### 7. Deployment and endpoint impact

When software reaches managed devices, assess:

- installation method;
- update mechanism;
- required permissions;
- supported operating systems;
- background services or agents;
- browser extensions;
- network requirements;
- compatibility dependencies;
- uninstall behavior;
- pilot and rollback path.

A technically installable application is not necessarily operationally supportable at scale.

### 8. Support and service ownership

Define:

- business owner;
- technical owner;
- first-line support path;
- escalation path;
- vendor-support entitlement;
- expected support hours;
- documentation requirements;
- known maintenance tasks;
- monitoring expectations;
- continuity plan if the primary administrator leaves.

**Finding:**  
`Owned | Ownership incomplete | Unsupported`

### 9. Cost and licensing

Record:

- pricing model;
- minimum commitment;
- expected starting scope;
- growth drivers;
- renewal timing;
- implementation or integration cost;
- premium features required for governance;
- overlap with existing licensed capability;
- exit or data-egress cost.

Cost should be evaluated across the lifecycle, not only against the first invoice.

### 10. Accessibility and user experience

Assess whether the tool can be used by the intended audience without creating avoidable barriers.

Consider:

- keyboard navigation;
- screen-reader compatibility;
- contrast and visual requirements;
- captioning or transcript support;
- mobile or remote-work requirements;
- language needs;
- training burden;
- workflow complexity.

Accessibility is part of service quality, not an optional polish step after approval.

### 11. Lifecycle and exit

Before approval, answer:

- Who reviews continued need?
- What event triggers a review?
- What data must be exported before termination?
- How are accounts and integrations removed?
- What configuration or documentation must be retained?
- Is there a replacement or rollback path?
- What would make the tool no longer worth operating?

Define a review date even for a successful implementation.

## Decision record

### Recommended outcome

Choose one:

- **Approve** — evidence is sufficient and the service has clear ownership and acceptable residual risk.
- **Approve with conditions** — approval depends on explicit controls, remediation, or scope limits.
- **Pilot** — value or risk requires bounded testing before a broader commitment.
- **Defer** — the need may be valid, but evidence, ownership, funding, or dependencies are incomplete.
- **Reject** — the request does not justify the cost, duplication, risk, or operational burden.
- **Retire existing capability** — adoption is approved with an explicit plan to remove redundant technology.

### Decision summary

**Problem:**  
`...`

**Selected outcome:**  
`...`

**Reasoning:**  
`...`

**Required controls or conditions:**  
`...`

**Owner:**  
`...`

**Review date:**  
`YYYY-MM-DD`

**Open evidence:**  
`...`

## Synthetic example

A team requests a new analytics service because preparing a recurring report requires several manual transformations.

The review finds that:

- the business outcome is clear and measurable;
- an existing licensed platform covers most, but not all, of the need;
- the proposed product can use single sign-on but automated provisioning requires a higher subscription tier;
- the initial use case can be tested with synthetic or low-sensitivity data;
- the integration is optional during the pilot;
- ownership is clear for the trial but not yet for long-term administration;
- data export is available, but the team has not tested whether the export is sufficient for migration.

A reasonable decision is **Pilot**, not immediate enterprise approval.

Conditions might include:

- a small named user cohort;
- no sensitive production data during the pilot;
- success criteria tied to time saved and report accuracy;
- confirmation of the long-term owner;
- validation of export and deletion behavior;
- a decision date at the end of the pilot;
- no production integration until identity and support requirements are resolved.

The rubric makes the uncertainty visible without turning uncertainty into either reflexive rejection or automatic approval.

## Completion criteria

The evaluation is complete enough for a decision when:

- the underlying problem and desired outcome are clear;
- accountable business and technical owners are identified;
- material identity, data, security, integration, support, cost, and lifecycle questions have answers or explicit open actions;
- alternatives and duplication have been considered;
- evidence is distinguished from vendor claims and assumptions;
- the proposed outcome includes conditions where needed;
- a review or decision date exists;
- the exit path is understood well enough to avoid accidental lock-in.

Not every field needs a perfect answer. The record needs enough truth to make the remaining uncertainty an intentional decision.

## Governance

### Ownership

The service owner is accountable for continued business need. Technical ownership covers administration, access model, integration, support documentation, and operational health. Procurement, security, privacy, legal, accessibility, or architecture review may be required depending on the request, but those functions should not become substitute owners.

### Review triggers

Review the decision when:

- the software materially changes its authentication, data use, pricing, or architecture;
- the use case expands to more sensitive data or a larger population;
- a major integration is added;
- an incident exposes a missing control;
- ownership changes;
- the product becomes redundant;
- renewal creates a natural decision point;
- the original success criteria are no longer being met.

### Decision history

Preserve the original decision and later changes rather than rewriting history. A tool can be reasonable to approve under one set of conditions and reasonable to retire later.

## Trade-offs and limitations

- A consistent rubric reduces omission but can become bureaucracy if every low-risk request receives the same depth of review.
- Scoring systems can create false precision; narrative reasoning should remain visible behind any numeric summary.
- Vendor evidence can reduce uncertainty without eliminating it.
- Security is one decision dimension, not the only one. A secure product can still be duplicative, inaccessible, unsupported, or too expensive to sustain.
- A pilot reduces commitment but still needs ownership and an exit condition.
- Standardization reduces operational complexity but should not be used to dismiss a real capability gap without examining it.

The framework should scale with risk while preserving the same core questions.

## What this demonstrates

- Requirements analysis that begins with the user and service outcome rather than the requested product
- Risk modeling across identity, data, security, integration, cost, support, accessibility, and lifecycle
- Governance that turns software adoption into an owned and reviewable decision
- Preference for reversible experiments when evidence is incomplete
- Documentation designed to preserve reasoning, uncertainty, ownership, and future review

---
id: portfolio.project-card.m365-license-report
title: Microsoft 365 License Report
summary: A PowerShell and Microsoft Graph reporting project for examining license assignment, usage, cost signals, and governance opportunities without treating the output as an automatic removal decision.
artifact_type: project-card
domains:
  - microsoft-365
  - automation
  - operations
status: active
classification: professional-portfolio
source_disclosure: Derived only from the intentionally public M365LicenseReport repository; private tenant data, operational usage, and deployment claims are not included.
skills:
  - PowerShell
  - Microsoft Graph
  - Microsoft 365 administration
  - License governance
  - Reporting and data analysis
created: 2026-08-15
updated: 2026-08-15
---

# Microsoft 365 License Report

> **Portfolio note:** This page is a curated project card, not a copy of the repository README. The executable script and its complete upstream attribution remain in the [canonical public repository](https://github.com/skrrtvonnegut-droid/M365LicenseReport).

## Why it exists

Microsoft 365 licensing decisions are easy to reduce to a seat count, but useful governance requires more context. An administrator may need to distinguish direct from group-based assignment, understand disabled service plans, identify dormant identities, compare purchased capacity with assigned capacity, and interpret cost signals without assuming that inactivity automatically means an account or license is safe to remove.

The Microsoft 365 License Report is a PowerShell working artifact built to bring those signals into one report that can support review and investigation.

## What the public project does

The current public script uses the Microsoft Graph PowerShell SDK and, where the required data is available, reports on:

- direct and group-based license assignments;
- disabled service plans;
- sign-in activity and days since last sign-in;
- disabled or inactive accounts;
- duplicate license conditions;
- purchased-versus-used SKU counts;
- license pricing and estimated cost views;
- organizational cost groupings such as country, department, company, and optional cost center;
- HTML output and optional Excel output, with CSV fallback.

The project uses application and certificate authentication rather than embedding credentials in the script. Tenant-specific SKU and service-plan lookup data are intentionally excluded from the public repository.

## Design choices

### Keep analysis separate from the decision

The report is evidence for a licensing review, not a license-removal engine. A stale sign-in signal can be meaningful, but it does not capture every service dependency, leave scenario, shared responsibility, or business exception. The project therefore surfaces potentially useful conditions without pretending they are sufficient authorization for a change.

### Make provenance visible

The script is an adaptation of `ReportUserAssignedLicenses-MgGraph.PS1` from the Office365ITPros project. The upstream source and related Practical 365 material are identified in the script itself. The portfolio card does not recast that upstream work as original authorship; the professional value here is in maintaining, extending, and operationalizing an attributed working version.

### Keep tenant-derived data outside Git

The public code expects environment-specific lookup data but does not publish it. That keeps executable logic versioned while preserving the boundary between reusable code and tenant-derived operational information.

### Degrade usefully

HTML output is always available. When the optional `ImportExcel` module is present, the report can also produce an Excel workbook; otherwise it falls back to CSV rather than failing solely because the richer export dependency is absent.

## Operational considerations

This is an administrative reporting script, not a turnkey product. Safe reuse requires an operator to review:

- Microsoft Graph permissions and authentication configuration;
- local paths and environment variables;
- SKU and pricing assumptions;
- the freshness and interpretation of sign-in data;
- whether a reported condition is sufficient evidence for a governance action.

The same report can support cost awareness and access governance, but those goals are not identical. A financially attractive removal can still be operationally wrong if the underlying identity or entitlement serves a valid dependency.

## Current maturity

The repository is a public technical working artifact. It contains functioning reporting logic and explicit operational caveats, but it is not presented as a packaged service, universal tenant model, or proof of production adoption. Environment-specific configuration and review remain the responsibility of the operator.

## What this demonstrates

- Extending and maintaining attributed PowerShell work rather than obscuring upstream provenance
- Working with Microsoft Graph data for Microsoft 365 administrative reporting
- Treating licensing as a governance problem involving assignment, activity, ownership, cost, and context
- Separating reusable code from tenant-specific data and credential material
- Designing reports to support accountable decisions instead of automating irreversible conclusions

## Canonical repository

Inspect the current implementation, license, script history, and upstream attribution in [M365LicenseReport](https://github.com/skrrtvonnegut-droid/M365LicenseReport).

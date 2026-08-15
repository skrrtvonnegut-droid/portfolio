# Security and sensitive-information reporting

This repository is intentionally public and should never contain employer-confidential information, private source mappings, credentials, or personal data.

## Publication boundary

Automated checks reject common private workspace links, Microsoft private-storage links, raw ChatGPT links, email addresses, tenant-style identifiers, internal hostnames, private IP addresses, ticket-like identifiers, and private metadata keys. Gitleaks separately scans repository history for credentials and secret-like values.

Repository administrators may also define the Actions secret `PORTFOLIO_DENYLIST` as newline-separated literal terms. The scanner matches these terms case-insensitively in public content while withholding the matched value from workflow logs. This private layer is intended for employer names, internal domains, project codenames, and other organization-specific identifiers that should never cross the publication boundary.

Blank lines and lines beginning with `#` are ignored. Terms shorter than three characters are ignored to avoid dangerously broad matches. The secret should contain only blocking terms, never source documents or explanatory context.

These controls reduce risk; they do not replace contextual human review. A technically clean build can still disclose a recognizable combination of facts.

## Suspected sensitive exposure

Do **not** open a public issue containing the suspected data.

Use the repository's **Security** tab to submit a private vulnerability report. Include only the minimum information required to identify the affected file and revision.

## General security concerns

Generic concerns about the publication-boundary tooling, CI configuration, or dependency posture may be reported through a normal GitHub issue when doing so does not disclose sensitive information.

## Response approach

A confirmed exposure should be handled as an incident:

1. Contain public access where practical.
2. Remove the material from the current branch.
3. Revoke or rotate any affected secret outside this repository.
4. Assess Git history, workflow artifacts, forks, caches, and downstream copies.
5. Document corrective controls without republishing the exposed data.

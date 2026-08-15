# Security and sensitive-information reporting

This repository is intentionally public and should never contain employer-confidential information, private source mappings, credentials, or personal data.

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

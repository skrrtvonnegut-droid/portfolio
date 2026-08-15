# Security and Privacy

## Public repository boundary

This repository must contain only intentionally sanitized Professional Portfolio material.

Do not open a public issue containing a credential, private key, token, certificate, recovery code, production log, internal link, non-public identity, customer or employee data, proprietary document, or organization-specific security configuration.

## Reporting a concern

Use GitHub’s private vulnerability-reporting feature when available, or contact the repository owner through an established private channel. Do not reproduce sensitive material in a public issue merely to prove that it exists.

## Response

If sensitive content is discovered:

1. Stop further distribution and avoid quoting the content.
2. Remove it from the active branch or pull request.
3. Determine whether history rewriting is required.
4. Rotate or revoke any affected credential immediately through the owning system.
5. Assess downstream exposure, forks, caches, workflow artifacts, and logs.
6. Document the incident privately and add a preventive control to the portfolio pipeline.

Deleting a file in a later commit is not sufficient for a secret that already entered Git history.

## Automated controls

CI uses two complementary layers:

- **Gitleaks** scans repository history and common secret formats.
- **Portfolio validation** scans public text for private infrastructure patterns, identifiers, private workspace links, and repository-specific denylist terms.

Configure the private `PORTFOLIO_DENYLIST` repository secret as a newline-separated list of organization names, domains, project names, system names, or other terms that must never enter this public repository. The value remains private; CI receives it only during validation.

External-link checks, strict site rendering, metadata validation, rights rules, and review dates reduce other publication risks.

These controls are safety nets, not confidentiality decision engines. A clean scan does not prove that a document is safe, original, accurate, or non-identifying. Human contextual review remains required.

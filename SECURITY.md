# Security and Privacy

## Public repository boundary

This repository must contain only Public or intentionally sanitized Professional Portfolio material.

Do not open a public issue containing a credential, private key, token, certificate, recovery code, production log, internal link, non-public identity, customer or employee data, proprietary document, or organization-specific security configuration.

## Reporting a concern

Use GitHub’s private vulnerability-reporting feature when available, or contact the repository owner through an established private channel. Do not reproduce sensitive material in a public issue merely to prove that it exists.

## Response

If sensitive content is discovered:

1. Stop further distribution and avoid quoting the content.
2. Remove it from the active branch or pull request.
3. Determine whether history rewriting is required.
4. Rotate or revoke any affected credential immediately through the owning system.
5. Assess downstream exposure, forks, caches, artifacts, and logs.
6. Document the incident privately and add a preventive control to the portfolio pipeline.

Deleting a file in a later commit is not sufficient for a secret that already entered Git history.

## CI scanning

The validation script scans for common secrets, private infrastructure patterns, internal identifiers, and repository-specific denylist terms. Configure the optional `PORTFOLIO_DENYLIST` repository secret as a newline-separated list of private organization names, domains, project names, or other terms that must never enter the public repository.

The scanner is a safety net, not a confidentiality decision engine. Human review remains required.

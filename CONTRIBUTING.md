# Contributing

This is a personal professional portfolio, but corrections and improvements to its public tooling, accessibility, schemas, and reusable templates are welcome.

## Publication boundary

Never include:

- Employer or customer names without explicit public authorization
- Internal domains, tenant identifiers, account names, network details, or ticket data
- Private workspace links or raw conversation references
- Credentials, tokens, connection strings, or secrets
- Copied vendor documentation presented as original work

When proposing content, state whether it is original, AI-assisted original, adapted, or an external reference.

## Pull requests

A pull request should:

1. Explain the public value of the change.
2. Identify any artifact IDs added or changed.
3. Describe provenance and publication rights.
4. Confirm that examples are synthetic or already public.
5. Pass the repository's local and CI checks.

Run:

```bash
pip install -e ".[dev]"
python scripts/run_checks.py
zensical build --clean --strict
```

The private source-evidence and approval workflow is intentionally outside this repository. Public issues and pull requests are not substitutes for private candidate review.

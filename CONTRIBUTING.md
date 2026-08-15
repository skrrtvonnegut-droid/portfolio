# Contributing

This is a personal professional portfolio, but corrections and improvements to its public tooling, accessibility, schemas, and reusable templates are welcome.

## Publication boundary

Never include:

- Employer or customer names without explicit public authorization
- Internal domains, tenant identifiers, account names, network details, or ticket data
- Private workspace links or raw conversation references
- Credentials, tokens, connection strings, or secrets
- Copied vendor documentation presented as original work

When proposing content, identify whether it is original, AI-assisted original, adapted, or an external reference.

## Pull requests

A pull request should:

1. Explain the public value of the change.
2. Identify artifact IDs added, changed, superseded, or archived.
3. Describe provenance, authorship, and publication rights.
4. Confirm that examples are synthetic or already public.
5. Set or update review dates.
6. Pass the repository's local and CI checks.

Run:

```bash
python -m pip install -r requirements-dev.txt
python scripts/portfolio.py validate
python scripts/portfolio.py review-dates
python scripts/portfolio.py links
ruff check scripts tests
python -m unittest discover -s tests
zensical build --clean --strict
python scripts/portfolio.py catalog --output site/catalog.json
```

The private source-evidence and approval workflow is intentionally outside this repository. Public issues and pull requests are not substitutes for private candidate review.

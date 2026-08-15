# Living Professional Portfolio

This repository is the public presentation and validation layer for Breezy Lynne's living professional portfolio.

It is designed to accumulate **sanitized, attributable, reviewable professional artifacts** over time without turning private work history, employer documentation, or raw AI conversations into a public data dump.

> **Automatic accumulation; deliberate publication.**

## What belongs here

- Sanitized case studies
- Reusable technical and governance patterns
- Public project cards that link to canonical repositories
- Learning notes that demonstrate durable professional growth
- Methodology and documentation templates

## What never belongs here

- Raw ChatGPT conversation history
- Private workspace links or source mappings
- Employer names, tenant details, production identifiers, internal topology, or operational secrets
- Customer or employee data
- Third-party documentation presented as original work
- Unreviewed AI-generated prose

Private evidence and approval state remain outside this repository. A public artifact enters through a pull request, passes automated publication-boundary checks, and is merged only after human review.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/run_checks.py
zensical serve
```

On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python scripts/run_checks.py
zensical serve
```

## Repository structure

```text
docs/        Public site content
data/        Public structured metadata
schemas/     Public artifact contracts
templates/   Sanitized authoring templates
scripts/     Validation, indexing, and boundary controls
tests/       Publication-boundary regression tests
.github/     CI, deployment, maintenance, and contribution workflows
```

The site is built with [Zensical](https://zensical.org/) and deployed through GitHub Pages. Markdown and structured front matter remain the canonical content format so the presentation layer can change without rewriting the portfolio.

## Publication contract

Every portfolio artifact must declare:

- Stable artifact ID and public slug
- Artifact kind and professional domains
- Authorship and provenance
- Publication rights
- Review dates
- Explicit professional-portfolio classification

The schema and validation rules live in [`schemas/portfolio-artifact.schema.json`](schemas/portfolio-artifact.schema.json).

## Current state

The repository foundation and publication controls are active. Historical professional work will be introduced gradually through separate, reviewable pull requests after sanitization.

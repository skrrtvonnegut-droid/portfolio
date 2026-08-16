# Living resume publication architecture

> **Status:** v0.2 is approved and exported to the promotion pull request. Merge and deployment remain pending.

## Purpose

The living resume uses the portfolio's existing publication boundary: private professional material is staged and approved outside this public repository, while GitHub records only a sanitized, approved snapshot and the code that presents it.

The system produces two public representations without creating two manually maintained resumes:

- A styled portfolio page designed for human reading.
- A plain, single-column page designed for printing, copying, and ATS-friendly use.

## Authority and boundaries

| Layer | Authority | Editing rule |
| --- | --- | --- |
| Private candidate | Editorial source and approval record | Resume content changes are staged here |
| `data/resume.yml` | Last approved public snapshot | Written only through an approved promotion |
| Styled and plain pages | Derived presentation | Generated; never edited directly |
| GitHub `main` | Published release record | Changes arrive through a reviewed pull request |

The deployed site never reads from the private workspace at runtime. Private page links, internal identifiers, application-only contact details, and unapproved claims must not enter this repository.

## Promotion flow

1. Edit the canonical resume candidate in the private portfolio pipeline.
2. Resolve factual, privacy, provenance, and rights questions.
3. Move the candidate through `Candidate`, `Sanitizing`, and `Review`.
4. Record an approval hash for the exact normalized public body.
5. Mark the candidate `Approved` and explicitly ready for a public draft.
6. Export the approved body to `data/resume.yml` on a dedicated branch.
7. Validate the schema, regeneration, semantic parity, public-content boundary, links, and site build.
8. Review and merge the pull request; deployment from `main` publishes both views.
9. Write the pull request, commit, deployment, and publication state back to the private candidate.

Any content edit after approval invalidates the approval hash and returns the candidate to review.

Repository checks prove that the public YAML, its recorded digest, and both generated pages agree; they cannot independently attest private workspace state. During promotion, the export actor must compare the computed digest with the candidate's recorded Approval Hash and include that cross-system check in the pull-request evidence. Reviewers enforce this gate without copying private workspace identifiers into GitHub.

## Public content contract

The public snapshot is a versioned semantic document, not page-shaped Markdown. The contract includes:

- Release state, version, approval time, and a SHA256 content hash.
- Public-safe name, headline, location, and labeled HTTPS links.
- Summary paragraphs.
- Ordered skill groups.
- Ordered experience and education entries with stable IDs, partial date ranges, or a completion-only graduation year.
- Ordered achievement bullets as content, not decorative layout.

Stable IDs and explicit order values make changes reviewable and prevent reordering from becoming ambiguous. The exporter must fail on unknown source structures rather than silently dropping content.

## Dual-render invariant

Both pages receive the same semantic resume body. Only their outer shell and CSS may differ. The plain view cannot omit, abbreviate, or reorder content from the styled view.

The deterministic renderer and CI checks now:

- Validate `data/resume.yml` against `schemas/resume.schema.json`.
- Regenerate both pages and fail when tracked outputs are stale.
- Compare headings, dates, bullets, labels, and link targets across both outputs.
- Preserve linear DOM and reading order in the plain view.
- Keep content selectable and printable without JavaScript.

## Public and application variants

The public GitHub snapshot should contain only contact details deliberately approved for the open web. Private phone, email, street address, or job-specific tailoring can remain in a private application overlay and be combined when producing a targeted copy.

A deterministic PDF or word-processing export is intentionally deferred. v0.2 establishes the styled route and the plain print route without introducing an opaque binary that bypasses the text scanner.

## Repository paths

```text
data/resume.yml
schemas/resume.schema.json
templates/resume-stylized.md
templates/resume-plain.md
scripts/build_resume.py
docs/resume/index.md
docs/resume/plain.md
docs/stylesheets/resume.css
tests/test_resume_sync.py
```

The implementation establishes the data, schema, deterministic renderer, templates, routes, scoped styles, approval-hash validation, parity tests, navigation entry, and approved v0.2 public snapshot.

## Implementation status

- The renderer rejects duplicate YAML keys, unknown schema structures, invalid lifecycle metadata, inconsistent dates, duplicate IDs or order values, and stale approval hashes.
- A SHA256 digest covers normalized semantic content while excluding release metadata, avoiding a recursive hash.
- Both routes contain one byte-identical semantic article; only the outer presentation shell and format switch differ.
- Local checks, pull-request CI, pre-commit, and deployment all fail when generated pages are stale.
- The styled view uses a responsive, accessible presentation layer, while the plain view linearizes the same document for printing, copying, and ATS-friendly use.
- The approved v0.2 snapshot is linked from site navigation on the promotion branch; publication completes after review, merge, and deployment.

## Approval outcome

Approved architecture decisions:

1. Reuse the existing portfolio candidate lifecycle and add `Resume` to its artifact taxonomy.
2. Treat the current private resume page as source material and the normalized candidate body as the canonical public draft.
3. Publish a public-safe plain page first; keep application-only contact details in a private overlay.
4. Defer PDF or word-processing generation until its text extraction and privacy controls are designed.
5. Resolve conflicting dates and verify any quantitative or organization-specific claims before approval.

All five decisions have been resolved for v0.2. The exact normalized public body is approved, its digest is recorded in `data/resume.yml`, and both generated views match that snapshot. The pull request merge and deployment are the remaining publication gates.

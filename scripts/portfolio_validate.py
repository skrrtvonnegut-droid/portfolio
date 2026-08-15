"""Repository, schema, semantic, and review-date validation."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable

import jsonschema
import yaml

from portfolio_common import (
    ARTIFACT_ROOT,
    CONFIG_PATH,
    DOCS_ROOT,
    INDEX_PATH,
    MANIFEST_PATH,
    ROOT,
    SCHEMA_PATH,
    STYLE_PATH,
    Artifact,
    governance_records,
    iter_artifact_paths,
    load_artifacts,
    load_manifest,
    load_schema,
    parse_artifact,
    public_text_paths,
    validate_config,
    validate_manifest,
)
from portfolio_security import check_relative_links, scan_text


def validate_artifact_semantics(metadata: dict, label: str) -> list[str]:
    """Apply cross-field rules that are clearer outside JSON Schema."""

    errors: list[str] = []
    provenance = metadata.get("provenance")
    rights = metadata.get("rights")
    if isinstance(rights, dict):
        attribution = rights.get("attribution")
        source_url = rights.get("source_url")
        if provenance in {"adapted", "external-reference"}:
            if not attribution:
                errors.append(f"{label}: rights.attribution is required for {provenance}")
            if not source_url:
                errors.append(f"{label}: rights.source_url is required for {provenance}")
        elif provenance in {"original", "ai-assisted-original"} and (attribution or source_url):
            errors.append(
                f"{label}: original work must keep rights.attribution and rights.source_url null"
            )

    review = metadata.get("review")
    if isinstance(review, dict):
        try:
            last_reviewed = dt.date.fromisoformat(str(review.get("last_reviewed")))
            review_due = dt.date.fromisoformat(str(review.get("review_due")))
            if review_due < last_reviewed:
                errors.append(f"{label}: review_due cannot precede last_reviewed")
        except (TypeError, ValueError):
            pass
    return errors


def validate_repository() -> list[str]:
    """Validate repository structure, metadata, content, links, and privacy controls."""

    errors: list[str] = []
    for required in (SCHEMA_PATH, MANIFEST_PATH, CONFIG_PATH, STYLE_PATH, INDEX_PATH):
        if not required.exists():
            errors.append(f"missing required file: {required.relative_to(ROOT)}")
    if (ROOT / "artifacts").exists():
        errors.append("legacy artifacts/ directory exists; public artifacts must live under docs/artifacts/")
    if errors:
        return errors

    errors.extend(validate_config())
    try:
        manifest = load_manifest()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return errors + [f"portfolio.yml: invalid manifest: {exc}"]

    errors.extend(validate_manifest(manifest))
    governance, governance_errors = governance_records(manifest)
    errors.extend(governance_errors)

    validator = jsonschema.Draft202012Validator(
        load_schema(), format_checker=jsonschema.FormatChecker()
    )
    seen_ids = {}
    seen_slugs = {}
    artifacts: list[Artifact] = []

    for path in iter_artifact_paths():
        try:
            artifact = parse_artifact(path, governance)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue

        artifacts.append(artifact)
        for issue in sorted(validator.iter_errors(artifact.metadata), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path) or "metadata"
            errors.append(f"{artifact.relative_path}: {location}: {issue.message}")
        errors.extend(validate_artifact_semantics(artifact.metadata, str(artifact.relative_path)))

        artifact_id = str(artifact.metadata.get("id", ""))
        if artifact_id in seen_ids:
            first = seen_ids[artifact_id].relative_to(ROOT)
            errors.append(f"{artifact.relative_path}: duplicate id {artifact_id!r}; first used by {first}")
        elif artifact_id:
            seen_ids[artifact_id] = path

        slug = str(artifact.metadata.get("slug", ""))
        if slug in seen_slugs:
            first = seen_slugs[slug].relative_to(ROOT)
            errors.append(f"{artifact.relative_path}: duplicate slug {slug!r}; first used by {first}")
        elif slug:
            seen_slugs[slug] = path

        expected_slug = "/" + path.relative_to(DOCS_ROOT).with_suffix("").as_posix() + "/"
        if slug and slug != expected_slug:
            errors.append(
                f"{artifact.relative_path}: slug {slug!r} must match rendered path {expected_slug!r}"
            )

        title = str(artifact.metadata.get("title", ""))
        if not artifact.body.startswith(f"# {title}\n"):
            errors.append(f"{artifact.relative_path}: first heading must exactly match metadata title")
        if len(artifact.body) < 1_200:
            errors.append(
                f"{artifact.relative_path}: body is too short to demonstrate a durable professional artifact"
            )
        if "## What this demonstrates" not in artifact.body:
            errors.append(f"{artifact.relative_path}: missing 'What this demonstrates' section")

        disclosure = str(artifact.metadata.get("source_disclosure", ""))
        if "http://" in disclosure or "https://" in disclosure:
            errors.append(f"{artifact.relative_path}: source_disclosure must not contain a source URL")
        created = str(artifact.metadata.get("created", ""))
        updated = str(artifact.metadata.get("updated", ""))
        if created and updated and updated < created:
            errors.append(f"{artifact.relative_path}: updated date precedes created date")
        errors.extend(check_relative_links(path, artifact.body))

    for artifact_id in sorted(set(governance) - set(seen_ids)):
        errors.append(f"portfolio.yml: governance record has no artifact file: {artifact_id}")
    if not artifacts:
        errors.append(f"no artifacts found under {ARTIFACT_ROOT.relative_to(ROOT)}/")

    for path in public_text_paths():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path.relative_to(ROOT)}: publishable text file is not valid UTF-8")
            continue
        errors.extend(scan_text(text, str(path.relative_to(ROOT))))
        if path.suffix.lower() == ".md":
            errors.extend(check_relative_links(path, text))
    return sorted(set(errors))


def find_overdue_reviews(
    today: dt.date, artifacts: Iterable[Artifact] | None = None
) -> list[str]:
    """Return active artifacts whose public review date has passed."""

    overdue: list[str] = []
    for artifact in artifacts if artifacts is not None else load_artifacts():
        if artifact.metadata.get("status") not in {"active", "review-due"}:
            continue
        due = dt.date.fromisoformat(str(artifact.metadata["review"]["review_due"]))
        if due < today:
            overdue.append(
                f"{artifact.relative_path} ({artifact.metadata['id']}) was due for review on {due.isoformat()}"
            )
    return overdue

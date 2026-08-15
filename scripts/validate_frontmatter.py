#!/usr/bin/env python3
"""Validate public artifact metadata against the portfolio contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from scripts.common import (
    ARTIFACT_REGISTRY_PATH,
    DOCS_ROOT,
    SCHEMA_PATH,
    FrontMatterError,
    is_artifact_location,
    iter_files,
    parse_markdown,
    repo_relative,
)

REGISTRY_ENTRY_KEYS = {"path", "source_id", "metadata"}
REGISTRY_METADATA_KEYS = {
    "id",
    "slug",
    "kind",
    "status",
    "classification",
    "provenance",
    "authorship",
    "domains",
    "skills",
    "rights",
    "review",
    "featured",
}


def load_validator(schema_path: Path = SCHEMA_PATH) -> Draft202012Validator:
    """Load the JSON Schema validator."""

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def load_artifact_registry(
    path: Path = ARTIFACT_REGISTRY_PATH,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load public governance overlays for reconstructed artifact narratives."""

    if not path.exists():
        return {}, []

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return {}, [f"{repo_relative(path)}: cannot read artifact registry: {exc}"]

    if not isinstance(payload, dict):
        return {}, [f"{repo_relative(path)}: registry root must be a mapping"]

    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append(f"{repo_relative(path)}: schema_version must be 1")

    raw_records = payload.get("artifacts")
    if not isinstance(raw_records, list):
        return {}, errors + [f"{repo_relative(path)}: artifacts must be a list"]

    records: dict[str, dict[str, Any]] = {}
    seen_source_ids: set[str] = set()
    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()

    for index, record in enumerate(raw_records):
        label = f"{repo_relative(path)}:artifacts[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: entry must be a mapping")
            continue

        missing = REGISTRY_ENTRY_KEYS - set(record)
        extra = set(record) - REGISTRY_ENTRY_KEYS
        if missing:
            errors.append(f"{label}: missing keys: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{label}: unsupported keys: {', '.join(sorted(extra))}")

        public_path = record.get("path")
        source_id = record.get("source_id")
        metadata = record.get("metadata")
        if not isinstance(public_path, str):
            errors.append(f"{label}.path: must be a repository-relative string")
            continue

        parsed_path = PurePosixPath(public_path)
        if (
            parsed_path.is_absolute()
            or ".." in parsed_path.parts
            or not public_path.startswith("docs/artifacts/")
            or parsed_path.suffix != ".md"
        ):
            errors.append(
                f"{label}.path: must identify a Markdown file beneath docs/artifacts/"
            )
            continue
        if public_path in records:
            errors.append(f"{label}.path: duplicate path {public_path!r}")
            continue

        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{label}.source_id: must be a non-empty string")
            continue
        if source_id in seen_source_ids:
            errors.append(f"{label}.source_id: duplicate value {source_id!r}")
        seen_source_ids.add(source_id)

        if not isinstance(metadata, dict):
            errors.append(f"{label}.metadata: must be a mapping")
            continue
        metadata_missing = REGISTRY_METADATA_KEYS - set(metadata)
        metadata_extra = set(metadata) - REGISTRY_METADATA_KEYS
        if metadata_missing:
            errors.append(
                f"{label}.metadata: missing keys: {', '.join(sorted(metadata_missing))}"
            )
        if metadata_extra:
            errors.append(
                f"{label}.metadata: unsupported keys: {', '.join(sorted(metadata_extra))}"
            )

        canonical_id = metadata.get("id")
        slug = metadata.get("slug")
        if isinstance(canonical_id, str):
            if canonical_id in seen_ids:
                errors.append(f"{label}.metadata.id: duplicate value {canonical_id!r}")
            seen_ids.add(canonical_id)
        if isinstance(slug, str):
            if slug in seen_slugs:
                errors.append(f"{label}.metadata.slug: duplicate value {slug!r}")
            seen_slugs.add(slug)

        records[public_path] = {"source_id": source_id, "metadata": metadata}

    return records, errors


def canonicalize_registered_metadata(
    document_metadata: dict[str, Any],
    record: dict[str, Any],
    *,
    path: Path,
) -> tuple[dict[str, Any], list[str]]:
    """Merge narrative metadata with its public governance overlay."""

    errors: list[str] = []
    source_id = record["source_id"]
    if document_metadata.get("id") != source_id:
        errors.append(
            f"{repo_relative(path)}: narrative id must match registry source_id {source_id!r}"
        )

    if document_metadata.get("classification") != "professional-portfolio":
        errors.append(
            f"{repo_relative(path)}: reconstructed narrative classification must be "
            "professional-portfolio"
        )

    disclosure = document_metadata.get("source_disclosure")
    if not isinstance(disclosure, str) or len(disclosure.strip()) < 40:
        errors.append(
            f"{repo_relative(path)}: reconstructed narrative requires a substantive "
            "source_disclosure"
        )

    canonical = dict(record["metadata"])
    canonical["title"] = document_metadata.get("title")
    canonical["summary"] = document_metadata.get("summary")
    return canonical, errors


def validate_metadata(
    metadata: dict[str, Any],
    *,
    path: Path,
    validator: Draft202012Validator,
) -> list[str]:
    """Validate one metadata mapping and return human-readable errors."""

    errors: list[str] = []
    for error in sorted(validator.iter_errors(metadata), key=lambda item: list(item.path)):
        location = ".".join(str(part) for part in error.path) or "<root>"
        errors.append(f"{repo_relative(path)}:{location}: {error.message}")

    provenance = metadata.get("provenance")
    rights = metadata.get("rights")
    if isinstance(rights, dict):
        attribution = rights.get("attribution")
        source_url = rights.get("source_url")
        if provenance in {"adapted", "external-reference"}:
            if not attribution:
                errors.append(
                    f"{repo_relative(path)}:rights.attribution: required for {provenance}"
                )
            if not source_url:
                errors.append(f"{repo_relative(path)}:rights.source_url: required for {provenance}")
        elif attribution or source_url:
            errors.append(
                f"{repo_relative(path)}:rights: attribution/source_url should be null "
                f"for provenance {provenance!r}"
            )

    review = metadata.get("review")
    if isinstance(review, dict):
        try:
            reviewed = date.fromisoformat(str(review.get("last_reviewed")))
            due = date.fromisoformat(str(review.get("review_due")))
            if due < reviewed:
                errors.append(
                    f"{repo_relative(path)}:review.review_due: cannot precede last_reviewed"
                )
        except (TypeError, ValueError):
            pass

    return errors


def _uses_repository_registry(roots: Iterable[Path]) -> bool:
    docs_root = DOCS_ROOT.resolve()
    for root in roots:
        try:
            root.resolve().relative_to(docs_root)
            return True
        except ValueError:
            continue
    return False


def collect_artifacts(
    roots: Iterable[Path],
    *,
    validator: Draft202012Validator | None = None,
    registry_path: Path | None = None,
) -> tuple[list[tuple[Path, dict[str, Any]]], list[str]]:
    """Collect and validate canonical public artifacts beneath roots."""

    roots = list(roots)
    validator = validator or load_validator()
    artifacts: list[tuple[Path, dict[str, Any]]] = []
    errors: list[str] = []

    use_default_registry = registry_path is None and _uses_repository_registry(roots)
    selected_registry = ARTIFACT_REGISTRY_PATH if use_default_registry else registry_path
    registry: dict[str, dict[str, Any]] = {}
    if selected_registry is not None:
        registry, registry_errors = load_artifact_registry(selected_registry)
        errors.extend(registry_errors)

    used_registry_paths: set[str] = set()
    validate_registry_coverage = registry_path is not None or any(
        root.resolve() == DOCS_ROOT.resolve() for root in roots
    )

    for path in iter_files(roots, suffixes={".md"}):
        try:
            document = parse_markdown(path)
        except FrontMatterError as exc:
            errors.append(str(exc))
            continue

        expected = is_artifact_location(path)
        relative = repo_relative(path)
        record = registry.get(relative)

        if expected and document.metadata is None:
            errors.append(f"{relative}: artifact page requires YAML front matter")
            continue
        if document.metadata is None or "id" not in document.metadata:
            continue

        if record is not None:
            metadata, merge_errors = canonicalize_registered_metadata(
                document.metadata,
                record,
                path=path,
            )
            errors.extend(merge_errors)
            used_registry_paths.add(relative)
        else:
            metadata = document.metadata
            if expected and "kind" not in metadata:
                errors.append(
                    f"{relative}: legacy narrative metadata requires an entry in "
                    f"{repo_relative(ARTIFACT_REGISTRY_PATH)}"
                )
                continue

        errors.extend(validate_metadata(metadata, path=path, validator=validator))
        if expected:
            expected_slug = (
                "/"
                + path.resolve()
                .relative_to(DOCS_ROOT.resolve())
                .with_suffix("")
                .as_posix()
                + "/"
            )
            if metadata.get("slug") != expected_slug:
                errors.append(
                    f"{relative}: slug {metadata.get('slug')!r} must match "
                    f"rendered path {expected_slug!r}"
                )
        artifacts.append((path, metadata))

    if validate_registry_coverage:
        for registered_path in sorted(set(registry) - used_registry_paths):
            errors.append(
                f"{repo_relative(selected_registry or ARTIFACT_REGISTRY_PATH)}: "
                f"registry entry has no scanned artifact: {registered_path}"
            )

    by_id: dict[str, list[str]] = defaultdict(list)
    by_slug: dict[str, list[str]] = defaultdict(list)
    for path, metadata in artifacts:
        artifact_id = metadata.get("id")
        slug = metadata.get("slug")
        if isinstance(artifact_id, str):
            by_id[artifact_id].append(repo_relative(path))
        if isinstance(slug, str):
            by_slug[slug].append(repo_relative(path))

    for value, paths in sorted(by_id.items()):
        if len(paths) > 1:
            errors.append(f"duplicate artifact id {value!r}: {', '.join(paths)}")
    for value, paths in sorted(by_slug.items()):
        if len(paths) > 1:
            errors.append(f"duplicate artifact slug {value!r}: {', '.join(paths)}")

    return artifacts, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[DOCS_ROOT],
        help="Markdown roots to validate (default: docs)",
    )
    args = parser.parse_args()

    artifacts, errors = collect_artifacts(args.paths)
    if errors:
        print("Portfolio front-matter validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(artifacts)} public portfolio artifact(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

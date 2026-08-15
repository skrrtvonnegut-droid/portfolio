#!/usr/bin/env python3
"""Validate public artifact front matter against the portfolio contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from scripts.common import (
    DOCS_ROOT,
    SCHEMA_PATH,
    FrontMatterError,
    is_artifact_location,
    iter_files,
    parse_markdown,
    repo_relative,
)


def load_validator(schema_path: Path = SCHEMA_PATH) -> Draft202012Validator:
    """Load the JSON Schema validator."""

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


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
            # JSON Schema reports malformed or absent dates.
            pass

    return errors


def collect_artifacts(
    roots: Iterable[Path],
    *,
    validator: Draft202012Validator | None = None,
) -> tuple[list[tuple[Path, dict[str, Any]]], list[str]]:
    """Collect and validate artifacts beneath roots."""

    validator = validator or load_validator()
    artifacts: list[tuple[Path, dict[str, Any]]] = []
    errors: list[str] = []

    for path in iter_files(roots, suffixes={".md"}):
        try:
            document = parse_markdown(path)
        except FrontMatterError as exc:
            errors.append(str(exc))
            continue

        expected = is_artifact_location(path)
        if expected and document.metadata is None:
            errors.append(f"{repo_relative(path)}: artifact page requires YAML front matter")
            continue

        if document.metadata is None or "id" not in document.metadata:
            continue

        errors.extend(validate_metadata(document.metadata, path=path, validator=validator))
        artifacts.append((path, document.metadata))

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

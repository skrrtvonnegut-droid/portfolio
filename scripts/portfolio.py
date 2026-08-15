#!/usr/bin/env python3
"""Validate, review, and publish the living professional portfolio."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from portfolio_common import Artifact, LINK_ROOTS, ROOT, iter_artifact_paths, load_artifacts
from portfolio_links import check_external_links, validate_external_url
from portfolio_security import scan_text
from portfolio_validate import (
    find_overdue_reviews,
    validate_artifact_semantics,
    validate_repository,
)


def catalog_records() -> list[dict]:
    """Return public catalog records with content and governance metadata merged."""

    artifacts = sorted(
        load_artifacts(),
        key=lambda item: (
            not item.metadata["featured"],
            item.metadata["domains"][0],
            item.metadata["title"],
        ),
    )
    return [
        {
            **artifact.metadata,
            "path": artifact.path.relative_to(ROOT / "docs").with_suffix("").as_posix() + "/",
        }
        for artifact in artifacts
    ]


def write_catalog(output: Path) -> None:
    """Write the machine-readable public artifact catalog."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(catalog_records(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def command_validate() -> int:
    errors = validate_repository()
    if errors:
        print("Portfolio validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Portfolio validation passed: {len(list(iter_artifact_paths()))} artifacts checked.")
    return 0


def command_catalog(output: Path) -> int:
    errors = validate_repository()
    if errors:
        print("Catalog generation blocked by validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    write_catalog(output)
    print(f"Wrote machine-readable catalog to {output}")
    return 0


def command_review_dates(today: dt.date) -> int:
    errors = validate_repository()
    if errors:
        print("Review-date check blocked by repository validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    overdue = find_overdue_reviews(today)
    if overdue:
        print("Portfolio review required:", file=sys.stderr)
        for item in overdue:
            print(f"  - {item}", file=sys.stderr)
        return 1
    print("No active portfolio artifacts are past review.")
    return 0


def command_links(paths: list[Path], external: bool) -> int:
    failures, warnings, count = check_external_links(paths, external=external)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if failures:
        print("External link validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"Validated {count} unique external link(s).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "validate", help="Validate metadata, links, privacy patterns, and repository structure"
    )

    catalog_parser = subcommands.add_parser(
        "catalog", help="Write a machine-readable artifact catalog"
    )
    catalog_parser.add_argument(
        "--output", type=Path, default=ROOT / "site" / "catalog.json"
    )

    review_parser = subcommands.add_parser(
        "review-dates", help="Fail when an active public artifact is past its review date"
    )
    review_parser.add_argument(
        "--today",
        type=dt.date.fromisoformat,
        default=dt.date.today(),
        help="Override the current date for deterministic checks",
    )

    links_parser = subcommands.add_parser(
        "links", help="Validate public external links"
    )
    links_parser.add_argument(
        "paths", nargs="*", type=Path, default=list(LINK_ROOTS)
    )
    links_parser.add_argument(
        "--external",
        action="store_true",
        help="Perform live HTTP requests; transient failures are warnings",
    )

    args = parser.parse_args(argv)
    if args.command == "validate":
        return command_validate()
    if args.command == "catalog":
        return command_catalog(args.output)
    if args.command == "review-dates":
        return command_review_dates(args.today)
    if args.command == "links":
        return command_links(args.paths, args.external)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

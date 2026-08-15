#!/usr/bin/env python3
"""Fail when a published artifact is past its declared review date."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from scripts.common import DOCS_ROOT, repo_relative
from scripts.validate_frontmatter import collect_artifacts


def find_overdue(today: date, roots: list[Path]) -> tuple[list[str], list[str]]:
    """Return overdue artifact messages and validation errors."""

    artifacts, errors = collect_artifacts(roots)
    overdue: list[str] = []
    for path, metadata in artifacts:
        if metadata.get("status") != "published":
            continue
        due = date.fromisoformat(str(metadata["review"]["review_due"]))
        if due < today:
            overdue.append(
                f"{repo_relative(path)} ({metadata['id']}) was due for review on {due.isoformat()}"
            )
    return overdue, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="Override the current date for deterministic testing.",
    )
    parser.add_argument("paths", nargs="*", type=Path, default=[DOCS_ROOT])
    args = parser.parse_args()

    overdue, errors = find_overdue(args.today, args.paths)
    if errors or overdue:
        print("Portfolio review-date check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        for item in overdue:
            print(f"- {item}", file=sys.stderr)
        return 1

    print("No published artifacts are past review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

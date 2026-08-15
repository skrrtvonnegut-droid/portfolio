#!/usr/bin/env python3
"""Apply deterministic structural checks to public Markdown."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

from scripts.common import DOCS_ROOT, REPO_ROOT, iter_files, repo_relative

TEMPLATES_ROOT = REPO_ROOT / "templates"
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+\S")
FENCE_PATTERN = re.compile(r"^```(.*)$")


def lint_file(path: Path) -> list[str]:
    """Return Markdown lint errors for one file."""

    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    if text and not text.endswith("\n"):
        errors.append(f"{repo_relative(path)}: file must end with a newline")

    in_fence = False
    h1_count = 0
    previous_heading_level = 0

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\r\n")

        if "\t" in line:
            errors.append(f"{repo_relative(path)}:{number}: tabs are not allowed")
        if line.endswith((" ", "\t")):
            errors.append(f"{repo_relative(path)}:{number}: trailing whitespace")

        fence = FENCE_PATTERN.match(line)
        if fence:
            info = fence.group(1).strip()
            if not in_fence and not info:
                errors.append(
                    f"{repo_relative(path)}:{number}: opening code fence requires a language"
                )
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        heading = HEADING_PATTERN.match(line)
        if not heading:
            continue
        level = len(heading.group(1))
        if level == 1:
            h1_count += 1
        if previous_heading_level and level > previous_heading_level + 1:
            errors.append(
                f"{repo_relative(path)}:{number}: heading level jumps "
                f"from H{previous_heading_level} to H{level}"
            )
        previous_heading_level = level

    if in_fence:
        errors.append(f"{repo_relative(path)}: unclosed code fence")
    if h1_count != 1:
        errors.append(f"{repo_relative(path)}: expected exactly one H1, found {h1_count}")

    return errors


def lint_paths(paths: Iterable[Path]) -> list[str]:
    """Lint Markdown files beneath paths."""

    errors: list[str] = []
    for path in iter_files(paths, suffixes={".md"}):
        errors.extend(lint_file(path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[DOCS_ROOT, TEMPLATES_ROOT],
        help="Markdown roots to lint (default: docs templates)",
    )
    args = parser.parse_args()

    errors = lint_paths(args.paths)
    if errors:
        print("Markdown lint failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Markdown lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

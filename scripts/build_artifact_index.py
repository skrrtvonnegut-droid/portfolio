#!/usr/bin/env python3
"""Build the deterministic public artifact index from validated metadata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from scripts.common import ARTIFACT_INDEX_PATH, DOCS_ROOT
from scripts.validate_frontmatter import collect_artifacts


def _link_for(path: Path) -> str:
    relative = path.resolve().relative_to(DOCS_ROOT.resolve())
    return relative.as_posix()


def render_index(artifacts: list[tuple[Path, dict[str, Any]]]) -> str:
    """Render the generated index."""

    published = [
        (path, metadata)
        for path, metadata in artifacts
        if metadata.get("status") == "published"
    ]
    published.sort(
        key=lambda item: (
            not bool(item[1].get("featured")),
            str(item[1].get("kind", "")),
            str(item[1].get("title", "")).casefold(),
        )
    )

    lines = [
        "<!-- GENERATED: run `python -m scripts.build_artifact_index` -->",
        "# Artifact index",
        "",
    ]

    if not published:
        lines.extend(
            [
                "No portfolio artifacts have been published yet.",
                "",
                "The repository foundation, schema, publication-boundary controls, and "
                "deployment workflow are active. The first artifacts will be introduced "
                "through separate reviewed pull requests.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "| Artifact | Kind | Domains | Review due |",
            "| --- | --- | --- | --- |",
        ]
    )
    for path, metadata in published:
        title = str(metadata["title"]).replace("|", r"\|")
        kind = str(metadata["kind"]).replace("-", " ")
        domains = ", ".join(str(value).replace("-", " ") for value in metadata["domains"])
        review_due = str(metadata["review"]["review_due"])
        lines.append(
            f"| [{title}]({_link_for(path)}) | {kind} | {domains} | {review_due} |"
        )

    lines.extend(["", f"**Published artifacts:** {len(published)}", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if docs/artifact-index.md is not current.",
    )
    args = parser.parse_args()

    artifacts, errors = collect_artifacts([DOCS_ROOT])
    if errors:
        print("Cannot build artifact index because validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    rendered = render_index(artifacts)
    current = ARTIFACT_INDEX_PATH.read_text(encoding="utf-8") if ARTIFACT_INDEX_PATH.exists() else ""

    if args.check:
        if current != rendered:
            print(
                "Artifact index is stale. Run `python -m scripts.build_artifact_index`.",
                file=sys.stderr,
            )
            return 1
        print("Artifact index is current.")
        return 0

    ARTIFACT_INDEX_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {ARTIFACT_INDEX_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

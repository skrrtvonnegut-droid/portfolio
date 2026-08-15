#!/usr/bin/env python3
"""Validate external Markdown links with conservative network failure handling."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scripts.common import DOCS_ROOT, iter_files, repo_relative

INLINE_LINK = re.compile(r"!?\[[^\]]*\]\((https?://[^)\s]+)\)")
AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")
SUCCESS_CODES = set(range(200, 400))
SOFT_CODES = {401, 403, 408, 425, 429, 500, 502, 503, 504}
FAIL_CODES = {404, 410}


@dataclass(frozen=True)
class LinkReference:
    path: Path
    line: int
    url: str


def discover_links(paths: Iterable[Path]) -> list[LinkReference]:
    """Find unique external links in Markdown."""

    references: list[LinkReference] = []
    seen: set[tuple[Path, str]] = set()
    for path in iter_files(paths, suffixes={".md"}):
        text = path.read_text(encoding="utf-8")
        for pattern in (INLINE_LINK, AUTOLINK):
            for match in pattern.finditer(text):
                url = match.group(1).rstrip(".,;:")
                key = (path.resolve(), url)
                if key in seen:
                    continue
                seen.add(key)
                references.append(
                    LinkReference(
                        path=path,
                        line=text.count("\n", 0, match.start()) + 1,
                        url=url,
                    )
                )
    return references


def validate_url(url: str, attempts: int = 2, timeout: float = 12.0) -> tuple[bool, str]:
    """Return hard validity and a status message for one URL."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "malformed URL"

    headers = {
        "User-Agent": "breezy-portfolio-link-check/1.0",
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }

    last_message = "network error"
    for attempt in range(attempts):
        for method in ("HEAD", "GET"):
            request = Request(url, headers=headers, method=method)
            try:
                with urlopen(request, timeout=timeout) as response:
                    status = response.getcode()
                if status in SUCCESS_CODES:
                    return True, f"HTTP {status}"
                if status in SOFT_CODES:
                    return True, f"HTTP {status} (reachable but not conclusively testable)"
                if status in FAIL_CODES:
                    return False, f"HTTP {status}"
                last_message = f"HTTP {status}"
            except HTTPError as exc:
                if exc.code == 405 and method == "HEAD":
                    continue
                if exc.code in SOFT_CODES:
                    return True, f"HTTP {exc.code} (reachable but not conclusively testable)"
                if exc.code in FAIL_CODES:
                    return False, f"HTTP {exc.code}"
                last_message = f"HTTP {exc.code}"
            except (URLError, TimeoutError, OSError) as exc:
                last_message = str(exc)
                break
        if attempt + 1 < attempts:
            time.sleep(1.0 + attempt)

    # A transient network failure should be visible but should not block publication.
    return True, f"warning: {last_message}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[DOCS_ROOT])
    parser.add_argument(
        "--external",
        action="store_true",
        help="Perform network requests. Without this flag, only URL syntax is checked.",
    )
    args = parser.parse_args()

    references = discover_links(args.paths)
    failures: list[str] = []
    warnings: list[str] = []

    checked: dict[str, tuple[bool, str]] = {}
    for reference in references:
        if reference.url not in checked:
            if args.external:
                checked[reference.url] = validate_url(reference.url)
            else:
                parsed = urlparse(reference.url)
                checked[reference.url] = (
                    parsed.scheme in {"http", "https"} and bool(parsed.netloc),
                    "syntax",
                )

        valid, message = checked[reference.url]
        rendered = (
            f"{repo_relative(reference.path)}:{reference.line}: "
            f"{reference.url} — {message}"
        )
        if not valid:
            failures.append(rendered)
        elif message.startswith("warning:"):
            warnings.append(rendered)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if failures:
        print("External link validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Validated {len(checked)} unique external link(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Public external-link discovery and conservative HTTP validation."""

from __future__ import annotations

import re
import time
from collections.abc import Iterable
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from portfolio_common import ROOT, LinkReference

MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")
SUCCESS_CODES = set(range(200, 400))
SOFT_CODES = {401, 403, 408, 425, 429, 500, 502, 503, 504}
HARD_CODES = {404, 410}


def iter_markdown_paths(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield Markdown files beneath paths in deterministic order."""

    discovered: set[Path] = set()
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.suffix.lower() == ".md":
            discovered.add(path)
        elif path.is_dir():
            discovered.update(candidate for candidate in path.rglob("*.md") if candidate.is_file())
    yield from sorted(discovered)


def discover_external_links(paths: Iterable[Path]) -> list[LinkReference]:
    """Discover unique external Markdown links with source locations."""

    references: list[LinkReference] = []
    seen: set[tuple[Path, str]] = set()
    for path in iter_markdown_paths(paths):
        text = path.read_text(encoding="utf-8")
        for pattern in (MARKDOWN_LINK, AUTOLINK):
            for match in pattern.finditer(text):
                raw = match.group(1).strip().split(" ", 1)[0].strip("<>")
                if not raw.startswith(("http://", "https://")):
                    continue
                url = raw.rstrip(".,;:")
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


def validate_external_url(
    url: str, attempts: int = 2, timeout: float = 12.0
) -> tuple[bool, str]:
    """Validate one URL without letting transient failures block publication."""

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
                    return True, f"HTTP {status} (reachable but inconclusive)"
                if status in HARD_CODES:
                    return False, f"HTTP {status}"
                last_message = f"HTTP {status}"
            except HTTPError as exc:
                if exc.code == 405 and method == "HEAD":
                    continue
                if exc.code in SOFT_CODES:
                    return True, f"HTTP {exc.code} (reachable but inconclusive)"
                if exc.code in HARD_CODES:
                    return False, f"HTTP {exc.code}"
                last_message = f"HTTP {exc.code}"
            except (URLError, TimeoutError, OSError) as exc:
                last_message = str(exc)
                break
        if attempt + 1 < attempts:
            time.sleep(1.0 + attempt)
    return True, f"warning: {last_message}"


def check_external_links(
    paths: Iterable[Path], *, external: bool
) -> tuple[list[str], list[str], int]:
    """Check external link syntax and optionally live HTTP status."""

    failures: list[str] = []
    warnings: list[str] = []
    checked: dict[str, tuple[bool, str]] = {}
    for reference in discover_external_links(paths):
        if reference.url not in checked:
            if external:
                checked[reference.url] = validate_external_url(reference.url)
            else:
                parsed = urlparse(reference.url)
                checked[reference.url] = (
                    parsed.scheme in {"http", "https"} and bool(parsed.netloc),
                    "syntax",
                )
        valid, message = checked[reference.url]
        rendered = (
            f"{reference.path.relative_to(ROOT)}:{reference.line}: "
            f"{reference.url} — {message}"
        )
        if not valid:
            failures.append(rendered)
        elif message.startswith("warning:"):
            warnings.append(rendered)
    return failures, warnings, len(checked)

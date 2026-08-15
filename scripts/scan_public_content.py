#!/usr/bin/env python3
"""Reject common private references and identifiers from public content."""

from __future__ import annotations

import argparse
import ipaddress
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from scripts.common import DOCS_ROOT, REPO_ROOT, iter_files, repo_relative

DATA_ROOT = REPO_ROOT / "data"
PUBLIC_CONTENT_PATHS = [
    DOCS_ROOT,
    DATA_ROOT,
    REPO_ROOT / "templates",
    REPO_ROOT / "README.md",
    REPO_ROOT / "CONTRIBUTING.md",
    REPO_ROOT / "SECURITY.md",
    REPO_ROOT / ".github" / "ISSUE_TEMPLATE",
    REPO_ROOT / ".github" / "pull_request_template.md",
]

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private workspace link",
        re.compile(
            r"https?://(?:www\.)?(?:app\.notion\.com|notion\.so)/",
            re.IGNORECASE,
        ),
    ),
    (
        "private Microsoft storage link",
        re.compile(
            r"https?://[^\s)>\]]*(?:sharepoint\.com|1drv\.ms|onedrive\.live\.com)",
            re.IGNORECASE,
        ),
    ),
    (
        "raw ChatGPT conversation link",
        re.compile(r"https?://(?:www\.)?chatgpt\.com/(?:c|share)/", re.IGNORECASE),
    ),
    (
        "email address",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    (
        "UUID or tenant-style identifier",
        re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "internal hostname suffix",
        re.compile(r"\b[a-z0-9][a-z0-9.-]*\.(?:local|corp|internal)\b", re.IGNORECASE),
    ),
    (
        "Windows or UNC path",
        re.compile(r"(?:\b[A-Z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]*|\\\\[A-Z0-9_.-]+\\)", re.IGNORECASE),
    ),
    (
        "ticket-like identifier",
        re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d{3,}\b"),
    ),
)

PRIVATE_METADATA_KEYS = {
    "source_references",
    "private_sources",
    "notion_url",
    "conversation_id",
    "tenant_id",
    "employer",
}

IPV4_PATTERN = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
MIN_DENYLIST_TERM_LENGTH = 3


@dataclass(frozen=True)
class Finding:
    """A publication-boundary finding."""

    path: Path
    line: int
    rule: str
    excerpt: str

    def render(self) -> str:
        return f"{repo_relative(self.path)}:{self.line}: {self.rule}: {self.excerpt}"


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _excerpt(text: str, offset: int, length: int) -> str:
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset + length)
    if line_end == -1:
        line_end = len(text)
    value = text[line_start:line_end].strip()
    return value[:180]


def load_custom_denylist(raw: str | None = None) -> tuple[str, ...]:
    """Load unique literal terms without exposing them in scanner output."""

    if raw is None:
        raw = os.environ.get("PORTFOLIO_DENYLIST", "")

    terms: list[str] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        term = line.strip()
        if not term or term.startswith("#"):
            continue
        if len(term) < MIN_DENYLIST_TERM_LENGTH:
            continue
        normalized = term.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        terms.append(term)
    return tuple(terms)


def _scan_custom_terms(path: Path, text: str, terms: Iterable[str]) -> list[Finding]:
    """Find private literal terms while withholding their values from logs."""

    findings: list[Finding] = []
    folded_text = text.casefold()
    for term in terms:
        folded_term = term.casefold()
        offset = 0
        while True:
            match_offset = folded_text.find(folded_term, offset)
            if match_offset == -1:
                break
            findings.append(
                Finding(
                    path=path,
                    line=_line_number(text, match_offset),
                    rule="custom denylist term",
                    excerpt="[matched value withheld]",
                )
            )
            offset = match_offset + len(folded_term)
    return findings


def scan_text(
    path: Path,
    text: str,
    custom_terms: Iterable[str] = (),
) -> list[Finding]:
    """Scan one text value."""

    findings: list[Finding] = []
    for rule, pattern in PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                Finding(
                    path=path,
                    line=_line_number(text, match.start()),
                    rule=rule,
                    excerpt=_excerpt(text, match.start(), len(match.group(0))),
                )
            )

    for match in IPV4_PATTERN.finditer(text):
        try:
            address = ipaddress.ip_address(match.group(0))
        except ValueError:
            continue
        if address.is_private or address.is_loopback or address.is_link_local:
            findings.append(
                Finding(
                    path=path,
                    line=_line_number(text, match.start()),
                    rule="non-public IP address",
                    excerpt=_excerpt(text, match.start(), len(match.group(0))),
                )
            )

    for key in PRIVATE_METADATA_KEYS:
        pattern = re.compile(rf"(?im)^\s*{re.escape(key)}\s*:")
        for match in pattern.finditer(text):
            findings.append(
                Finding(
                    path=path,
                    line=_line_number(text, match.start()),
                    rule=f"private metadata key {key!r}",
                    excerpt=_excerpt(text, match.start(), len(match.group(0))),
                )
            )

    findings.extend(_scan_custom_terms(path, text, custom_terms))
    return findings


def scan_paths(
    paths: Iterable[Path],
    custom_terms: Iterable[str] = (),
) -> list[Finding]:
    """Scan all supported public files beneath paths."""

    findings: list[Finding] = []
    terms = tuple(custom_terms)
    for path in iter_files(paths):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(
                Finding(path=path, line=1, rule="non-UTF-8 public file", excerpt=path.name)
            )
            continue
        findings.extend(scan_text(path, text, custom_terms=terms))
    return sorted(findings, key=lambda item: (str(item.path), item.line, item.rule))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=PUBLIC_CONTENT_PATHS,
        help="Public prose and metadata roots to scan.",
    )
    args = parser.parse_args()

    custom_terms = load_custom_denylist()
    findings = scan_paths(args.paths, custom_terms=custom_terms)
    if findings:
        print("Public-content boundary scan failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding.render()}", file=sys.stderr)
        print(
            "\nA clean scan is necessary but not sufficient. Contextual human review is still required.",
            file=sys.stderr,
        )
        return 1

    print("Public-content boundary scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

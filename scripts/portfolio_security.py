"""Publication-boundary and repository-relative link checks."""

from __future__ import annotations

import os
import re
from pathlib import Path

from portfolio_common import ROOT

MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
SECURITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT-like token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    (
        "private IPv4 address",
        re.compile(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"),
    ),
    ("internal DNS suffix", re.compile(r"\b[a-z0-9][a-z0-9.-]*\.(?:corp|internal|local)\b", re.IGNORECASE)),
    ("tenant-specific cloud domain", re.compile(r"\b[a-z0-9-]+\.onmicrosoft\.com\b", re.IGNORECASE)),
    (
        "private SharePoint link",
        re.compile(r"https://[^\s)]+\.sharepoint\.com/(?:sites|personal)/[^\s)]*", re.IGNORECASE),
    ),
    (
        "private Notion page link",
        re.compile(r"https://(?:www\.|app\.)?notion\.(?:so|site|com)/[^\s)]*[0-9a-f]{24,}", re.IGNORECASE),
    ),
    ("raw ChatGPT conversation link", re.compile(r"https://(?:www\.)?chatgpt\.com/(?:c|share)/[^\s)]*", re.IGNORECASE)),
    ("UNC path", re.compile(r"(?<!`)\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9_$.-]+")),
    ("service-management record", re.compile(r"\b(?:INC|REQ|RITM|CHG|PRB)\d{5,}\b", re.IGNORECASE)),
    (
        "GUID",
        re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE),
    ),
    (
        "credential assignment",
        re.compile(
            r"\b(?:password|passwd|client[_ -]?secret|api[_ -]?key|access[_ -]?token)\s*[:=]\s*[\"']?(?!<|\$\{|\[)[A-Za-z0-9_./+=-]{8,}",
            re.IGNORECASE,
        ),
    ),
)


def scan_text(text: str, label: str) -> list[str]:
    """Scan public text for common secrets, identifiers, and private infrastructure."""

    findings: list[str] = []
    lines = text.splitlines()
    for finding_name, pattern in SECURITY_PATTERNS:
        for line_number, line in enumerate(lines, start=1):
            match = pattern.search(line)
            if match:
                excerpt = match.group(0)
                if len(excerpt) > 64:
                    excerpt = excerpt[:61] + "..."
                findings.append(f"{label}:{line_number}: possible {finding_name}: {excerpt!r}")

    denylist = [item.strip() for item in os.getenv("PORTFOLIO_DENYLIST", "").splitlines() if item.strip()]
    lowered = text.casefold()
    for term in denylist:
        if term.casefold() in lowered:
            findings.append(f"{label}: repository denylist term detected: {term!r}")
    return findings


def check_relative_links(path: Path, text: str) -> list[str]:
    """Validate that repository-relative Markdown links remain in the repo and resolve."""

    errors: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(text):
        target = raw_target.strip().split(" ", 1)[0].strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        target_without_fragment = target.split("#", 1)[0]
        if not target_without_fragment:
            continue
        resolved = (path.parent / target_without_fragment).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{path.relative_to(ROOT)}: relative link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{path.relative_to(ROOT)}: broken relative link: {target}")
    return errors

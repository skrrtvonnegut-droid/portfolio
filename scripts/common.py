"""Shared helpers for portfolio validation scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"
SCHEMA_PATH = REPO_ROOT / "schemas" / "portfolio-artifact.schema.json"
ARTIFACT_INDEX_PATH = DOCS_ROOT / "artifact-index.md"
ARTIFACT_DIRECTORIES = {
    "case-studies",
    "patterns",
    "projects",
    "learning",
    "methodology",
}
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".toml", ".txt", ".css"}


class FrontMatterError(ValueError):
    """Raised when a Markdown front-matter block cannot be parsed."""


@dataclass(frozen=True)
class MarkdownDocument:
    """Parsed Markdown file."""

    path: Path
    text: str
    metadata: dict[str, Any] | None
    body: str


def iter_files(paths: Iterable[Path], suffixes: set[str] | None = None) -> Iterable[Path]:
    """Yield files beneath paths in deterministic order."""

    allowed = suffixes or TEXT_SUFFIXES
    discovered: set[Path] = set()
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            candidates = [path]
        else:
            candidates = [candidate for candidate in path.rglob("*") if candidate.is_file()]
        for candidate in candidates:
            if candidate.suffix.lower() in allowed:
                discovered.add(candidate.resolve())
    yield from sorted(discovered)


def parse_markdown(path: Path) -> MarkdownDocument:
    """Read Markdown and parse optional YAML front matter."""

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return MarkdownDocument(path=path, text=text, metadata=None, body=text)

    lines = text.splitlines(keepends=True)
    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            closing_index = index
            break

    if closing_index is None:
        raise FrontMatterError(f"{path}: front matter starts but never closes")

    raw = "".join(lines[1:closing_index])
    try:
        metadata = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise FrontMatterError(f"{path}: invalid YAML front matter: {exc}") from exc

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise FrontMatterError(f"{path}: front matter must be a mapping")

    body = "".join(lines[closing_index + 1 :])
    return MarkdownDocument(path=path, text=text, metadata=metadata, body=body)


def is_artifact_location(path: Path, docs_root: Path = DOCS_ROOT) -> bool:
    """Return whether a Markdown path is expected to be a portfolio artifact."""

    try:
        relative = path.resolve().relative_to(docs_root.resolve())
    except ValueError:
        return False
    if relative.name in {"index.md", "artifact-index.md", "404.md"}:
        return False
    return bool(relative.parts and relative.parts[0] in ARTIFACT_DIRECTORIES)


def repo_relative(path: Path) -> str:
    """Return a repository-relative POSIX path when possible."""

    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()

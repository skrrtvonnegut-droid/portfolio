#!/usr/bin/env python3
"""Validate public portfolio artifacts and generate a machine-readable catalog."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
ARTIFACT_ROOT = DOCS_ROOT / "artifacts"
SCHEMA_PATH = ROOT / "schema" / "artifact.schema.json"
MANIFEST_PATH = ROOT / "portfolio.yml"
CONFIG_PATH = ROOT / "zensical.toml"
STYLE_PATH = DOCS_ROOT / "stylesheets" / "extra.css"
INDEX_PATH = DOCS_ROOT / "index.md"

MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")

SECURITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT-like token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    (
        "private IPv4 address",
        re.compile(
            r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
        ),
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
    ("UNC path", re.compile(r"(?<!`)\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9_$.-]+")),
    ("service-management record", re.compile(r"\b(?:INC|REQ|RITM|CHG|PRB)\d{5,}\b", re.IGNORECASE)),
    (
        "GUID",
        re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "credential assignment",
        re.compile(
            r"\b(?:password|passwd|client[_ -]?secret|api[_ -]?key|access[_ -]?token)\s*[:=]\s*[\"']?(?!<|\$\{|\[)[A-Za-z0-9_./+=-]{8,}",
            re.IGNORECASE,
        ),
    ),
)

PUBLISHABLE_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".toml", ".html", ".css", ".txt"}
IGNORED_PARTS = {".git", ".venv", "site", "__pycache__", ".pytest_cache"}


@dataclass(frozen=True)
class Artifact:
    path: Path
    relative_path: Path
    metadata: dict[str, Any]
    body: str


def normalize_yaml(value: Any) -> Any:
    """Convert PyYAML date objects into schema-friendly strings."""
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [normalize_yaml(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_yaml(item) for key, item in value.items()}
    return value


def parse_artifact(path: Path) -> Artifact:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML front matter delimiter")

    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing closing YAML front matter delimiter")

    metadata_text = text[4:end]
    body = text[end + 5 :].lstrip()
    loaded = yaml.safe_load(metadata_text)
    if not isinstance(loaded, dict):
        raise ValueError("front matter must be a YAML mapping")

    return Artifact(
        path=path,
        relative_path=path.relative_to(ROOT),
        metadata=normalize_yaml(loaded),
        body=body,
    )


def iter_artifact_paths() -> Iterable[Path]:
    if not ARTIFACT_ROOT.exists():
        return []
    return sorted(ARTIFACT_ROOT.rglob("*.md"))


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_artifacts() -> list[Artifact]:
    return [parse_artifact(path) for path in iter_artifact_paths()]


def public_text_paths() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLISHABLE_SUFFIXES:
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        if "scripts" in path.parts or "tests" in path.parts:
            continue
        yield path


def scan_text(text: str, label: str) -> list[str]:
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


def validate_config() -> list[str]:
    errors: list[str] = []
    try:
        config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"zensical.toml: invalid configuration: {exc}"]

    project = config.get("project")
    if not isinstance(project, dict):
        return ["zensical.toml: expected a [project] table"]

    if project.get("docs_dir") != "docs":
        errors.append("zensical.toml: project.docs_dir must be 'docs'")
    if project.get("site_dir") != "site":
        errors.append("zensical.toml: project.site_dir must be 'site'")
    if not isinstance(project.get("site_name"), str) or not project["site_name"].strip():
        errors.append("zensical.toml: project.site_name is required")
    if not isinstance(project.get("site_url"), str) or not project["site_url"].startswith("https://"):
        errors.append("zensical.toml: project.site_url must be an HTTPS URL")
    if not isinstance(project.get("nav"), list) or not project["nav"]:
        errors.append("zensical.toml: project.nav must define at least one page")
    return errors


def validate_repository() -> list[str]:
    errors: list[str] = []

    for required in (SCHEMA_PATH, MANIFEST_PATH, CONFIG_PATH, STYLE_PATH, INDEX_PATH):
        if not required.exists():
            errors.append(f"missing required file: {required.relative_to(ROOT)}")

    if (ROOT / "artifacts").exists():
        errors.append("legacy artifacts/ directory exists; public artifacts must live under docs/artifacts/")

    if errors:
        return errors

    errors.extend(validate_config())

    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    seen_ids: dict[str, Path] = {}
    artifacts: list[Artifact] = []

    for path in iter_artifact_paths():
        try:
            artifact = parse_artifact(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue

        artifacts.append(artifact)
        for issue in sorted(validator.iter_errors(artifact.metadata), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path) or "metadata"
            errors.append(f"{artifact.relative_path}: {location}: {issue.message}")

        artifact_id = str(artifact.metadata.get("id", ""))
        if artifact_id in seen_ids:
            errors.append(
                f"{artifact.relative_path}: duplicate id {artifact_id!r}; "
                f"first used by {seen_ids[artifact_id].relative_to(ROOT)}"
            )
        elif artifact_id:
            seen_ids[artifact_id] = path

        title = str(artifact.metadata.get("title", ""))
        if not artifact.body.startswith(f"# {title}\n"):
            errors.append(f"{artifact.relative_path}: first heading must exactly match metadata title")

        if len(artifact.body) < 1_200:
            errors.append(f"{artifact.relative_path}: body is too short to demonstrate a durable professional artifact")

        if "## What this demonstrates" not in artifact.body:
            errors.append(f"{artifact.relative_path}: missing 'What this demonstrates' section")

        disclosure = str(artifact.metadata.get("source_disclosure", ""))
        if "http://" in disclosure or "https://" in disclosure:
            errors.append(f"{artifact.relative_path}: source_disclosure must not contain a source URL")

        created = str(artifact.metadata.get("created", ""))
        updated = str(artifact.metadata.get("updated", ""))
        if created and updated and updated < created:
            errors.append(f"{artifact.relative_path}: updated date precedes created date")

        errors.extend(check_relative_links(path, artifact.body))

    if not artifacts:
        errors.append("no artifacts found under docs/artifacts/")

    for path in public_text_paths():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{path.relative_to(ROOT)}: publishable text file is not valid UTF-8")
            continue
        errors.extend(scan_text(text, str(path.relative_to(ROOT))))
        if path.suffix.lower() == ".md":
            errors.extend(check_relative_links(path, text))

    try:
        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("site"), dict):
            errors.append("portfolio.yml: expected a top-level 'site' mapping")
        if not isinstance(manifest, dict) or not isinstance(manifest.get("projects"), list):
            errors.append("portfolio.yml: expected a top-level 'projects' list")
    except yaml.YAMLError as exc:
        errors.append(f"portfolio.yml: invalid YAML: {exc}")

    return sorted(set(errors))


def catalog_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for artifact in sorted(load_artifacts(), key=lambda item: (item.metadata["domains"][0], item.metadata["title"])):
        page_path = artifact.path.relative_to(DOCS_ROOT).with_suffix("").as_posix() + "/"
        records.append({**artifact.metadata, "path": page_path})
    return records


def write_catalog(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog_records(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Validate metadata, links, privacy patterns, and repository structure")
    catalog_parser = subcommands.add_parser("catalog", help="Write a machine-readable artifact catalog")
    catalog_parser.add_argument("--output", type=Path, default=ROOT / "site" / "catalog.json")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return command_validate()
    if args.command == "catalog":
        return command_catalog(args.output)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

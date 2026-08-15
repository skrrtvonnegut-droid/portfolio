"""Shared models, paths, parsing, and configuration helpers."""

from __future__ import annotations

import datetime as dt
import json
import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = ROOT / "docs"
ARTIFACT_ROOT = DOCS_ROOT / "artifacts"
SCHEMA_PATH = ROOT / "schema" / "artifact.schema.json"
MANIFEST_PATH = ROOT / "portfolio.yml"
CONFIG_PATH = ROOT / "zensical.toml"
STYLE_PATH = DOCS_ROOT / "stylesheets" / "extra.css"
INDEX_PATH = DOCS_ROOT / "index.md"

GOVERNANCE_KEYS = {
    "id",
    "slug",
    "provenance",
    "authorship",
    "rights",
    "review",
    "featured",
}
PUBLISHABLE_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".toml", ".html", ".css", ".txt"}
IGNORED_PARTS = {".git", ".venv", "site", "__pycache__", ".pytest_cache", ".ruff_cache"}
LINK_ROOTS = (DOCS_ROOT, ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md")


@dataclass(frozen=True)
class Artifact:
    """One public artifact with merged content and governance metadata."""

    path: Path
    relative_path: Path
    metadata: dict[str, Any]
    body: str


@dataclass(frozen=True)
class LinkReference:
    """One external link and the public file that contains it."""

    path: Path
    line: int
    url: str


def normalize_yaml(value: Any) -> Any:
    """Convert PyYAML date objects into schema-friendly strings."""

    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [normalize_yaml(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize_yaml(item) for key, item in value.items()}
    return value


def load_manifest() -> dict[str, Any]:
    """Load the public site, project, and artifact-governance manifest."""

    loaded = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("portfolio.yml root must be a mapping")
    return normalize_yaml(loaded)


def governance_records(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Index public governance records by stable artifact ID."""

    errors: list[str] = []
    records = manifest.get("artifacts")
    if not isinstance(records, list):
        return {}, ["portfolio.yml: expected a top-level 'artifacts' list"]

    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        label = f"portfolio.yml:artifacts[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: entry must be a mapping")
            continue
        extra = set(record) - GOVERNANCE_KEYS
        missing = GOVERNANCE_KEYS - set(record)
        if extra:
            errors.append(f"{label}: unsupported keys: {', '.join(sorted(extra))}")
        if missing:
            errors.append(f"{label}: missing keys: {', '.join(sorted(missing))}")
        artifact_id = record.get("id")
        if not isinstance(artifact_id, str) or not artifact_id:
            errors.append(f"{label}.id: stable artifact ID is required")
            continue
        if artifact_id in indexed:
            errors.append(f"{label}.id: duplicate governance record {artifact_id!r}")
            continue
        indexed[artifact_id] = record
    return indexed, errors


def parse_artifact(path: Path, governance: dict[str, dict[str, Any]]) -> Artifact:
    """Parse an artifact and merge its public governance record."""

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML front matter delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing closing YAML front matter delimiter")

    loaded = yaml.safe_load(text[4:end])
    if not isinstance(loaded, dict):
        raise ValueError("front matter must be a YAML mapping")
    metadata = normalize_yaml(loaded)
    artifact_id = metadata.get("id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("front matter requires a stable artifact id")

    record = governance.get(artifact_id)
    if record is None:
        raise ValueError(f"missing public governance record in portfolio.yml for {artifact_id!r}")
    overlap = (set(metadata) & set(record)) - {"id"}
    if overlap:
        raise ValueError(
            "content front matter and governance manifest both define: "
            + ", ".join(sorted(overlap))
        )

    return Artifact(
        path=path,
        relative_path=path.relative_to(ROOT),
        metadata={**metadata, **record},
        body=text[end + 5 :].lstrip(),
    )


def iter_artifact_paths() -> Iterable[Path]:
    """Yield artifact Markdown files in deterministic order."""

    if not ARTIFACT_ROOT.exists():
        return []
    return sorted(ARTIFACT_ROOT.rglob("*.md"))


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_artifacts() -> list[Artifact]:
    manifest = load_manifest()
    governance, errors = governance_records(manifest)
    if errors:
        raise ValueError("; ".join(errors))
    return [parse_artifact(path, governance) for path in iter_artifact_paths()]


def public_text_paths() -> Iterable[Path]:
    """Yield text files that can influence the public repository or site."""

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLISHABLE_SUFFIXES:
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        if "scripts" in path.parts or "tests" in path.parts:
            continue
        yield path


def validate_config() -> list[str]:
    """Validate the minimum renderer configuration contract."""

    try:
        config = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"zensical.toml: invalid configuration: {exc}"]

    project = config.get("project")
    if not isinstance(project, dict):
        return ["zensical.toml: expected a [project] table"]

    errors: list[str] = []
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

    validation = project.get("validation")
    if not isinstance(validation, dict):
        errors.append("zensical.toml: expected [project.validation]")
    else:
        if validation.get("invalid_links") is not True:
            errors.append("zensical.toml: project.validation.invalid_links must be true")
        if validation.get("invalid_link_anchors") is not True:
            errors.append("zensical.toml: project.validation.invalid_link_anchors must be true")
    return errors


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Validate public profile and project manifest structure."""

    errors: list[str] = []
    if not isinstance(manifest.get("site"), dict):
        errors.append("portfolio.yml: expected a top-level 'site' mapping")

    projects = manifest.get("projects")
    if not isinstance(projects, list):
        return errors + ["portfolio.yml: expected a top-level 'projects' list"]

    seen_urls: set[str] = set()
    for index, project in enumerate(projects):
        label = f"portfolio.yml:projects[{index}]"
        if not isinstance(project, dict):
            errors.append(f"{label}: entry must be a mapping")
            continue
        for key in ("title", "url", "summary", "tags"):
            if key not in project:
                errors.append(f"{label}: missing {key!r}")
        url = project.get("url")
        valid_url = isinstance(url, str) and bool(
            re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", url)
        )
        if not valid_url:
            errors.append(f"{label}.url: must be a public GitHub repository URL")
        elif url in seen_urls:
            errors.append(f"{label}.url: duplicate project URL {url!r}")
        else:
            seen_urls.add(url)
    return errors

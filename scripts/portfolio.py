#!/usr/bin/env python3
"""Validate portfolio artifacts and build a dependency-light static site."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable

import jsonschema
import mistune
import yaml

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts"
SCHEMA_PATH = ROOT / "schema" / "artifact.schema.json"
MANIFEST_PATH = ROOT / "portfolio.yml"
STYLE_PATH = ROOT / "assets" / "style.css"

MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")

SECURITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT-like token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("email address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("private IPv4 address", re.compile(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b")),
    ("internal DNS suffix", re.compile(r"\b[a-z0-9][a-z0-9.-]*\.(?:corp|internal|local)\b", re.IGNORECASE)),
    ("tenant-specific cloud domain", re.compile(r"\b[a-z0-9-]+\.onmicrosoft\.com\b", re.IGNORECASE)),
    ("private SharePoint link", re.compile(r"https://[^\s)]+\.sharepoint\.com/(?:sites|personal)/[^\s)]*", re.IGNORECASE)),
    ("private Notion page link", re.compile(r"https://(?:www\.)?notion\.(?:so|site)/[^\s)]*[0-9a-f]{24,}", re.IGNORECASE)),
    ("UNC path", re.compile(r"(?<!`)\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9_$.-]+")),
    ("service-management record", re.compile(r"\b(?:INC|REQ|RITM|CHG|PRB)\d{5,}\b", re.IGNORECASE)),
    ("GUID", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE)),
    (
        "credential assignment",
        re.compile(
            r"\b(?:password|passwd|client[_ -]?secret|api[_ -]?key|access[_ -]?token)\s*[:=]\s*[\"']?(?!<|\$\{|\[)[A-Za-z0-9_./+=-]{8,}",
            re.IGNORECASE,
        ),
    ),
)

PUBLISHABLE_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".html", ".css"}
IGNORED_PARTS = {".git", "_site", ".venv", "__pycache__"}


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


def validate_repository() -> list[str]:
    errors: list[str] = []

    for required in (SCHEMA_PATH, MANIFEST_PATH, STYLE_PATH):
        if not required.exists():
            errors.append(f"missing required file: {required.relative_to(ROOT)}")

    if errors:
        return errors

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
                f"{artifact.relative_path}: duplicate id {artifact_id!r}; first used by {seen_ids[artifact_id].relative_to(ROOT)}"
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
        errors.append("no artifacts found under artifacts/")

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


def load_artifacts() -> list[Artifact]:
    return [parse_artifact(path) for path in iter_artifact_paths()]


def page_frame(*, title: str, body: str, root_prefix: str = "", description: str = "") -> str:
    safe_title = html.escape(title)
    safe_description = html.escape(description or title, quote=True)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <meta name=\"description\" content=\"{safe_description}\">
  <title>{safe_title}</title>
  <link rel=\"stylesheet\" href=\"{root_prefix}assets/style.css\">
</head>
<body>
  <header class=\"site-header\">
    <div class=\"shell\">
      <a class=\"brand\" href=\"{root_prefix}index.html\">Breezy Lynne</a>
      <nav class=\"nav\" aria-label=\"Primary\">
        <a href=\"{root_prefix}index.html#artifacts\">Artifacts</a>
        <a href=\"{root_prefix}index.html#projects\">Projects</a>
        <a href=\"https://github.com/skrrtvonnegut-droid/portfolio\">Repository</a>
      </nav>
    </div>
  </header>
  {body}
  <footer class=\"site-footer\">
    <div class=\"shell\">A living, review-gated professional portfolio. Private source material remains outside this public repository.</div>
  </footer>
</body>
</html>
"""


def chip_list(items: Iterable[str]) -> str:
    return "".join(f'<span class="chip">{html.escape(str(item))}</span>' for item in items)


def build_site(output: Path) -> None:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    site = manifest["site"]
    projects = manifest["projects"]
    artifacts = sorted(load_artifacts(), key=lambda item: (item.metadata["domains"][0], item.metadata["title"]))

    if output.exists():
        shutil.rmtree(output)
    (output / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(STYLE_PATH, output / "assets" / "style.css")
    (output / ".nojekyll").write_text("", encoding="utf-8")

    artifact_cards: list[str] = []
    catalog: list[dict[str, Any]] = []
    markdown = mistune.create_markdown(escape=False, plugins=["strikethrough", "table", "task_lists", "url"])

    for artifact in artifacts:
        relative_source = artifact.path.relative_to(ARTIFACT_ROOT)
        destination = output / "artifacts" / relative_source.with_suffix(".html")
        destination.parent.mkdir(parents=True, exist_ok=True)
        root_prefix = "../" * len(destination.parent.relative_to(output).parts)

        metadata = artifact.metadata
        rendered = markdown(artifact.body)
        article = f"""
<main class=\"article-shell\">
  <p class=\"eyebrow\">{html.escape(metadata['artifact_type'].replace('-', ' '))}</p>
  <h1 class=\"article-title\">{html.escape(metadata['title'])}</h1>
  <p class=\"article-summary\">{html.escape(metadata['summary'])}</p>
  <div class=\"article-meta chips\">{chip_list(metadata['domains'])}{chip_list(metadata['skills'])}</div>
  <p class=\"notice\"><strong>Source boundary:</strong> {html.escape(metadata['source_disclosure'])}</p>
  <article class=\"article-body\">{rendered}</article>
</main>
"""
        destination.write_text(
            page_frame(
                title=f"{metadata['title']} — Breezy Lynne",
                body=article,
                root_prefix=root_prefix,
                description=metadata["summary"],
            ),
            encoding="utf-8",
        )

        web_path = destination.relative_to(output).as_posix()
        artifact_cards.append(
            f"""
<article class=\"card\">
  <p class=\"eyebrow\">{html.escape(metadata['domains'][0].replace('-', ' '))}</p>
  <a class=\"card-link\" href=\"{html.escape(web_path)}\"><h3>{html.escape(metadata['title'])}</h3></a>
  <p>{html.escape(metadata['summary'])}</p>
  <div class=\"chips\">{chip_list(metadata['skills'][:4])}</div>
</article>
"""
        )
        catalog.append({**metadata, "path": web_path})

    project_cards = "".join(
        f"""
<article class=\"card\">
  <p class=\"eyebrow\">Open-source project</p>
  <a class=\"card-link\" href=\"{html.escape(project['url'], quote=True)}\"><h3>{html.escape(project['title'])}</h3></a>
  <p>{html.escape(project['summary'])}</p>
  <div class=\"chips\">{chip_list(project.get('tags', []))}</div>
</article>
"""
        for project in projects
    )

    principles = "".join(f"<li>{html.escape(item)}</li>" for item in site.get("principles", []))
    index_body = f"""
<main>
  <section class=\"hero\">
    <div class=\"shell\">
      <p class=\"eyebrow\">Systems administration · identity · automation</p>
      <h1>{html.escape(site['short_title'])}</h1>
      <p class=\"lede\">{html.escape(site['description'])}</p>
      <div class=\"actions\">
        <a class=\"button primary\" href=\"#artifacts\">Explore artifacts</a>
        <a class=\"button secondary\" href=\"{html.escape(site['profile_url'], quote=True)}\">GitHub profile</a>
      </div>
    </div>
  </section>
  <section>
    <div class=\"shell\">
      <h2>Operating principles</h2>
      <ul class=\"principles\">{principles}</ul>
    </div>
  </section>
  <section id=\"artifacts\">
    <div class=\"shell\">
      <p class=\"eyebrow\">Sanitized professional evidence</p>
      <h2>Artifacts</h2>
      <p class=\"lede\">Reconstructed case studies, operating patterns, and technical systems. The transferable reasoning remains; private environments do not.</p>
      <div class=\"grid\">{''.join(artifact_cards)}</div>
    </div>
  </section>
  <section id=\"projects\">
    <div class=\"shell\">
      <p class=\"eyebrow\">Public repositories</p>
      <h2>Featured projects</h2>
      <div class=\"grid\">{project_cards}</div>
    </div>
  </section>
</main>
"""
    (output / "index.html").write_text(
        page_frame(title=site["title"], body=index_body, description=site["description"]),
        encoding="utf-8",
    )
    (output / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def command_validate() -> int:
    errors = validate_repository()
    if errors:
        print("Portfolio validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"Portfolio validation passed: {len(list(iter_artifact_paths()))} artifacts checked.")
    return 0


def command_build(output: Path) -> int:
    errors = validate_repository()
    if errors:
        print("Build blocked by validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    build_site(output)
    print(f"Built static portfolio at {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate", help="Validate metadata, links, privacy patterns, and repository structure")
    build_parser = subcommands.add_parser("build", help="Build the static portfolio site")
    build_parser.add_argument("--output", type=Path, default=ROOT / "_site")
    subcommands.add_parser("check", help="Run validation, tests, and a temporary site build")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return command_validate()
    if args.command == "build":
        return command_build(args.output)
    if args.command == "check":
        result = command_validate()
        if result:
            return result
        with TemporaryDirectory(prefix="portfolio-build-") as directory:
            build_site(Path(directory))
        print("Temporary site build passed.")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

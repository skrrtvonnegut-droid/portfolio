#!/usr/bin/env python3
"""Validate the public project-card registry."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.common import REPO_ROOT, repo_relative

PROJECTS_PATH = REPO_ROOT / "data" / "projects.yml"
GITHUB_REPOSITORY = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROVENANCE = {"original", "ai-assisted-original", "adapted", "external-reference"}


def validate_registry(path: Path = PROJECTS_PATH) -> list[str]:
    """Validate public project metadata."""

    errors: list[str] = []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{repo_relative(path)}: cannot read registry: {exc}"]

    if not isinstance(payload, dict):
        return [f"{repo_relative(path)}: root must be a mapping"]
    if payload.get("schema_version") != 1:
        errors.append(f"{repo_relative(path)}: schema_version must be 1")

    projects = payload.get("projects")
    if not isinstance(projects, list):
        return errors + [f"{repo_relative(path)}: projects must be a list"]

    seen_ids: set[str] = set()
    for index, project in enumerate(projects):
        prefix = f"{repo_relative(path)}:projects[{index}]"
        if not isinstance(project, dict):
            errors.append(f"{prefix}: entry must be a mapping")
            continue

        required = {"id", "title", "summary", "repository_url", "provenance", "status"}
        missing = sorted(required - set(project))
        if missing:
            errors.append(f"{prefix}: missing {', '.join(missing)}")
            continue

        project_id = project["id"]
        if not isinstance(project_id, str) or not ID_PATTERN.fullmatch(project_id):
            errors.append(f"{prefix}.id: must be a lowercase hyphenated identifier")
        elif project_id in seen_ids:
            errors.append(f"{prefix}.id: duplicate value {project_id!r}")
        else:
            seen_ids.add(project_id)

        if not isinstance(project["title"], str) or len(project["title"].strip()) < 3:
            errors.append(f"{prefix}.title: must be a descriptive string")
        if not isinstance(project["summary"], str) or len(project["summary"].strip()) < 20:
            errors.append(f"{prefix}.summary: must contain at least 20 characters")
        if not isinstance(project["repository_url"], str) or not GITHUB_REPOSITORY.fullmatch(
            project["repository_url"]
        ):
            errors.append(f"{prefix}.repository_url: must be a public GitHub repository URL")
        if project["provenance"] not in PROVENANCE:
            errors.append(f"{prefix}.provenance: unsupported value")
        if project["status"] not in {"active", "maintenance", "archived", "experimental"}:
            errors.append(f"{prefix}.status: unsupported value")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=PROJECTS_PATH)
    args = parser.parse_args()

    errors = validate_registry(args.path)
    if errors:
        print("Project registry validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Project registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

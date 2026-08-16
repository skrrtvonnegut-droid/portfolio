"""Validate the living resume architecture scaffold."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_resume_scaffold_matches_schema() -> None:
    schema = json.loads(
        (REPO_ROOT / "schemas" / "resume.schema.json").read_text(encoding="utf-8")
    )
    payload = yaml.safe_load((REPO_ROOT / "data" / "resume.yml").read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    assert errors == []


def test_both_templates_use_one_shared_semantic_body() -> None:
    for name in ("resume-stylized.md", "resume-plain.md"):
        text = (REPO_ROOT / "templates" / name).read_text(encoding="utf-8")
        assert text.count("{{ semantic_resume_body }}") == 1
        assert "data-resume-content-hash" in text

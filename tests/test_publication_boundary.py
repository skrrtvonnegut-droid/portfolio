"""Regression tests for the public/private portfolio membrane."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import yaml

from scripts.build_artifact_index import render_index
from scripts.check_review_dates import find_overdue
from scripts.scan_public_content import load_custom_denylist, scan_text
from scripts.validate_frontmatter import load_validator, validate_metadata
from scripts.verify_projects import validate_registry


def valid_metadata() -> dict:
    return {
        "id": "portfolio.identity.synthetic-example",
        "slug": "/case-studies/identity/synthetic-example/",
        "kind": "case-study",
        "title": "Synthetic identity governance example",
        "summary": "A synthetic artifact used to verify the public portfolio metadata contract.",
        "status": "published",
        "classification": "professional-portfolio",
        "provenance": "ai-assisted-original",
        "authorship": "breezy-lynne",
        "domains": ["identity", "security"],
        "skills": ["risk-modeling", "technical-writing"],
        "rights": {
            "publishable": True,
            "attribution": None,
            "source_url": None,
        },
        "review": {
            "last_reviewed": "2026-08-15",
            "review_due": "2027-02-15",
        },
        "featured": False,
    }


def test_valid_metadata_passes(tmp_path: Path) -> None:
    path = tmp_path / "artifact.md"
    errors = validate_metadata(valid_metadata(), path=path, validator=load_validator())
    assert errors == []


def test_kind_prefixed_legacy_id_is_rejected(tmp_path: Path) -> None:
    metadata = valid_metadata()
    metadata["id"] = "portfolio.case-study.identity.synthetic-example"
    path = tmp_path / "artifact.md"
    errors = validate_metadata(metadata, path=path, validator=load_validator())
    assert any("does not match" in error for error in errors)


def test_adapted_artifact_requires_attribution(tmp_path: Path) -> None:
    metadata = valid_metadata()
    metadata["provenance"] = "adapted"
    path = tmp_path / "artifact.md"
    errors = validate_metadata(metadata, path=path, validator=load_validator())
    assert any("rights.attribution" in error for error in errors)
    assert any("rights.source_url" in error for error in errors)


def test_review_due_cannot_precede_reviewed_date(tmp_path: Path) -> None:
    metadata = valid_metadata()
    metadata["review"]["review_due"] = "2026-01-01"
    path = tmp_path / "artifact.md"
    errors = validate_metadata(metadata, path=path, validator=load_validator())
    assert any("cannot precede" in error for error in errors)


def test_scanner_rejects_private_workspace_link(tmp_path: Path) -> None:
    private_url = "https://app." + "notion.com/private-page"
    findings = scan_text(tmp_path / "page.md", f"# Example\n\n{private_url}\n")
    assert any(finding.rule == "private workspace link" for finding in findings)


def test_scanner_rejects_email_address(tmp_path: Path) -> None:
    address = "person" + "@" + "example.com"
    findings = scan_text(tmp_path / "page.md", f"# Example\n\n{address}\n")
    assert any(finding.rule == "email address" for finding in findings)


def test_scanner_rejects_private_metadata_key(tmp_path: Path) -> None:
    findings = scan_text(tmp_path / "page.md", "# Example\n\nsource_references: hidden\n")
    assert any("private metadata key" in finding.rule for finding in findings)


def test_scanner_rejects_custom_term_without_disclosing_it(tmp_path: Path) -> None:
    private_term = "SyntheticInternalName"
    findings = scan_text(
        tmp_path / "page.md",
        f"# Example\n\nA reference to {private_term.lower()} appears here.\n",
        custom_terms=(private_term,),
    )
    matches = [finding for finding in findings if finding.rule == "custom denylist term"]
    assert len(matches) == 1
    assert private_term.casefold() not in matches[0].render().casefold()
    assert matches[0].excerpt == "[matched value withheld]"


def test_denylist_loader_normalizes_comments_and_duplicates() -> None:
    raw = "# private terms\nInternalName\ninternalname\nxy\n\nProject Cedar\n"
    assert load_custom_denylist(raw) == ("InternalName", "Project Cedar")


def test_scanner_allows_public_github_repository(tmp_path: Path) -> None:
    text = "# Example\n\nhttps://github.com/example/public-repository\n"
    assert scan_text(tmp_path / "page.md", text) == []


def test_empty_artifact_index_is_deterministic() -> None:
    rendered = render_index([])
    assert "No portfolio artifacts have been published yet." in rendered
    assert rendered.endswith("\n")


def test_overdue_artifact_is_detected(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    path = docs / "case-studies" / "synthetic.md"
    path.parent.mkdir(parents=True)
    metadata = valid_metadata()
    metadata["review"]["last_reviewed"] = "2026-01-01"
    metadata["review"]["review_due"] = "2026-08-14"
    path.write_text(
        "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n# Synthetic\n",
        encoding="utf-8",
    )
    overdue, errors = find_overdue(date(2026, 8, 15), [docs])
    assert errors == []
    assert len(overdue) == 1


def test_empty_project_registry_passes(tmp_path: Path) -> None:
    path = tmp_path / "projects.yml"
    path.write_text("schema_version: 1\nprojects: []\n", encoding="utf-8")
    assert validate_registry(path) == []


def test_schema_file_is_valid_json() -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "portfolio-artifact.schema.json"
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    assert payload["$schema"].endswith("2020-12/schema")

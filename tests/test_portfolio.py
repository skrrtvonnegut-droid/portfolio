from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("portfolio_pipeline", ROOT / "scripts" / "portfolio.py")
assert SPEC and SPEC.loader
portfolio = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = portfolio
SPEC.loader.exec_module(portfolio)


class PortfolioPipelineTests(unittest.TestCase):
    def test_repository_validates(self) -> None:
        self.assertEqual([], portfolio.validate_repository())

    def test_sensitive_private_ip_is_detected(self) -> None:
        findings = portfolio.scan_text("Synthetic fixture at 10.20.30.40", "fixture")
        self.assertTrue(any("private IPv4" in finding for finding in findings))

    def test_private_workspace_link_is_detected(self) -> None:
        url = "https://app.notion.com/example" + "1234567890abcdef12345678"
        findings = portfolio.scan_text(url, "fixture")
        self.assertTrue(any("private Notion" in finding for finding in findings))

    def test_email_address_is_detected(self) -> None:
        address = "person" + "@" + "example.com"
        findings = portfolio.scan_text(address, "fixture")
        self.assertTrue(any("email address" in finding for finding in findings))

    def test_public_github_repository_is_allowed(self) -> None:
        text = "https://github.com/example/public-repository"
        self.assertEqual([], portfolio.scan_text(text, "fixture"))

    def test_artifact_ids_and_slugs_are_unique(self) -> None:
        artifacts = portfolio.load_artifacts()
        ids = [artifact.metadata["id"] for artifact in artifacts]
        slugs = [artifact.metadata["slug"] for artifact in artifacts]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_catalog_contains_governance_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.json"
            portfolio.write_catalog(output)
            records = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(5, len(records))
            self.assertTrue(all(record["id"].startswith("portfolio.") for record in records))
            self.assertTrue(all(record["slug"].startswith("/artifacts/") for record in records))
            self.assertTrue(all("provenance" in record for record in records))
            self.assertTrue(all("review" in record for record in records))

    def test_adapted_artifact_requires_attribution_and_source(self) -> None:
        metadata = {
            "provenance": "adapted",
            "rights": {
                "publishable": True,
                "attribution": None,
                "source_url": None,
            },
            "review": {
                "last_reviewed": "2026-08-15",
                "review_due": "2027-02-15",
            },
        }
        errors = portfolio.validate_artifact_semantics(metadata, "fixture")
        self.assertTrue(any("rights.attribution" in error for error in errors))
        self.assertTrue(any("rights.source_url" in error for error in errors))

    def test_review_due_cannot_precede_last_reviewed(self) -> None:
        metadata = {
            "provenance": "original",
            "rights": {
                "publishable": True,
                "attribution": None,
                "source_url": None,
            },
            "review": {
                "last_reviewed": "2026-08-15",
                "review_due": "2026-08-14",
            },
        }
        errors = portfolio.validate_artifact_semantics(metadata, "fixture")
        self.assertTrue(any("review_due cannot precede" in error for error in errors))

    def test_overdue_active_artifact_is_detected(self) -> None:
        artifact = portfolio.Artifact(
            path=ROOT / "docs" / "artifacts" / "synthetic.md",
            relative_path=Path("docs/artifacts/synthetic.md"),
            metadata={
                "id": "portfolio.test.synthetic",
                "status": "active",
                "review": {
                    "last_reviewed": "2026-01-01",
                    "review_due": "2026-08-14",
                },
            },
            body="# Synthetic\n",
        )
        overdue = portfolio.find_overdue_reviews(dt.date(2026, 8, 15), [artifact])
        self.assertEqual(1, len(overdue))

    def test_archived_artifact_is_not_overdue(self) -> None:
        artifact = portfolio.Artifact(
            path=ROOT / "docs" / "artifacts" / "synthetic.md",
            relative_path=Path("docs/artifacts/synthetic.md"),
            metadata={
                "id": "portfolio.test.synthetic",
                "status": "archived",
                "review": {
                    "last_reviewed": "2025-01-01",
                    "review_due": "2025-02-01",
                },
            },
            body="# Synthetic\n",
        )
        self.assertEqual([], portfolio.find_overdue_reviews(dt.date(2026, 8, 15), [artifact]))

    def test_malformed_external_url_fails(self) -> None:
        valid, message = portfolio.validate_external_url("not-a-url", attempts=1, timeout=0.1)
        self.assertFalse(valid)
        self.assertEqual("malformed URL", message)


if __name__ == "__main__":
    unittest.main()

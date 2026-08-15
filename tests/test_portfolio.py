from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portfolio_pipeline", ROOT / "scripts" / "portfolio.py")
assert SPEC and SPEC.loader
portfolio = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = portfolio
SPEC.loader.exec_module(portfolio)


class PortfolioPipelineTests(unittest.TestCase):
    def test_repository_validates(self) -> None:
        self.assertEqual([], portfolio.validate_repository())

    def test_sensitive_fixture_is_detected(self) -> None:
        findings = portfolio.scan_text("Synthetic fixture at 10.20.30.40", "fixture")
        self.assertTrue(any("private IPv4" in finding for finding in findings))

    def test_artifact_ids_are_unique(self) -> None:
        artifacts = portfolio.load_artifacts()
        ids = [artifact.metadata["id"] for artifact in artifacts]
        self.assertEqual(len(ids), len(set(ids)))

    def test_catalog_is_generated_from_artifact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.json"
            portfolio.write_catalog(output)
            records = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(5, len(records))
            self.assertTrue(all(record["id"].startswith("portfolio.") for record in records))
            self.assertTrue(all(record["path"].endswith("/") for record in records))


if __name__ == "__main__":
    unittest.main()

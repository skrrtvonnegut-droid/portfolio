from __future__ import annotations

import importlib.util
import tempfile
import unittest
import sys
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

    def test_site_build_contains_index_and_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            portfolio.build_site(output)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "catalog.json").is_file())
            self.assertTrue((output / "assets" / "style.css").is_file())

    def test_sensitive_fixture_is_detected(self) -> None:
        findings = portfolio.scan_text("Synthetic fixture at 10.20.30.40", "fixture")
        self.assertTrue(any("private IPv4" in finding for finding in findings))

    def test_artifact_ids_are_unique(self) -> None:
        artifacts = portfolio.load_artifacts()
        ids = [artifact.metadata["id"] for artifact in artifacts]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()

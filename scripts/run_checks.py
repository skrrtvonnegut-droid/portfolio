#!/usr/bin/env python3
"""Run the local publication checks in the same order as CI."""

from __future__ import annotations

import shutil
import subprocess
import sys

COMMANDS = [
    [sys.executable, "-m", "scripts.lint_markdown", "docs", "templates"],
    [sys.executable, "-m", "scripts.validate_frontmatter", "docs"],
    [sys.executable, "-m", "scripts.scan_public_content"],
    [sys.executable, "-m", "scripts.verify_projects"],
    [sys.executable, "-m", "scripts.build_artifact_index", "--check"],
    [sys.executable, "-m", "scripts.check_review_dates"],
    [sys.executable, "-m", "scripts.check_links", "docs", "README.md", "CONTRIBUTING.md", "SECURITY.md"],
    [sys.executable, "-m", "pytest"],
]


def main() -> int:
    for command in COMMANDS:
        print(f"\n$ {' '.join(command)}", flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            return completed.returncode

    if shutil.which("ruff"):
        print("\n$ ruff check scripts tests", flush=True)
        completed = subprocess.run(["ruff", "check", "scripts", "tests"], check=False)
        if completed.returncode:
            return completed.returncode

    if shutil.which("zensical"):
        print("\n$ zensical build --clean --strict", flush=True)
        completed = subprocess.run(["zensical", "build", "--clean", "--strict"], check=False)
        if completed.returncode:
            return completed.returncode
    else:
        print("\nZensical is not installed; site build skipped locally.")

    print("\nAll available checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

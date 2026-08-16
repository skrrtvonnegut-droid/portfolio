"""Protect the resume's one-source, two-render publication contract."""

from __future__ import annotations

import json
from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path

import pytest

from scripts.build_resume import (
    DATA_PATH,
    SCHEMA_PATH,
    SEMANTIC_END,
    SEMANTIC_START,
    TEMPLATE_PATHS,
    ResumeError,
    check_outputs,
    compute_content_hash,
    extract_semantic_region,
    load_resume,
    render_outputs,
    render_semantic_body,
    validate_resume,
)


class TextExtractor(HTMLParser):
    """Collect normalized visible text for copy-and-ATS regression checks."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_data(self, data: str) -> None:
        self.values.append(data)


@pytest.fixture
def schema() -> dict[str, object]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def approved_resume() -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "resume_id": "portfolio.resume.canonical",
        "release": {
            "state": "approved",
            "version": "resume-2026-08-15",
            "approved_at": "2026-08-15T12:00:00-07:00",
            "content_hash": "0" * 64,
        },
        "basics": {
            "name": "Sample & Candidate",
            "headline": "Example Headline",
            "location": "Example Region",
            "links": [
                {
                    "id": "sample-profile",
                    "label": "example.com/profile",
                    "url": "https://example.com/profile?view=public&from=sample",
                }
            ],
        },
        "summary": ["Synthetic summary text for deterministic renderer tests."],
        "skills": [
            {
                "id": "category-b",
                "label": "Category B",
                "order": 20,
                "items": ["Sample skill B1", "Sample skill B2"],
            },
            {
                "id": "category-a",
                "label": "Category & A",
                "order": 10,
                "items": ["Sample skill A1"],
            },
        ],
        "experience": [
            {
                "id": "example-role",
                "order": 10,
                "role": "Example Role",
                "organization": "Example Organization",
                "location": "Example Location",
                "start": "2023-02",
                "end": None,
                "current": True,
                "highlights": ["Synthetic accomplishment for renderer testing."],
            }
        ],
        "education": [
            {
                "id": "example-credential",
                "order": 10,
                "credential": "Example Credential",
                "institution": "Example Institution",
                "location": None,
                "start": "2013",
                "end": "2017",
            }
        ],
    }
    payload["release"]["content_hash"] = compute_content_hash(payload)  # type: ignore[index]
    return payload


def test_repository_snapshot_validates(schema: dict[str, object]) -> None:
    payload = load_resume(DATA_PATH)
    assert validate_resume(payload, schema) == []


def test_tracked_pages_match_renderer_and_share_exact_content() -> None:
    outputs = render_outputs(load_resume(DATA_PATH))
    assert check_outputs(outputs) == []

    rendered = list(outputs.values())
    assert len(rendered) == 2
    assert extract_semantic_region(rendered[0]) == extract_semantic_region(rendered[1])
    for text in rendered:
        assert text.count(SEMANTIC_START) == 1
        assert text.count(SEMANTIC_END) == 1
        assert text.count("<h1 ") == 1
        assert 'data-resume-content-hash="scaffold"' in text


def test_templates_expose_only_the_fixed_contract() -> None:
    allowed = {
        "{{ release.state }}",
        "{{ release.version }}",
        "{{ release.content_hash }}",
        "{{ semantic_resume_body }}",
    }
    for path in TEMPLATE_PATHS.values():
        text = path.read_text(encoding="utf-8")
        for token in allowed:
            assert text.count(token) == 1
        assert text.count("{{") == len(allowed)


def test_hash_ignores_release_metadata_but_tracks_content(
    approved_resume: dict[str, object],
) -> None:
    original = compute_content_hash(approved_resume)

    metadata_edit = deepcopy(approved_resume)
    metadata_edit["release"]["version"] = "resume-2026-08-15.2"  # type: ignore[index]
    metadata_edit["release"]["approved_at"] = "2026-08-16T09:00:00-07:00"  # type: ignore[index]
    assert compute_content_hash(metadata_edit) == original

    content_edit = deepcopy(approved_resume)
    content_edit["summary"][0] += " Reliably."  # type: ignore[index]
    assert compute_content_hash(content_edit) != original


def test_explicit_order_normalizes_source_list_order(
    approved_resume: dict[str, object],
) -> None:
    reordered = deepcopy(approved_resume)
    reordered["skills"].reverse()  # type: ignore[union-attr]
    assert compute_content_hash(reordered) == compute_content_hash(approved_resume)


def test_approved_fixture_validates_and_escapes_html(
    approved_resume: dict[str, object],
    schema: dict[str, object],
) -> None:
    assert validate_resume(approved_resume, schema) == []
    body = render_semantic_body(approved_resume)
    assert "Sample &amp; Candidate" in body
    assert "Category &amp; A" in body
    assert "public&amp;from" in body
    assert '<time datetime="2023-02">Feb 2023</time>' in body
    parser = TextExtractor()
    parser.feed(body)
    plain_text = " ".join("".join(parser.values).split())
    assert "Example Location Feb 2023 – Present" in plain_text


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda item: item["skills"].__setitem__(1, deepcopy(item["skills"][0])), "stable IDs"),
        (lambda item: item["skills"][1].__setitem__("order", 20), "order values"),
        (lambda item: item["experience"][0].__setitem__("end", "2024-01"), "experience.0.end"),
        (lambda item: item["education"][0].__setitem__("end", "2012"), "end date"),
        (lambda item: item["summary"].__setitem__(0, " padded "), "whitespace"),
    ],
)
def test_semantic_invariants_reject_ambiguous_content(
    approved_resume: dict[str, object],
    schema: dict[str, object],
    mutation: object,
    expected: str,
) -> None:
    payload = deepcopy(approved_resume)
    mutation(payload)  # type: ignore[operator]
    errors = validate_resume(payload, schema)
    assert any(expected in error for error in errors)


def test_hash_mismatch_and_scaffold_content_are_rejected(
    approved_resume: dict[str, object],
    schema: dict[str, object],
) -> None:
    mismatch = deepcopy(approved_resume)
    mismatch["summary"][0] += " Changed."  # type: ignore[index]
    assert any("content_hash" in error for error in validate_resume(mismatch, schema))

    scaffold = load_resume(DATA_PATH)
    scaffold["summary"] = ["Not approved."]
    assert validate_resume(scaffold, schema)


def test_duplicate_yaml_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "resume.yml"
    path.write_text("schema_version: 1\nschema_version: 1\n", encoding="utf-8")
    with pytest.raises(ResumeError, match="duplicate mapping key"):
        load_resume(path)


def test_check_mode_reports_stale_path_without_writing(tmp_path: Path) -> None:
    path = tmp_path / "generated.md"
    path.write_text("old\n", encoding="utf-8")
    assert check_outputs({path: "new\n"}) == [path.as_posix()]
    assert path.read_text(encoding="utf-8") == "old\n"

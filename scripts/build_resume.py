#!/usr/bin/env python3
"""Validate and deterministically render the public resume snapshot."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from scripts.common import REPO_ROOT, repo_relative

DATA_PATH = REPO_ROOT / "data" / "resume.yml"
SCHEMA_PATH = REPO_ROOT / "schemas" / "resume.schema.json"
TEMPLATE_PATHS = {
    REPO_ROOT / "docs" / "resume" / "index.md": REPO_ROOT
    / "templates"
    / "resume-stylized.md",
    REPO_ROOT / "docs" / "resume" / "plain.md": REPO_ROOT
    / "templates"
    / "resume-plain.md",
}
ORDERED_COLLECTIONS = ("skills", "experience", "education")
SEMANTIC_START = "<!-- resume-semantic-body:start -->"
SEMANTIC_END = "<!-- resume-semantic-body:end -->"
TOKEN_PATTERN = re.compile(r"{{\s*([a-z0-9_.]+)\s*}}")
CONTROL_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
MONTHS = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
ALLOWED_SHELL_TEXT = ("Styled", "Plain / ATS-friendly")


class ResumeError(ValueError):
    """Raised when the resume source cannot be safely processed."""


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ResumeError("resume source contains a duplicate mapping key")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_resume(path: Path = DATA_PATH) -> dict[str, Any]:
    """Load a resume YAML mapping without accepting duplicate keys."""

    try:
        payload = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except ResumeError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ResumeError("resume source could not be read as UTF-8 YAML") from exc
    if not isinstance(payload, dict):
        raise ResumeError("resume source root must be a mapping")
    return payload


def load_schema(path: Path = SCHEMA_PATH) -> dict[str, Any]:
    """Load the resume JSON Schema."""

    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ResumeError("resume schema could not be read as JSON") from exc
    if not isinstance(schema, dict):
        raise ResumeError("resume schema root must be an object")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ResumeError("resume schema is invalid") from exc
    return schema


def _path_label(parts: Iterable[object]) -> str:
    values = [str(part) for part in parts]
    return ".".join(values) if values else "<root>"


def _walk_strings(value: Any, path: tuple[object, ...] = ()) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield _path_label(path), value
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk_strings(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, (*path, index))


def _date_bounds(value: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if len(value) == 4:
        year = int(value)
        return (year, 1), (year, 12)
    year, month = (int(part) for part in value.split("-"))
    return (year, month), (year, month)


def _ordered_records(payload: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    records = payload.get(key, [])
    if not isinstance(records, list):
        return []
    return sorted(records, key=lambda record: record.get("order", -1))


def canonical_content(payload: Mapping[str, Any]) -> bytes:
    """Return canonical semantic JSON bytes, excluding recursive release metadata."""

    canonical = {
        "schema_version": payload["schema_version"],
        "resume_id": payload["resume_id"],
        "basics": deepcopy(payload["basics"]),
        "summary": deepcopy(payload["summary"]),
        "skills": deepcopy(_ordered_records(payload, "skills")),
        "experience": deepcopy(_ordered_records(payload, "experience")),
        "education": deepcopy(_ordered_records(payload, "education")),
    }
    return json.dumps(
        canonical,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def compute_content_hash(payload: Mapping[str, Any]) -> str:
    """Compute the approval hash for canonical public content."""

    return hashlib.sha256(canonical_content(payload)).hexdigest()


def validate_resume(
    payload: Mapping[str, Any],
    schema: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return schema and semantic validation errors without echoing source values."""

    selected_schema = schema or load_schema()
    validator = Draft202012Validator(selected_schema, format_checker=FormatChecker())
    errors = [
        f"{_path_label(error.absolute_path)}: failed {error.validator} validation"
        for error in sorted(
            validator.iter_errors(payload),
            key=lambda item: (list(item.absolute_path), str(item.validator)),
        )
    ]
    if errors:
        return errors

    for path, value in _walk_strings(payload):
        if value != value.strip():
            errors.append(f"{path}: leading or trailing whitespace is not allowed")
        if CONTROL_PATTERN.search(value):
            errors.append(f"{path}: control characters are not allowed")
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{path}: text must use NFC Unicode normalization")

    seen_ids: set[str] = set()
    record_groups = [payload["basics"]["links"]]
    record_groups.extend(payload[key] for key in ORDERED_COLLECTIONS)
    for records in record_groups:
        for record in records:
            record_id = record["id"]
            if record_id in seen_ids:
                errors.append("stable IDs must be unique across the resume")
            seen_ids.add(record_id)

    for key in ORDERED_COLLECTIONS:
        orders = [record["order"] for record in payload[key]]
        if len(orders) != len(set(orders)):
            errors.append(f"{key}: order values must be unique")

    for index, record in enumerate(payload["experience"]):
        current = record["current"]
        end = record["end"]
        if current and end is not None:
            errors.append(f"experience.{index}.end: current roles must have a null end")
        if not current and not isinstance(end, str):
            errors.append(f"experience.{index}.end: past roles require an end date")
        if isinstance(end, str):
            if _date_bounds(record["start"])[0] > _date_bounds(end)[1]:
                errors.append(f"experience.{index}: end date cannot precede start date")

    for index, record in enumerate(payload["education"]):
        if _date_bounds(record["start"])[0] > _date_bounds(record["end"])[1]:
            errors.append(f"education.{index}: end date cannot precede start date")

    release = payload["release"]
    if release["state"] == "approved":
        expected_hash = compute_content_hash(payload)
        if release["content_hash"] != expected_hash:
            errors.append("release.content_hash: does not match canonical public content")
        try:
            approved_at = datetime.fromisoformat(release["approved_at"].replace("Z", "+00:00"))
        except (AttributeError, ValueError):
            pass
        else:
            if approved_at.tzinfo is None:
                errors.append("release.approved_at: timezone information is required")

    return errors


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _format_date(value: str) -> str:
    if len(value) == 4:
        return value
    year, month = (int(part) for part in value.split("-"))
    return f"{MONTHS[month]} {year}"


def _time(value: str) -> str:
    return f'<time datetime="{_escape(value)}">{_escape(_format_date(value))}</time>'


def _optional_location(value: str | None) -> str:
    if value is None:
        return ""
    return f'<span class="resume__location">{_escape(value)}</span>'


def _render_scaffold(payload: Mapping[str, Any]) -> str:
    name = _escape(payload["basics"]["name"])
    return "\n".join(
        [
            SEMANTIC_START,
            '<article class="resume__document resume__document--scaffold" '
            'aria-labelledby="resume-name" data-resume-content>',
            '  <header class="resume__masthead">',
            '    <div class="resume__identity">',
            '      <p class="resume__eyebrow">Living resume</p>',
            f'      <h1 id="resume-name" class="resume__name">{name}</h1>',
            "    </div>",
            "  </header>",
            '  <section class="resume__section resume__status" aria-labelledby="resume-status">',
            '    <h2 id="resume-status" class="resume__section-title">Publication scaffold</h2>',
            "    <p>The generation pipeline is active. Public resume content remains staged "
            "for factual and privacy review.</p>",
            "    <p>After approval, this route and the plain, ATS-friendly route will be "
            "regenerated from one canonical snapshot.</p>",
            "  </section>",
            "</article>",
            SEMANTIC_END,
        ]
    )


def _render_links(links: list[Mapping[str, Any]]) -> list[str]:
    if not links:
        return []
    lines = [
        '    <ul class="resume__links" role="list" aria-label="Professional profiles">'
    ]
    for link in links:
        lines.append(
            "      <li>"
            f'<a href="{_escape(link["url"])}">{_escape(link["label"])}</a>'
            "</li>"
        )
    lines.append("    </ul>")
    return lines


def _render_approved(payload: Mapping[str, Any]) -> str:
    basics = payload["basics"]
    lines = [
        SEMANTIC_START,
        '<article class="resume__document" aria-labelledby="resume-name" data-resume-content>',
        '  <header class="resume__masthead">',
        '    <div class="resume__identity">',
        '      <p class="resume__eyebrow">Resume</p>',
        f'      <h1 id="resume-name" class="resume__name">{_escape(basics["name"])}</h1>',
        f'      <p class="resume__headline">{_escape(basics["headline"])}</p>',
    ]
    if basics["location"] is not None:
        lines.append(f'      <p class="resume__location">{_escape(basics["location"])}</p>')
    lines.extend(["    </div>", *_render_links(basics["links"]), "  </header>"])

    lines.extend(
        [
            '  <section class="resume__section resume__summary" aria-labelledby="resume-summary">',
            '    <h2 id="resume-summary" class="resume__section-title">Professional summary</h2>',
        ]
    )
    for paragraph in payload["summary"]:
        lines.append(f"    <p>{_escape(paragraph)}</p>")
    lines.append("  </section>")

    lines.extend(
        [
            '  <section class="resume__section resume__skills" aria-labelledby="resume-skills">',
            '    <h2 id="resume-skills" class="resume__section-title">Core capabilities</h2>',
            '    <div class="resume__skill-groups">',
        ]
    )
    for group in _ordered_records(payload, "skills"):
        group_id = f'skill-{_escape(group["id"])}'
        lines.extend(
            [
                f'      <section class="resume__skill-group" aria-labelledby="{group_id}">',
                f'        <h3 id="{group_id}" class="resume__skill-title">'
                f'{_escape(group["label"])}</h3>',
                '        <ul class="resume__skill-list" role="list">',
            ]
        )
        lines.extend(f"          <li>{_escape(item)}</li>" for item in group["items"])
        lines.extend(["        </ul>", "      </section>"])
    lines.extend(["    </div>", "  </section>"])

    lines.extend(
        [
            '  <section class="resume__section resume__experience" '
            'aria-labelledby="resume-experience">',
            '    <h2 id="resume-experience" class="resume__section-title">Experience</h2>',
            '    <div class="resume__entries">',
        ]
    )
    for record in _ordered_records(payload, "experience"):
        entry_id = f'experience-{_escape(record["id"])}'
        end = "<span>Present</span>" if record["current"] else _time(record["end"])
        location = _optional_location(record["location"])
        dates = f'<span class="resume__dates">{_time(record["start"])} – {end}</span>'
        meta_parts = [part for part in (location, dates) if part]
        meta = "\n".join(meta_parts)
        lines.extend(
            [
                f'      <section class="resume__entry" aria-labelledby="{entry_id}">',
                '        <header class="resume__entry-header">',
                "          <div>",
                f'            <h3 id="{entry_id}" class="resume__entry-role">'
                f'{_escape(record["role"])}</h3>',
                f'            <p class="resume__organization">{_escape(record["organization"])}</p>',
                "          </div>",
                f'          <p class="resume__entry-meta">{meta}</p>',
                "        </header>",
                '        <ul class="resume__highlights">',
            ]
        )
        lines.extend(f"          <li>{_escape(item)}</li>" for item in record["highlights"])
        lines.extend(["        </ul>", "      </section>"])
    lines.extend(["    </div>", "  </section>"])

    lines.extend(
        [
            '  <section class="resume__section resume__education" '
            'aria-labelledby="resume-education">',
            '    <h2 id="resume-education" class="resume__section-title">Education</h2>',
            '    <div class="resume__entries">',
        ]
    )
    for record in _ordered_records(payload, "education"):
        entry_id = f'education-{_escape(record["id"])}'
        location = _optional_location(record["location"])
        dates = (
            f'<span class="resume__dates">{_time(record["start"])} '
            f'– {_time(record["end"])}</span>'
        )
        meta_parts = [part for part in (location, dates) if part]
        meta = "\n".join(meta_parts)
        lines.extend(
            [
                f'      <section class="resume__entry resume__education-entry" '
                f'aria-labelledby="{entry_id}">',
                '        <header class="resume__entry-header">',
                "          <div>",
                f'            <h3 id="{entry_id}" class="resume__entry-role">'
                f'{_escape(record["credential"])}</h3>',
                f'            <p class="resume__organization">{_escape(record["institution"])}</p>',
                "          </div>",
                f'          <p class="resume__entry-meta">{meta}</p>',
                "        </header>",
                "      </section>",
            ]
        )
    lines.extend(["    </div>", "  </section>", "</article>", SEMANTIC_END])
    return "\n".join(lines)


def render_semantic_body(payload: Mapping[str, Any]) -> str:
    """Render the one canonical semantic article used by both public views."""

    if payload["release"]["state"] == "scaffold":
        return _render_scaffold(payload)
    return _render_approved(payload)


def render_template(template: str, context: Mapping[str, str]) -> str:
    """Render a fixed-token template, rejecting omissions and surprises."""

    discovered = TOKEN_PATTERN.findall(template)
    unknown = set(discovered) - set(context)
    missing = set(context) - set(discovered)
    duplicate = {token for token in discovered if discovered.count(token) != 1}
    if unknown or missing or duplicate:
        raise ResumeError("resume template token contract is invalid")

    def replace(match: re.Match[str]) -> str:
        return context[match.group(1)]

    rendered = TOKEN_PATTERN.sub(replace, template)
    if "{{" in rendered or "}}" in rendered:
        raise ResumeError("resume template contains an unresolved token")
    return rendered.rstrip() + "\n"


class _VisibleTextParser(HTMLParser):
    """Collect non-whitespace visible text outside the semantic article."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value:
            self.values.append(value)


def _validate_presentational_shell(rendered: str) -> None:
    """Allow only format controls—not resume copy—outside the shared article."""

    semantic = extract_semantic_region(rendered)
    outside = rendered.replace(semantic, "", 1)
    if outside.startswith("---\n"):
        closing = outside.find("\n---\n", 4)
        if closing == -1:
            raise ResumeError("generated resume front matter is not closed")
        outside = outside[closing + 5 :]

    parser = _VisibleTextParser()
    parser.feed(outside)
    if tuple(parser.values) != ALLOWED_SHELL_TEXT:
        raise ResumeError("generated resume shell contains unsupported visible copy")
    if rendered.count('class="resume-shell ') != 1:
        raise ResumeError("generated resume must contain one presentation shell")
    if rendered.count('class="resume__utility"') != 1:
        raise ResumeError("generated resume must contain one format control")


def render_outputs(
    payload: Mapping[str, Any],
    template_paths: Mapping[Path, Path] = TEMPLATE_PATHS,
) -> dict[Path, str]:
    """Render both public resume routes after validating the snapshot."""

    errors = validate_resume(payload)
    if errors:
        raise ResumeError("resume validation failed:\n- " + "\n- ".join(errors))

    release = payload["release"]
    context = {
        "release.state": release["state"],
        "release.version": release["version"] or "",
        "release.content_hash": release["content_hash"] or "scaffold",
        "semantic_resume_body": render_semantic_body(payload),
    }
    outputs: dict[Path, str] = {}
    for output_path, template_path in template_paths.items():
        template = template_path.read_text(encoding="utf-8")
        rendered = render_template(template, context)
        _validate_presentational_shell(rendered)
        outputs[output_path] = rendered
    return outputs


def check_outputs(outputs: Mapping[Path, str]) -> list[str]:
    """Return stale output paths without printing potentially sensitive diffs."""

    stale: list[str] = []
    for path, expected in outputs.items():
        try:
            actual = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            stale.append(repo_relative(path))
            continue
        if actual != expected:
            stale.append(repo_relative(path))
    return stale


def write_outputs(outputs: Mapping[Path, str]) -> list[str]:
    """Write only changed generated routes and return their paths."""

    changed: list[str] = []
    for path, expected in outputs.items():
        try:
            actual = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            actual = None
        if actual == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        changed.append(repo_relative(path))
    return changed


def extract_semantic_region(text: str) -> str:
    """Extract the exact shared semantic region from one generated route."""

    if text.count(SEMANTIC_START) != 1 or text.count(SEMANTIC_END) != 1:
        raise ResumeError("generated resume must contain one semantic region")
    start = text.index(SEMANTIC_START)
    end = text.index(SEMANTIC_END) + len(SEMANTIC_END)
    if end <= start:
        raise ResumeError("generated resume semantic markers are inverted")
    return text[start:end]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when tracked generated pages do not match the canonical snapshot",
    )
    args = parser.parse_args()

    try:
        payload = load_resume()
        outputs = render_outputs(payload)
    except ResumeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.check:
        stale = check_outputs(outputs)
        if stale:
            print("Generated resume pages are stale:", file=sys.stderr)
            for path in stale:
                print(f"- {path}", file=sys.stderr)
            print("Run `python -m scripts.build_resume` and review the result.", file=sys.stderr)
            return 1
        print("Generated resume pages are current.")
        return 0

    changed = write_outputs(outputs)
    if changed:
        print("Updated generated resume pages:")
        for path in changed:
            print(f"- {path}")
    else:
        print("Generated resume pages were already current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

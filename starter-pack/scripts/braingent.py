#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Braingent metadata tools.

This module backs the public shell wrappers:

- scripts/validate.sh
- scripts/reindex.sh
- scripts/find.sh
- scripts/recall.sh
- scripts/doctor.sh
- scripts/synthesize.sh
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by wrapper fallback.
    raise SystemExit(
        "Missing PyYAML. Install it with `python3 -m pip install PyYAML==6.0.3` "
        "or install uv and rerun the wrapper."
    ) from exc


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = REPO_ROOT / "preferences" / "taxonomy.yml"
INDEX_DIR = REPO_ROOT / "indexes"
RECORDS_JSON_PATH = INDEX_DIR / "records.json"
RECORDS_COMPACT_JSON_PATH = INDEX_DIR / "records-compact.json"
RECORDS_ROLLUP_MD_PATH = INDEX_DIR / "records-rollup.md"
SQLITE_PATH = REPO_ROOT / ".braingent.db"
GENERATED_BY = "scripts/reindex.sh"
SCHEMA_VERSION = 1
RECORDS_ROLLUP_PER_ORG_LIMIT = 30
FOLLOWUP_SCAN_ROOTS = ["orgs", "repositories", "topics", "tools", "tickets", "inbox", "imports"]
TASKS_DIR = REPO_ROOT / "tasks"
AGENT_TASK_ID_PATTERN = re.compile(r"^BGT-[0-9]{4,}$")
AGENT_TASK_ACTIVITY_PATTERN = re.compile(
    r"^- (?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})) "
    r"\| (?P<actor>[^|]+) \| role:(?P<role>[^|]+) \| event:(?P<event>[^|]+) \|$"
)
AGENT_TASK_STATUS_CATEGORIES = {
    "triage": "triage",
    "todo": "active",
    "in-progress": "active",
    "in-review": "active",
    "blocked": "active",
    "closed": "closed",
}


@dataclass(frozen=True)
class Record:
    path: Path
    frontmatter: dict[str, Any]
    body: str

    @property
    def relpath(self) -> str:
        try:
            return self.path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return self.path.as_posix()

    @property
    def title(self) -> str:
        title = self.frontmatter.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return self.path.stem

    @property
    def kind(self) -> str:
        return as_scalar(self.frontmatter.get("record_kind"))

    @property
    def status(self) -> str:
        return as_scalar(self.frontmatter.get("status"))

    @property
    def date_sort(self) -> str:
        for field in ("date", "date_completed", "date_imported", "last_reviewed", "last_checked", "opened"):
            value = self.frontmatter.get(field)
            if value not in (None, ""):
                return as_scalar(value)
        return ""


@dataclass
class ValidationIssue:
    path: Path
    message: str

    def format(self) -> str:
        try:
            label = self.path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            label = str(self.path)
        return f"{label}: {self.message}"


def as_scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def display_value(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, list):
        return ", ".join(as_scalar(item) for item in value) or "-"
    return as_scalar(value)


def first_scalar(*values: Any) -> str:
    for value in values:
        for item in as_list(value):
            item_str = as_scalar(item)
            if item_str:
                return item_str
    return ""


def table_cell(value: Any) -> str:
    text = display_value(value)
    return text.replace("\n", " ").replace("|", "\\|")


def truncate_text(text: str, max_chars: int = 280) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def clean_markdown_text(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[-*]\s+\[[ xX]\]\s+", "", line)
    line = re.sub(r"^[-*]\s+", "", line)
    line = re.sub(r"^\d+\.\s+", "", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("`", "")
    line = line.replace("**", "").replace("__", "")
    line = line.replace("<br>", " ")
    return line.strip()


def useful_body_lines(body: str, start_heading: str | None = None) -> list[str]:
    lines = body.splitlines()
    if start_heading:
        heading_pattern = re.compile(rf"^##+\s+{re.escape(start_heading)}\s*$", re.IGNORECASE)
        for index, line in enumerate(lines):
            if heading_pattern.match(line.strip()):
                lines = lines[index + 1 :]
                break
        else:
            return []

    result: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("#"):
            if result:
                break
            continue
        if not stripped:
            if result:
                break
            continue
        if stripped.startswith("<!--") or stripped.startswith("|") or stripped.startswith("<"):
            continue
        if re.match(r"^-{3,}$", stripped):
            continue
        cleaned = clean_markdown_text(stripped)
        if cleaned:
            result.append(cleaned)
    return result


def record_summary(record: Record, max_chars: int = 280) -> str:
    preferred_sections = (
        "Summary",
        "Durable Extract",
        "Goal",
        "What Changed",
        "Decision",
        "Findings",
        "Context",
        "Execution Notes",
        "Learnings",
        "Scope",
    )
    for heading in preferred_sections:
        lines = useful_body_lines(record.body, heading)
        if lines:
            return truncate_text(" ".join(lines), max_chars)

    lines = useful_body_lines(record.body)
    if lines:
        return truncate_text(" ".join(lines), max_chars)
    return ""


def parse_date_value(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    value_str = as_scalar(value)
    try:
        return date.fromisoformat(value_str[:10])
    except ValueError:
        return None


def days_since(value: Any, today: date | None = None) -> int | None:
    parsed = parse_date_value(value)
    if parsed is None:
        return None
    today = today or date.today()
    return (today - parsed).days


def md_link(label: str, path: Path) -> str:
    return f"[{label}]({path.relative_to(REPO_ROOT).as_posix()})"


def index_link(label: str, path: Path) -> str:
    return f"[{label}](../{path.relative_to(REPO_ROOT).as_posix()})"


def load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.load(handle, Loader=YAML_LOADER)
    if not isinstance(data, dict):
        raise SystemExit(f"{path.relative_to(REPO_ROOT)} must contain a YAML mapping.")
    return data


def load_taxonomy() -> dict[str, Any]:
    return load_yaml_file(TAXONOMY_PATH)


def parse_frontmatter_text(path: Path, text: str) -> tuple[dict[str, Any] | None, str, str | None]:
    if not text.startswith("---\n"):
        return None, text, None

    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text, "frontmatter starts with --- but has no closing delimiter"

    raw = text[4:end]
    body = text[end + len("\n---\n") :]
    try:
        parsed = yaml.load(raw, Loader=YAML_LOADER) or {}
    except yaml.YAMLError as exc:
        return None, body, f"invalid YAML frontmatter: {exc}"

    if not isinstance(parsed, dict):
        return None, body, "frontmatter must be a YAML mapping"

    return parsed, body, None


def split_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    return parse_frontmatter_text(path, path.read_text(encoding="utf-8"))


def is_record_like_path(path: Path) -> bool:
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        return True
    parts = rel.parts
    if "records" in parts:
        return True
    return len(parts) >= 3 and parts[0] in {"repositories", "tickets", "people"} and path.name == "README.md"


def iter_markdown_files(roots: Iterable[str]) -> Iterable[Path]:
    for root_name in roots:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.md")):
            if path.is_file():
                yield path


def load_records(paths: list[Path] | None = None, include_parse_errors: bool = False) -> tuple[list[Record], list[ValidationIssue]]:
    taxonomy = load_taxonomy()
    roots = taxonomy.get("record_scan_roots", [])
    candidates = paths if paths is not None else list(iter_markdown_files(roots))
    records: list[Record] = []
    issues: list[ValidationIssue] = []

    for path in candidates:
        if not path.exists() or path.suffix != ".md":
            continue
        frontmatter, body, error = split_frontmatter(path)
        if error:
            issues.append(ValidationIssue(path, error))
            continue
        if frontmatter is None:
            if include_parse_errors and is_record_like_path(path):
                issues.append(ValidationIssue(path, "record-like Markdown file is missing YAML frontmatter"))
            continue
        records.append(Record(path=path, frontmatter=frontmatter, body=body))

    return sorted(records, key=lambda record: record.relpath), issues


def existing_entity_keys(field: str, spec: dict[str, Any]) -> set[str]:
    directory_root = spec.get("directory_root")
    if directory_root:
        root = REPO_ROOT / directory_root
        if not root.exists():
            return set()
        return {path.name for path in root.iterdir() if path.is_dir()}

    glob_pattern = spec.get("directory_glob")
    if glob_pattern and "{value}" not in glob_pattern:
        return {path.name for path in REPO_ROOT.glob(glob_pattern) if path.is_dir()}

    return set()


def entity_exists(value: str, spec: dict[str, Any]) -> bool:
    directory_root = spec.get("directory_root")
    if directory_root:
        return (REPO_ROOT / directory_root / value).is_dir()

    glob_pattern = spec.get("directory_glob")
    if glob_pattern:
        matches = list(REPO_ROOT.glob(glob_pattern.replace("{value}", value)))
        return any(path.is_dir() for path in matches)

    return True


def is_nullish(value: Any) -> bool:
    return value is None or value == "" or value == "null"


def parse_datetime_value(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    value_str = as_scalar(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value_str)
    except ValueError:
        return None


def body_has_heading(body: str, heading: str) -> bool:
    return re.search(rf"^## {re.escape(heading)}$", body, re.MULTILINE) is not None


def task_id_from_record(record: Record) -> str:
    return as_scalar(record.frontmatter.get("id"))


def agent_task_visibility(record: Record) -> str:
    return as_scalar(record.frontmatter.get("visibility") or "private")


def validate_enum_field(
    record: Record,
    field: str,
    allowed: Iterable[str],
    issues: list[ValidationIssue],
    *,
    nullable: bool = False,
) -> None:
    value = record.frontmatter.get(field)
    if nullable and is_nullish(value):
        return
    allowed_values = list(allowed)
    if value not in allowed_values:
        issues.append(ValidationIssue(record.path, f"`{field}` must be one of: {', '.join(allowed_values)}"))


def validate_agent_task_record(record: Record, taxonomy: dict[str, Any]) -> list[ValidationIssue]:
    fm = record.frontmatter
    issues: list[ValidationIssue] = []
    path = record.path
    task_id = task_id_from_record(record)

    if not AGENT_TASK_ID_PATTERN.match(task_id):
        issues.append(ValidationIssue(path, "`id` must match BGT-0001 style"))

    if path.is_relative_to(TASKS_DIR) and task_id and not path.name.startswith(f"{task_id}--"):
        issues.append(ValidationIssue(path, "filename must start with `<id>--`"))

    validate_enum_field(record, "status_category", taxonomy.get("agent_task_status_categories", []), issues)
    validate_enum_field(record, "type", taxonomy.get("agent_task_types", []), issues)
    validate_enum_field(record, "priority", taxonomy.get("agent_task_priorities", []), issues)
    validate_enum_field(record, "visibility", taxonomy.get("agent_task_visibilities", []), issues, nullable=True)

    status = as_scalar(fm.get("status"))
    expected_category = AGENT_TASK_STATUS_CATEGORIES.get(status)
    if expected_category and fm.get("status_category") != expected_category:
        issues.append(ValidationIssue(path, f"`status_category` must be `{expected_category}` when status is `{status}`"))

    resolution = fm.get("resolution")
    duplicate_of = fm.get("duplicate_of")
    closed = fm.get("closed")
    allowed_resolutions = taxonomy.get("agent_task_resolutions", [])
    if status == "closed":
        if resolution not in allowed_resolutions:
            issues.append(ValidationIssue(path, f"closed agent-task requires resolution: {', '.join(allowed_resolutions)}"))
        if is_nullish(closed):
            issues.append(ValidationIssue(path, "closed agent-task requires `closed` date"))
    else:
        if not is_nullish(resolution):
            issues.append(ValidationIssue(path, "`resolution` must be null unless status is `closed`"))
        if not is_nullish(closed):
            issues.append(ValidationIssue(path, "`closed` must be null unless status is `closed`"))

    if resolution == "duplicate" and is_nullish(duplicate_of):
        issues.append(ValidationIssue(path, "`duplicate_of` is required when resolution is `duplicate`"))
    if resolution != "duplicate" and not is_nullish(duplicate_of):
        issues.append(ValidationIssue(path, "`duplicate_of` must be null unless resolution is `duplicate`"))

    allowed_agents = set(taxonomy.get("agent_ids", []))
    for field in ("assignee", "reviewer", "claimed_by"):
        value = fm.get(field)
        if not is_nullish(value) and value not in allowed_agents:
            issues.append(ValidationIssue(path, f"`{field}` has unknown agent ID `{value}`"))
    for observer in as_list(fm.get("observers")):
        if observer not in allowed_agents:
            issues.append(ValidationIssue(path, f"`observers` has unknown agent ID `{observer}`"))

    for field in ("date", "created", "updated", "closed"):
        value = fm.get(field)
        if not is_nullish(value) and parse_date_value(value) is None:
            issues.append(ValidationIssue(path, f"`{field}` must be an ISO date"))
    if not is_nullish(fm.get("claimed_at")) and parse_datetime_value(fm.get("claimed_at")) is None:
        issues.append(ValidationIssue(path, "`claimed_at` must be an ISO datetime with timezone"))

    for heading in ("Description", "Acceptance Criteria", "Plan", "Dependencies", "Activity", "Linked Evidence"):
        if not body_has_heading(record.body, heading):
            issues.append(ValidationIssue(path, f"missing `## {heading}` section"))

    allowed_events = set(taxonomy.get("agent_task_events", []))
    for line in record.body.splitlines():
        if not line.startswith("- "):
            continue
        if "|" not in line or "event:" not in line:
            continue
        match = AGENT_TASK_ACTIVITY_PATTERN.match(line)
        if not match:
            issues.append(ValidationIssue(path, f"malformed activity entry `{line}`"))
            continue
        if parse_datetime_value(match.group("timestamp")) is None:
            issues.append(ValidationIssue(path, f"malformed activity timestamp `{match.group('timestamp')}`"))
        actor = match.group("actor").strip()
        if actor not in allowed_agents:
            issues.append(ValidationIssue(path, f"activity has unknown actor `{actor}`"))
        event = match.group("event").strip()
        if event not in allowed_events:
            issues.append(ValidationIssue(path, f"activity has unknown event `{event}`"))

    visibility = agent_task_visibility(record)
    if visibility in {"shareable", "public"} and "event:visibility" not in record.body:
        issues.append(ValidationIssue(path, f"`visibility: {visibility}` requires an activity entry with event:visibility"))

    return issues


def validate_record(record: Record, taxonomy: dict[str, Any]) -> list[ValidationIssue]:
    fm = record.frontmatter
    issues: list[ValidationIssue] = []
    path = record.path

    allowed_fields = set(taxonomy.get("allowed_fields", []))
    for field in sorted(fm):
        if field not in allowed_fields:
            suggestion = ""
            if field == "tickets":
                suggestion = " Use scalar `ticket:` instead."
            issues.append(ValidationIssue(path, f"unknown frontmatter field `{field}`.{suggestion}"))

    common_required = taxonomy.get("required_fields", {}).get("common", [])
    for field in common_required:
        if field not in fm:
            issues.append(ValidationIssue(path, f"missing required field `{field}`"))

    kind = fm.get("record_kind")
    if not isinstance(kind, str) or not kind:
        issues.append(ValidationIssue(path, "`record_kind` must be a non-empty string"))
        return issues

    record_kinds = set(taxonomy.get("record_kinds", []))
    if kind not in record_kinds:
        issues.append(ValidationIssue(path, f"unknown record_kind `{kind}`"))

    statuses = taxonomy.get("statuses", {})
    status = fm.get("status")
    if not isinstance(status, str) or not status:
        issues.append(ValidationIssue(path, "`status` must be a non-empty string"))
    elif kind in statuses and status not in statuses[kind]:
        allowed = ", ".join(statuses[kind])
        issues.append(ValidationIssue(path, f"invalid status `{status}` for {kind}; allowed: {allowed}"))

    for field in taxonomy.get("required_fields", {}).get(kind, []):
        if field not in fm:
            issues.append(ValidationIssue(path, f"missing required field `{field}` for {kind}"))

    list_fields = set(taxonomy.get("list_fields", []))
    for field in sorted(list_fields & set(fm)):
        if not isinstance(fm[field], list):
            issues.append(ValidationIssue(path, f"`{field}` must be a YAML list"))

    nullable_fields = set(taxonomy.get("nullable_fields", []))
    for field, value in fm.items():
        if is_nullish(value):
            continue
        if field in nullable_fields and value == "null":
            continue
        if field in taxonomy.get("entity_fields", {}):
            issues.extend(validate_entity_values(record, field, value, taxonomy["entity_fields"][field]))

    if "ai_tools" in fm and isinstance(fm["ai_tools"], list):
        allowed_ai_tools = set(taxonomy.get("ai_tools", []))
        for item in fm["ai_tools"]:
            if item not in allowed_ai_tools:
                allowed = ", ".join(sorted(allowed_ai_tools))
                issues.append(ValidationIssue(path, f"unknown ai_tools value `{item}`; allowed: {allowed}"))

    if kind == "agent-task":
        issues.extend(validate_agent_task_record(record, taxonomy))

    if "ticket_system" in fm and not is_nullish(fm["ticket_system"]):
        systems = set(taxonomy.get("ticket_systems", []))
        if fm["ticket_system"] not in systems:
            issues.append(ValidationIssue(path, f"unknown ticket_system `{fm['ticket_system']}`"))

    if "ticket" in fm and not is_nullish(fm["ticket"]):
        ticket = fm["ticket"]
        if isinstance(ticket, list):
            issues.append(ValidationIssue(path, "`ticket` must be a scalar; use one record per primary ticket"))
        elif as_scalar(ticket).lower() != as_scalar(ticket) and "-" not in as_scalar(ticket):
            pass
        else:
            ticket_system = as_scalar(fm.get("ticket_system"))
            if ticket_system == "github":
                pattern = taxonomy.get("ticket_patterns", {}).get("github")
            else:
                pattern = taxonomy.get("ticket_patterns", {}).get("jira")
            if pattern and not re.match(pattern, as_scalar(ticket)):
                issues.append(ValidationIssue(path, f"ticket `{ticket}` does not match expected uppercase ticket format"))

    return issues


def validate_entity_values(record: Record, field: str, value: Any, spec: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    values = as_list(value)
    prefix = spec.get("prefix")

    for item in values:
        if is_nullish(item):
            continue
        item_str = as_scalar(item)
        if prefix and not item_str.startswith(prefix):
            issues.append(ValidationIssue(record.path, f"`{field}` value `{item_str}` must start with `{prefix}`"))
            continue
        if not entity_exists(item_str, spec):
            issues.append(ValidationIssue(record.path, f"`{field}` value `{item_str}` has no matching directory"))

    return issues


def validate_agent_task_collection(records: list[Record]) -> list[ValidationIssue]:
    agent_tasks = [record for record in records if record.frontmatter.get("record_kind") == "agent-task"]
    issues: list[ValidationIssue] = []
    by_id: dict[str, Record] = {}

    for record in agent_tasks:
        task_id = task_id_from_record(record)
        if not task_id:
            continue
        if task_id in by_id:
            issues.append(ValidationIssue(record.path, f"duplicate agent-task id `{task_id}` also used by {by_id[task_id].relpath}"))
        else:
            by_id[task_id] = record

    for record in agent_tasks:
        task_id = task_id_from_record(record)
        for dependency in as_list(record.frontmatter.get("depends_on")):
            dep_id = as_scalar(dependency)
            if dep_id == task_id:
                issues.append(ValidationIssue(record.path, "agent-task cannot depend on itself"))
            elif dep_id not in by_id:
                issues.append(ValidationIssue(record.path, f"`depends_on` references unknown agent-task `{dep_id}`"))

        parent = record.frontmatter.get("parent")
        if not is_nullish(parent):
            parent_id = as_scalar(parent)
            if parent_id == task_id:
                issues.append(ValidationIssue(record.path, "agent-task cannot be its own parent"))
            elif parent_id not in by_id:
                issues.append(ValidationIssue(record.path, f"`parent` references unknown agent-task `{parent_id}`"))
            elif not is_nullish(by_id[parent_id].frontmatter.get("parent")):
                issues.append(ValidationIssue(record.path, "agent-task parent chains deeper than one level are not allowed"))

        duplicate_of = record.frontmatter.get("duplicate_of")
        if not is_nullish(duplicate_of):
            duplicate_id = as_scalar(duplicate_of)
            if duplicate_id == task_id:
                issues.append(ValidationIssue(record.path, "agent-task cannot duplicate itself"))
            elif duplicate_id not in by_id:
                issues.append(ValidationIssue(record.path, f"`duplicate_of` references unknown agent-task `{duplicate_id}`"))

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str, path: list[str]) -> None:
        if task_id in visited:
            return
        if task_id in visiting:
            cycle = " -> ".join([*path, task_id])
            issues.append(ValidationIssue(by_id[task_id].path, f"dependency cycle detected: {cycle}"))
            return
        visiting.add(task_id)
        record = by_id.get(task_id)
        if record:
            for dependency in as_list(record.frontmatter.get("depends_on")):
                dep_id = as_scalar(dependency)
                if dep_id in by_id:
                    visit(dep_id, [*path, task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in sorted(by_id):
        visit(task_id, [])

    return issues


def validate_loaded_records(
    records: list[Record],
    parse_issues: list[ValidationIssue],
    taxonomy: dict[str, Any] | None = None,
) -> list[ValidationIssue]:
    taxonomy = taxonomy or load_taxonomy()
    issues = list(parse_issues)
    for record in records:
        issues.extend(validate_record(record, taxonomy))
    issues.extend(validate_agent_task_collection(records))
    return issues


def validate(paths: list[Path] | None = None) -> list[ValidationIssue]:
    taxonomy = load_taxonomy()
    records, parse_issues = load_records(paths=paths, include_parse_errors=True)
    if paths is not None and any(record.frontmatter.get("record_kind") == "agent-task" for record in records):
        task_records, task_parse_issues = load_records(paths=task_files(), include_parse_errors=True)
        known_paths = {record.path for record in records}
        records.extend(record for record in task_records if record.path not in known_paths)
        parse_issues.extend(task_parse_issues)
    return validate_loaded_records(records, parse_issues, taxonomy)


def record_to_json(record: Record) -> dict[str, Any]:
    fm = record.frontmatter
    return {
        "path": record.relpath,
        "title": record.title,
        "summary": record_summary(record),
        "record_kind": fm.get("record_kind"),
        "status": fm.get("status"),
        "date": fm.get("date") or fm.get("date_imported") or fm.get("last_reviewed") or fm.get("opened"),
        "organization": fm.get("organization"),
        "project": fm.get("project"),
        "projects": as_list(fm.get("projects")),
        "ticket": fm.get("ticket"),
        "repositories": as_list(fm.get("repositories")) + as_list(fm.get("repo")),
        "people": as_list(fm.get("people")) + as_list(fm.get("person")),
        "topics": as_list(fm.get("topics")) + as_list(fm.get("topic")),
        "tools": as_list(fm.get("tools")) + as_list(fm.get("tool")),
        "ai_tools": as_list(fm.get("ai_tools")),
        "prs": as_list(fm.get("prs")),
        "commits": as_list(fm.get("commits")),
        "frontmatter": fm,
    }


def compact_record_to_json(record: Record) -> dict[str, Any]:
    fm = record.frontmatter
    return {
        "path": record.relpath,
        "title": record.title,
        "kind": as_scalar(fm.get("record_kind")),
        "date": as_scalar(fm.get("date") or fm.get("date_imported") or fm.get("last_reviewed") or fm.get("opened")),
        "org": first_scalar(fm.get("organization")),
        "repo": first_scalar(fm.get("repositories"), fm.get("repo")),
        "project": first_scalar(fm.get("project"), fm.get("projects")),
        "ticket": first_scalar(fm.get("ticket")),
        "status": as_scalar(fm.get("status")),
    }


def entity_name_from_readme(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    frontmatter, _, _ = split_frontmatter(path)
    if frontmatter and isinstance(frontmatter.get("title"), str):
        return frontmatter["title"].strip()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def discover_directory_entities(root_name: str, prefix: str) -> dict[str, dict[str, str]]:
    root = REPO_ROOT / root_name
    entities: dict[str, dict[str, str]] = {}
    if not root.exists():
        return entities
    for path in sorted(root.iterdir()):
        if not path.is_dir() or not path.name.startswith(prefix):
            continue
        readme = path / "README.md"
        entities[path.name] = {
            "key": path.name,
            "name": entity_name_from_readme(readme, path.name),
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "readme": readme.relative_to(REPO_ROOT).as_posix() if readme.exists() else "",
        }
    return entities


def discover_projects() -> dict[str, dict[str, str]]:
    entities: dict[str, dict[str, str]] = {}
    for path in sorted((REPO_ROOT / "orgs").glob("*/projects/project--*")):
        if not path.is_dir():
            continue
        readme = path / "README.md"
        rel_parts = path.relative_to(REPO_ROOT).parts
        organization = rel_parts[1] if len(rel_parts) > 1 else ""
        entities[path.name] = {
            "key": path.name,
            "name": entity_name_from_readme(readme, path.name),
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "readme": readme.relative_to(REPO_ROOT).as_posix() if readme.exists() else "",
            "organization": organization,
        }
    return entities


def build_entities(records: list[Record]) -> dict[str, Any]:
    organizations = discover_directory_entities("orgs", "org--")
    repositories = discover_directory_entities("repositories", "repo--")
    topics = discover_directory_entities("topics", "topic--")
    tools = discover_directory_entities("tools", "tool--")
    people = discover_directory_entities("people", "person--")
    projects = discover_projects()

    for record in records:
        fm = record.frontmatter
        for key in as_list(fm.get("organization")):
            if key and key not in organizations:
                organizations[key] = {"key": key, "name": key, "path": "", "readme": ""}
        for key in as_list(fm.get("project")) + as_list(fm.get("projects")):
            if key and key not in projects:
                projects[key] = {"key": key, "name": key, "path": "", "readme": ""}
        for key in as_list(fm.get("repo")) + as_list(fm.get("repositories")):
            if key and key not in repositories:
                repositories[key] = {"key": key, "name": key, "path": "", "readme": ""}
        for key in as_list(fm.get("topic")) + as_list(fm.get("topics")):
            if key and key not in topics:
                topics[key] = {"key": key, "name": key, "path": "", "readme": ""}
        for key in as_list(fm.get("tool")) + as_list(fm.get("tools")):
            if key and key not in tools:
                tools[key] = {"key": key, "name": key, "path": "", "readme": ""}
        for key in as_list(fm.get("person")) + as_list(fm.get("people")):
            if key and key not in people:
                people[key] = {"key": key, "name": key, "path": "", "readme": ""}

    return {
        "organizations": sorted(organizations.values(), key=lambda item: item["key"]),
        "projects": sorted(projects.values(), key=lambda item: item["key"]),
        "repositories": sorted(repositories.values(), key=lambda item: item["key"]),
        "topics": sorted(topics.values(), key=lambda item: item["key"]),
        "tools": sorted(tools.values(), key=lambda item: item["key"]),
        "people": sorted(people.values(), key=lambda item: item["key"]),
    }


def records_json(records: list[Record]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "records": [record_to_json(record) for record in records],
        "entities": build_entities(records),
    }
    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"


def records_compact_json(records: list[Record]) -> str:
    payload = [compact_record_to_json(record) for record in records]
    return json.dumps(payload, separators=(",", ":"), default=str) + "\n"


def records_for_entity(records: list[Record], *fields: str, value: str) -> list[Record]:
    matched: list[Record] = []
    for record in records:
        for field in fields:
            if value in [as_scalar(item) for item in as_list(record.frontmatter.get(field))]:
                matched.append(record)
                break
    return sorted(matched, key=lambda record: (record.date_sort, record.relpath), reverse=True)


def count_records(records: list[Record], *fields: str, value: str) -> int:
    return len(records_for_entity(records, *fields, value=value))


def record_index_link(record: Record) -> str:
    return index_link(record.title, record.path)


def recent_record_links(records: list[Record], *fields: str, value: str, limit: int = 3) -> str:
    matched = records_for_entity(records, *fields, value=value)
    if not matched:
        return "-"
    return "<br>".join(record_index_link(record) for record in matched[:limit])


def scope_label(record: Record) -> str:
    fm = record.frontmatter
    parts: list[str] = []
    for field in ("organization", "project", "ticket"):
        value = fm.get(field)
        if value:
            parts.append(f"`{value}`")
    for field in ("repositories", "repo", "topics", "topic", "tools", "tool"):
        for value in as_list(fm.get(field))[:2]:
            if value:
                parts.append(f"`{value}`")
    return "<br>".join(unique_strings(parts[:4])) or "-"


def repository_keys_for_project(records: list[Record], project_key: str) -> list[str]:
    values: list[str] = []
    for record in records:
        if record.kind != "profile":
            continue
        if project_key not in [as_scalar(item) for item in as_list(record.frontmatter.get("project"))]:
            continue
        values.extend(as_scalar(item) for item in as_list(record.frontmatter.get("repo")))
        values.extend(as_scalar(item) for item in as_list(record.frontmatter.get("repositories")))
    return unique_strings(values)


def generated_header(title: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "<!-- Generated by scripts/reindex.sh. Do not edit by hand. -->",
        "",
    ]


def render_organizations(records: list[Record], entities: dict[str, Any]) -> str:
    lines = generated_header("Organization Index")
    lines.extend(["| Organization | Key | Projects | Records | Recent Records |", "| --- | --- | ---: | ---: | --- |"])
    projects = entities["projects"]
    for org in entities["organizations"]:
        key = org["key"]
        org_projects = [project for project in projects if f"project--{key.removeprefix('org--')}--" in project["key"]]
        linked_name = index_link(org["name"], REPO_ROOT / org["readme"]) if org["readme"] else org["name"]
        lines.append(
            f"| {linked_name} | `{key}` | {len(org_projects)} | {count_records(records, 'organization', value=key)} | "
            f"{recent_record_links(records, 'organization', value=key)} |"
        )
    return "\n".join(lines) + "\n"


def render_projects(records: list[Record], entities: dict[str, Any]) -> str:
    lines = generated_header("Project Index")
    lines.extend(["| Project | Key | Organization | Repositories | Records | Recent Records |", "| --- | --- | --- | ---: | ---: | --- |"])
    for project in entities["projects"]:
        key = project["key"]
        organization = project.get("organization", "-")
        linked_name = index_link(project["name"], REPO_ROOT / project["readme"]) if project["readme"] else project["name"]
        repo_count = len(repository_keys_for_project(records, key))
        record_count = count_records(records, "project", "projects", value=key)
        lines.append(
            f"| {linked_name} | `{key}` | {display_value(organization)} | {repo_count} | {record_count} | "
            f"{recent_record_links(records, 'project', 'projects', value=key)} |"
        )
    return "\n".join(lines) + "\n"


def render_repositories(records: list[Record], entities: dict[str, Any]) -> str:
    lines = generated_header("Repository Index")
    lines.extend(["| Repository | Key | Organization | Project | Records | Profile | Recent Records |", "| --- | --- | --- | --- | ---: | --- | --- |"])
    for repo in entities["repositories"]:
        key = repo["key"]
        profile = next((record for record in records if record.frontmatter.get("repo") == key), None)
        organization = profile.frontmatter.get("organization") if profile else "-"
        project = profile.frontmatter.get("project") if profile else "-"
        profile_link = index_link("Profile", profile.path) if profile else "-"
        linked_name = index_link(repo["name"], REPO_ROOT / repo["readme"]) if repo["readme"] else repo["name"]
        lines.append(
            f"| {linked_name} | `{key}` | {display_value(organization)} | {display_value(project)} | "
            f"{count_records(records, 'repo', 'repositories', value=key)} | {profile_link} | "
            f"{recent_record_links(records, 'repo', 'repositories', value=key)} |"
        )
    return "\n".join(lines) + "\n"


def render_topics(records: list[Record], entities: dict[str, Any]) -> str:
    lines = generated_header("Topic Index")
    lines.extend(["| Topic | Key | Records | Recent Records |", "| --- | --- | ---: | --- |"])
    for topic in entities["topics"]:
        key = topic["key"]
        linked_name = index_link(topic["name"], REPO_ROOT / topic["readme"]) if topic["readme"] else topic["name"]
        lines.append(
            f"| {linked_name} | `{key}` | {count_records(records, 'topic', 'topics', value=key)} | "
            f"{recent_record_links(records, 'topic', 'topics', value=key)} |"
        )
    return "\n".join(lines) + "\n"


def render_tools(records: list[Record], entities: dict[str, Any]) -> str:
    lines = generated_header("Tool Index")
    lines.extend(["| Tool | Key | Current Version | Last Checked | Records | Recent Records |", "| --- | --- | --- | --- | ---: | --- |"])
    for tool in entities["tools"]:
        key = tool["key"]
        tool_records = records_for_entity(records, "tool", "tools", value=key)
        latest = tool_records[0] if tool_records else None
        current_version = latest.frontmatter.get("version") if latest else "-"
        last_checked = latest.frontmatter.get("last_checked") if latest else "-"
        linked_name = index_link(tool["name"], REPO_ROOT / tool["readme"]) if tool["readme"] else tool["name"]
        lines.append(
            f"| {linked_name} | `{key}` | {display_value(current_version)} | {display_value(last_checked)} | "
            f"{len(tool_records)} | {recent_record_links(records, 'tool', 'tools', value=key)} |"
        )
    return "\n".join(lines) + "\n"


def render_people(records: list[Record], entities: dict[str, Any]) -> str:
    lines = generated_header("People Index")
    lines.extend(["| Person | Key | Organization | Records | Recent Records |", "| --- | --- | --- | ---: | --- |"])
    for person in entities["people"]:
        key = person["key"]
        person_records = records_for_entity(records, "person", "people", value=key)
        org = person_records[0].frontmatter.get("organization") if person_records else "-"
        linked_name = index_link(person["name"], REPO_ROOT / person["readme"]) if person["readme"] else person["name"]
        lines.append(
            f"| {linked_name} | `{key}` | {display_value(org)} | {len(person_records)} | "
            f"{recent_record_links(records, 'person', 'people', value=key)} |"
        )
    return "\n".join(lines) + "\n"


def render_records_index(records: list[Record]) -> str:
    lines = generated_header("Records Index")
    lines.extend(
        [
            "This generated index is optimized for human and AI scanning. Durable records remain source of truth.",
            "",
            "| Date | Kind | Status | Title | Scope | Summary |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for record in sorted(records, key=lambda item: (item.date_sort, item.relpath), reverse=True):
        lines.append(
            f"| {table_cell(record.date_sort)} | {table_cell(record.kind)} | {table_cell(record.status)} | "
            f"{record_index_link(record)} | {scope_label(record)} | {table_cell(record_summary(record, max_chars=220))} |"
        )
    return "\n".join(lines) + "\n"


def render_records_rollup(records: list[Record]) -> str:
    groups: dict[str, list[Record]] = {}
    for record in records:
        org = first_scalar(record.frontmatter.get("organization")) or "unscoped"
        groups.setdefault(org, []).append(record)

    lines = generated_header("Records Rollup")
    lines.extend(
        [
            "Compact organization rollup for retrieval planning. Use records.md or records.json for complete detail.",
            "",
        ]
    )
    for org in sorted(groups):
        org_records = sorted(groups[org], key=lambda item: (item.date_sort, item.relpath), reverse=True)
        lines.extend([f"## `{org}`", ""])
        for record in org_records[:RECORDS_ROLLUP_PER_ORG_LIMIT]:
            line_parts = [
                f"`{record.kind or '-'}`",
                record_index_link(record),
                table_cell(record.date_sort),
                table_cell(record.status),
            ]
            lines.append("- " + " - ".join(line_parts))
        omitted = len(org_records) - RECORDS_ROLLUP_PER_ORG_LIMIT
        if omitted > 0:
            lines.append(f"- {omitted} older records omitted from this compact rollup.")
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def agent_task_records(records: list[Record]) -> list[Record]:
    return [record for record in records if record.frontmatter.get("record_kind") == "agent-task"]


def agent_task_status_counts(records: list[Record]) -> dict[str, int]:
    counts = {status: 0 for status in AGENT_TASK_STATUS_CATEGORIES}
    counts["active"] = 0
    for record in agent_task_records(records):
        status = as_scalar(record.frontmatter.get("status"))
        if status in counts:
            counts[status] += 1
        if status != "closed":
            counts["active"] += 1
    return counts


def agent_task_count_line(records: list[Record]) -> str:
    counts = agent_task_status_counts(records)
    ordered = ["active", "triage", "todo", "in-progress", "in-review", "blocked", "closed"]
    return "  ".join(f"# {status}: {counts.get(status, 0)}" for status in ordered)


def agent_task_sort_key(record: Record) -> tuple[str, str, str]:
    priority_rank = {"critical": "0", "high": "1", "medium": "2", "low": "3"}
    fm = record.frontmatter
    return (
        priority_rank.get(as_scalar(fm.get("priority")), "9"),
        as_scalar(fm.get("updated") or fm.get("date")),
        as_scalar(fm.get("id")),
    )


def latest_agent_task_activity_date(record: Record) -> date | None:
    latest: datetime | None = None
    for line in record.body.splitlines():
        match = AGENT_TASK_ACTIVITY_PATTERN.match(line)
        if not match:
            continue
        parsed = parse_datetime_value(match.group("timestamp"))
        if parsed is None:
            continue
        if latest is None or parsed > latest:
            latest = parsed
    return latest.date() if latest else None


def agent_task_freshness_date(record: Record) -> date | None:
    fm = record.frontmatter
    for value in (fm.get("updated"), fm.get("created"), fm.get("date")):
        parsed = parse_date_value(value)
        if parsed:
            return parsed
    return None


def agent_task_stale_reason(record: Record, today: date | None = None) -> str | None:
    today = today or date.today()
    status = as_scalar(record.frontmatter.get("status"))

    if status in {"triage", "blocked"}:
        basis = agent_task_freshness_date(record)
        if basis is None:
            return f"{status} task has no parseable updated, created, or date field"
        age = (today - basis).days
        if age > 30:
            return f"{status} task is {age} days old"

    if status == "in-progress":
        basis = latest_agent_task_activity_date(record)
        if basis is None:
            basis = agent_task_freshness_date(record)
            if basis is None:
                return "in-progress task has no parseable activity or freshness date"
            age = (today - basis).days
            if age > 14:
                return f"in-progress task has no activity entries and is {age} days old"
            return None
        age = (today - basis).days
        if age > 14:
            return f"in-progress task latest activity is {age} days old"

    return None


def render_memory_summary(records: list[Record]) -> str:
    lines = generated_header("Memory Summary")
    kinds: dict[str, int] = {}
    for record in records:
        kinds[record.kind] = kinds.get(record.kind, 0) + 1
    kind_summary = ", ".join(f"{kind}: {count}" for kind, count in sorted(kinds.items())) or "none"
    lines.extend(
        [
            "Tier 1 scan surface for live work and durable-memory volume.",
            "",
            f"Task counts: {agent_task_count_line(records)}",
            f"Record counts: {kind_summary}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_task_index(records: list[Record]) -> str:
    tasks = sorted(agent_task_records(records), key=lambda record: as_scalar(record.frontmatter.get("id")))
    lines = generated_header("Agent Task Index")
    lines.extend(
        [
            "Generated map of live and archived Braingent agent tasks.",
            "",
            f"Task counts: {agent_task_count_line(records)}",
            "",
            "| ID | Status | Priority | Assignee | Updated | Task |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not tasks:
        lines.append("| - | - | - | - | - | - |")
    for record in tasks:
        fm = record.frontmatter
        rel = record.path.relative_to(TASKS_DIR).as_posix()
        link = f"[{record.title}]({rel})"
        lines.append(
            f"| `{table_cell(fm.get('id'))}` | {table_cell(fm.get('status'))} | {table_cell(fm.get('priority'))} | "
            f"{table_cell(fm.get('assignee'))} | {table_cell(fm.get('updated'))} | {link} |"
        )
    return "\n".join(lines) + "\n"


def render_stale_candidates_index(records: list[Record], stale_days: int = 180) -> str:
    today = date.today()
    durable_candidates: list[tuple[Record, str]] = []
    task_candidates: list[tuple[Record, str]] = []

    for record in records:
        if record.kind == "agent-task":
            reason = agent_task_stale_reason(record, today)
            if reason:
                task_candidates.append((record, reason))
            continue
        reason = stale_reason(record, stale_days=stale_days, today=today)
        if reason:
            durable_candidates.append((record, reason))

    lines = generated_header("Stale Candidates")
    lines.extend(
        [
            "Generated cleanup queue for stale durable records and live task hygiene.",
            "",
            "## Live Tasks",
            "",
            "| Task | Status | Updated | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    if not task_candidates:
        lines.append("| - | - | - | - |")
    for record, reason in sorted(task_candidates, key=lambda item: agent_task_sort_key(item[0])):
        fm = record.frontmatter
        lines.append(
            f"| {record_index_link(record)} | {table_cell(fm.get('status'))} | "
            f"{table_cell(fm.get('updated') or fm.get('created') or fm.get('date'))} | {table_cell(reason)} |"
        )

    lines.extend(
        [
            "",
            "## Durable Records",
            "",
            "| Record | Kind | Status | Date | Reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if not durable_candidates:
        lines.append("| - | - | - | - | - |")
    for record, reason in sorted(durable_candidates, key=lambda item: (item[0].date_sort, item[0].relpath), reverse=True):
        lines.append(
            f"| {record_index_link(record)} | {table_cell(record.kind)} | {table_cell(record.status)} | "
            f"{table_cell(record.date_sort)} | {table_cell(reason)} |"
        )
    return "\n".join(lines) + "\n"


def render_agent_task_queue(records: list[Record]) -> str:
    tasks = sorted(agent_task_records(records), key=agent_task_sort_key)
    lines = generated_header("Agent Task Queue")
    lines.extend(
        [
            "Live task files are source of truth. Closed tasks stay queryable from the archive.",
            "",
        ]
    )
    sections = [
        ("Triage", "triage"),
        ("Todo", "todo"),
        ("In Progress", "in-progress"),
        ("In Review", "in-review"),
        ("Blocked", "blocked"),
        ("Closed", "closed"),
    ]
    for title, status in sections:
        lines.extend([f"## {title}", "", "| ID | Priority | Assignee | Reviewer | Updated | Task | Depends On |", "| --- | --- | --- | --- | --- | --- | --- |"])
        matching = [record for record in tasks if record.frontmatter.get("status") == status]
        if not matching:
            lines.append("| - | - | - | - | - | - | - |")
        for record in matching:
            fm = record.frontmatter
            lines.append(
                f"| `{table_cell(fm.get('id'))}` | {table_cell(fm.get('priority'))} | {table_cell(fm.get('assignee'))} | "
                f"{table_cell(fm.get('reviewer'))} | {table_cell(fm.get('updated'))} | {record_index_link(record)} | "
                f"{table_cell(fm.get('depends_on'))} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_agent_task_graph(records: list[Record]) -> str:
    tasks = sorted(agent_task_records(records), key=lambda record: as_scalar(record.frontmatter.get("id")))
    blockers: dict[str, list[str]] = {}
    for record in tasks:
        task_id = as_scalar(record.frontmatter.get("id"))
        for dependency in as_list(record.frontmatter.get("depends_on")):
            blockers.setdefault(as_scalar(dependency), []).append(task_id)

    lines = generated_header("Agent Task Graph")
    lines.extend(
        [
            "Dependency and blocker views are derived from task frontmatter.",
            "",
            "| ID | Status | Depends On | Blocks | Parent | Duplicate Of |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not tasks:
        lines.append("| - | - | - | - | - | - |")
    for record in tasks:
        fm = record.frontmatter
        task_id = as_scalar(fm.get("id"))
        lines.append(
            f"| {record_index_link(record)} | {table_cell(fm.get('status'))} | {table_cell(fm.get('depends_on'))} | "
            f"{table_cell(blockers.get(task_id, []))} | {table_cell(fm.get('parent'))} | {table_cell(fm.get('duplicate_of'))} |"
        )
    return "\n".join(lines) + "\n"


def build_index_outputs(records: list[Record]) -> dict[Path, str]:
    entities = build_entities(records)
    return {
        INDEX_DIR / "organizations.md": render_organizations(records, entities),
        INDEX_DIR / "projects.md": render_projects(records, entities),
        INDEX_DIR / "repositories.md": render_repositories(records, entities),
        INDEX_DIR / "topics.md": render_topics(records, entities),
        INDEX_DIR / "tools.md": render_tools(records, entities),
        INDEX_DIR / "people.md": render_people(records, entities),
        INDEX_DIR / "records.md": render_records_index(records),
        RECORDS_ROLLUP_MD_PATH: render_records_rollup(records),
        INDEX_DIR / "memory-summary.md": render_memory_summary(records),
        INDEX_DIR / "agent-task-queue.md": render_agent_task_queue(records),
        INDEX_DIR / "agent-task-graph.md": render_agent_task_graph(records),
        INDEX_DIR / "stale-candidates.md": render_stale_candidates_index(records),
        INDEX_DIR / "followups.md": render_followups_index(scan_unchecked_followups(FOLLOWUP_SCAN_ROOTS)),
        TASKS_DIR / "INDEX.md": render_task_index(records),
        RECORDS_JSON_PATH: records_json(records),
        RECORDS_COMPACT_JSON_PATH: records_compact_json(records),
    }


def unique_strings(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        value_str = as_scalar(value)
        if not value_str or value_str in seen:
            continue
        seen.add(value_str)
        result.append(value_str)
    return result


def write_many_to_link_table(conn: sqlite3.Connection, table: str, path: str, values: Iterable[Any]) -> None:
    conn.executemany(
        f"INSERT INTO {table} (path, value) VALUES (?, ?)",
        [(path, value) for value in unique_strings(values)],
    )


def write_sqlite_index(records: list[Record], db_path: Path = SQLITE_PATH) -> None:
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE records (
              path TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              summary TEXT,
              record_kind TEXT NOT NULL,
              status TEXT NOT NULL,
              date TEXT,
              organization TEXT,
              project TEXT,
              ticket TEXT,
              frontmatter_json TEXT NOT NULL
            );

            CREATE TABLE record_projects (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_repositories (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_topics (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_tools (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_people (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_ai_tools (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_prs (path TEXT NOT NULL, value TEXT NOT NULL);
            CREATE TABLE record_commits (path TEXT NOT NULL, value TEXT NOT NULL);

            CREATE INDEX idx_records_kind_status ON records(record_kind, status);
            CREATE INDEX idx_records_org ON records(organization);
            CREATE INDEX idx_records_project ON records(project);
            CREATE INDEX idx_records_ticket ON records(ticket);
            CREATE INDEX idx_record_projects_value ON record_projects(value);
            CREATE INDEX idx_record_repositories_value ON record_repositories(value);
            CREATE INDEX idx_record_topics_value ON record_topics(value);
            CREATE INDEX idx_record_tools_value ON record_tools(value);
            CREATE INDEX idx_record_people_value ON record_people(value);
            CREATE INDEX idx_record_ai_tools_value ON record_ai_tools(value);
            """
        )

        for record in records:
            fm = record.frontmatter
            path = record.relpath
            conn.execute(
                """
                INSERT INTO records (
                  path, title, summary, record_kind, status, date, organization, project, ticket, frontmatter_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    path,
                    record.title,
                    record_summary(record),
                    as_scalar(fm.get("record_kind")),
                    as_scalar(fm.get("status")),
                    record.date_sort or None,
                    fm.get("organization"),
                    fm.get("project"),
                    fm.get("ticket"),
                    json.dumps(fm, sort_keys=True, default=str),
                ),
            )
            write_many_to_link_table(conn, "record_projects", path, as_list(fm.get("project")) + as_list(fm.get("projects")))
            write_many_to_link_table(conn, "record_repositories", path, as_list(fm.get("repo")) + as_list(fm.get("repositories")))
            write_many_to_link_table(conn, "record_topics", path, as_list(fm.get("topic")) + as_list(fm.get("topics")))
            write_many_to_link_table(conn, "record_tools", path, as_list(fm.get("tool")) + as_list(fm.get("tools")))
            write_many_to_link_table(conn, "record_people", path, as_list(fm.get("person")) + as_list(fm.get("people")))
            write_many_to_link_table(conn, "record_ai_tools", path, as_list(fm.get("ai_tools")))
            write_many_to_link_table(conn, "record_prs", path, as_list(fm.get("prs")) + as_list(fm.get("related_prs")))
            write_many_to_link_table(conn, "record_commits", path, as_list(fm.get("commits")))

        conn.commit()
    finally:
        conn.close()


def run_dashboard_e2e() -> int:
    dashboard_dir = REPO_ROOT / "dashboard" / "tasks"
    if not dashboard_dir.exists():
        print("Dashboard e2e skipped: dashboard/tasks does not exist.", file=sys.stderr)
        return 0
    if not (dashboard_dir / "package.json").exists():
        print("Dashboard e2e skipped: dashboard/tasks/package.json does not exist.", file=sys.stderr)
        return 0
    try:
        completed = subprocess.run(["bun", "run", "test:e2e"], cwd=dashboard_dir, check=False)
    except FileNotFoundError:
        print("Dashboard e2e failed: bun is not installed.", file=sys.stderr)
        return 1
    return completed.returncode


def run_reindex(check: bool = False, dashboard_e2e: bool = False) -> int:
    records, parse_issues = load_records(include_parse_errors=True)
    issues = validate_loaded_records(records, parse_issues)
    if issues:
        print_issues(issues)
        return 1

    outputs = build_index_outputs(records)
    mismatches: list[Path] = []

    if check:
        for path, content in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                mismatches.append(path)
        if mismatches:
            print("Generated indexes are stale. Run `scripts/reindex.sh`.", file=sys.stderr)
            for path in mismatches:
                print(f"- {path.relative_to(REPO_ROOT).as_posix()}", file=sys.stderr)
            return 1
        print("Braingent indexes are current.")
        return run_dashboard_e2e() if dashboard_e2e else 0

    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    write_sqlite_index(records)
    print(f"Reindexed {len(records)} records and rebuilt .braingent.db.")
    return run_dashboard_e2e() if dashboard_e2e else 0


def print_issues(issues: list[ValidationIssue]) -> None:
    print(f"Braingent validation failed with {len(issues)} issue(s):", file=sys.stderr)
    for issue in issues:
        print(f"- {issue.format()}", file=sys.stderr)


def resolve_project_filter_value(value: str) -> str:
    if not value or value.startswith("project--"):
        return value

    direct = f"project--{value}"
    direct_matches = sorted((REPO_ROOT / "orgs").glob(f"*/projects/{direct}"))
    if len(direct_matches) == 1:
        return direct_matches[0].name

    suffix = f"project--*--{value}"
    suffix_matches = sorted((REPO_ROOT / "orgs").glob(f"*/projects/{suffix}"))
    if len(suffix_matches) == 1:
        return suffix_matches[0].name

    return direct


def resolve_repository_filter_value(value: str) -> str:
    if not value or value.startswith("repo--"):
        return value

    direct = f"repo--{value}"
    direct_path = REPO_ROOT / "repositories" / direct
    if direct_path.is_dir():
        return direct

    suffix = f"repo--*--{value}"
    suffix_matches = sorted((REPO_ROOT / "repositories").glob(suffix))
    if len(suffix_matches) == 1:
        return suffix_matches[0].name

    return direct


def normalize_filter(key: str, value: str) -> tuple[str, str]:
    aliases = {
        "kind": "record_kind",
        "org": "organization",
        "repo": "repositories",
        "repository": "repositories",
        "person": "people",
        "topic": "topics",
        "tool": "tools",
        "ai": "ai_tools",
        "ai_tool": "ai_tools",
        "pr": "prs",
        "commit": "commits",
        "q": "text",
    }
    key = aliases.get(key, key)
    if key in {"project", "projects"}:
        return key, resolve_project_filter_value(value)
    if key == "repositories":
        return key, resolve_repository_filter_value(value)
    prefix_by_key = {
        "organization": "org--",
        "people": "person--",
        "topics": "topic--",
        "tools": "tool--",
    }
    if key in prefix_by_key and value and not value.startswith(prefix_by_key[key]):
        value = prefix_by_key[key] + value
    if key == "ticket":
        value = value.upper()
    return key, value


def record_matches(record: Record, filters: dict[str, list[str]]) -> bool:
    text_filters = filters.get("text", [])
    for key, values in filters.items():
        if key == "text":
            continue
        fm_value = record.frontmatter.get(key)
        if key == "repositories":
            haystack = as_list(record.frontmatter.get("repositories")) + as_list(record.frontmatter.get("repo"))
        elif key == "people":
            haystack = as_list(record.frontmatter.get("people")) + as_list(record.frontmatter.get("person"))
        elif key == "topics":
            haystack = as_list(record.frontmatter.get("topics")) + as_list(record.frontmatter.get("topic"))
        elif key == "tools":
            haystack = as_list(record.frontmatter.get("tools")) + as_list(record.frontmatter.get("tool"))
        else:
            haystack = as_list(fm_value)
        haystack_strings = {as_scalar(item) for item in haystack}
        if not all(value in haystack_strings for value in values):
            return False

    body = record.body.lower()
    combined = (json.dumps(record.frontmatter, default=str).lower() + "\n" + body)
    return all(text.lower() in combined for text in text_filters)


def parse_find_filters(args: list[str]) -> dict[str, list[str]]:
    filters: dict[str, list[str]] = {}
    for arg in args:
        if "=" not in arg:
            key, value = "text", arg
        else:
            key, value = arg.split("=", 1)
        key, value = normalize_filter(key.strip(), value.strip())
        filters.setdefault(key, []).append(value)
    return filters


def run_find(
    args: list[str],
    output_json: bool = False,
    paths_only: bool = False,
    count_only: bool = False,
    limit: int | None = None,
) -> int:
    filters = parse_find_filters(args)
    records, parse_issues = load_records(include_parse_errors=False)
    if parse_issues:
        print_issues(parse_issues)
        return 1
    matched = [record for record in records if record_matches(record, filters)]
    matched.sort(key=lambda record: (record.date_sort, record.relpath), reverse=True)

    if count_only:
        print(len(matched))
        return 0
    output_records = matched[:limit] if limit is not None else matched
    if output_json:
        print(json.dumps([record_to_json(record) for record in output_records], indent=2, sort_keys=True, default=str))
        return 0
    if paths_only:
        for record in output_records:
            print(record.relpath)
        return 0

    if not matched:
        return 1

    print("| Path | Kind | Status | Date | Title |")
    print("| --- | --- | --- | --- | --- |")
    for record in output_records:
        print(
            f"| `{record.relpath}` | {display_value(record.kind)} | {display_value(record.status)} | "
            f"{display_value(record.date_sort)} | {record.title} |"
        )
    return 0


def record_priority(record: Record) -> int:
    kind = record.kind
    status = record.status
    if kind == "profile" and status == "active":
        return 0
    if kind == "decision" and status == "accepted":
        return 1
    if kind == "task" and status in {"active", "planned"}:
        return 2
    if kind == "learning" and status == "active":
        return 3
    if kind == "summary" and status == "completed":
        return 4
    if kind == "review" and status == "completed":
        return 5
    if kind == "task" and status == "completed":
        return 6
    return 9


def recall_sort_key(record: Record) -> tuple[int, int, str]:
    parsed = parse_date_value(record.date_sort)
    recency = -parsed.toordinal() if parsed else 0
    return (record_priority(record), recency, record.relpath)


def stale_reason(record: Record, stale_days: int, today: date | None = None) -> str | None:
    today = today or date.today()
    fm = record.frontmatter
    if record.kind == "profile":
        age = days_since(fm.get("last_reviewed"), today)
        if age is None:
            return "profile has no parseable last_reviewed"
        if age > stale_days:
            return f"profile last_reviewed is {age} days old"
    if record.kind == "learning":
        age = days_since(fm.get("last_revalidated"), today)
        if age is None:
            return "learning has no parseable last_revalidated"
        if age > stale_days:
            return f"learning last_revalidated is {age} days old"
    return None


def recall_classification(record: Record, stale_days: int) -> tuple[str, str]:
    if record.status in {"superseded", "draft", "archived", "rejected"}:
        return "do_not_use", f"status is {record.status}"
    stale = stale_reason(record, stale_days)
    if stale:
        return "stale_or_verify", stale
    return "candidate", "matched retrieval filters"


def infer_capture_target(records: list[Record], filters: dict[str, list[str]]) -> str:
    project_candidates: list[str] = []
    for key in ("project", "projects"):
        project_candidates.extend(filters.get(key, []))
    for record in records:
        project_candidates.extend(as_scalar(item) for item in as_list(record.frontmatter.get("project")))
        project_candidates.extend(as_scalar(item) for item in as_list(record.frontmatter.get("projects")))

    for project in unique_strings(project_candidates):
        for path in sorted((REPO_ROOT / "orgs").glob(f"*/projects/{project}")):
            records_dir = path / "records"
            if records_dir.is_dir():
                return records_dir.relative_to(REPO_ROOT).as_posix()

    repo_candidates = filters.get("repositories", [])
    if repo_candidates:
        all_records, _ = load_records(include_parse_errors=False)
        for repo in repo_candidates:
            profile = next((record for record in all_records if record.frontmatter.get("repo") == repo), None)
            if profile:
                project = profile.frontmatter.get("project")
                if project:
                    for path in sorted((REPO_ROOT / "orgs").glob(f"*/projects/{project}")):
                        records_dir = path / "records"
                        if records_dir.is_dir():
                            return records_dir.relative_to(REPO_ROOT).as_posix()

    return "Determine after identifying the primary org/project."


def recall_payload(filters: dict[str, list[str]], limit: int, stale_days: int) -> dict[str, Any]:
    records, parse_issues = load_records(include_parse_errors=False)
    if parse_issues:
        return {"errors": [issue.format() for issue in parse_issues]}

    matched = [record for record in records if record_matches(record, filters)]
    matched.sort(key=recall_sort_key)

    categories: dict[str, list[dict[str, Any]]] = {
        "must_read": [],
        "supporting": [],
        "stale_or_verify": [],
        "do_not_use": [],
    }

    candidate_items: list[dict[str, Any]] = []
    for record in matched:
        category, reason = recall_classification(record, stale_days)
        item = record_to_json(record)
        item["reason"] = reason
        if category == "candidate":
            candidate_items.append(item)
        else:
            categories[category].append(item)

    categories["must_read"] = candidate_items[:limit]
    categories["supporting"] = candidate_items[limit:]

    return {
        "filters": filters,
        "generated_on": date.today().isoformat(),
        "match_count": len(matched),
        **categories,
        "capture_target": infer_capture_target(matched, filters),
    }


def render_recall_markdown(payload: dict[str, Any]) -> str:
    if "errors" in payload:
        return "\n".join(["# Braingent Context Pack", "", "## Errors", *[f"- {error}" for error in payload["errors"]], ""])

    lines = [
        "# Braingent Context Pack",
        "",
        f"Generated: {payload['generated_on']}",
        f"Matches: {payload['match_count']}",
        "",
    ]
    for category in ("must_read", "supporting", "stale_or_verify", "do_not_use"):
        lines.extend([f"## {category}", ""])
        items = payload[category]
        if not items:
            lines.extend(["- None", ""])
            continue
        for item in items:
            date_label = display_value(item.get("date"))
            lines.append(
                f"- `{item['path']}` - {item['title']} "
                f"({item.get('record_kind')}/{item.get('status')}/{date_label})"
            )
            if item.get("summary"):
                lines.append(f"  Summary: {item['summary']}")
            lines.append(f"  Reason: {item.get('reason', 'matched retrieval filters')}")
        lines.append("")
    lines.extend(["## capture_target", "", f"- {payload['capture_target']}", ""])
    return "\n".join(lines)


def run_recall(filters_raw: list[str], output_json: bool = False, limit: int = 8, stale_days: int = 180) -> int:
    if not filters_raw:
        print("Provide at least one retrieval filter, e.g. `repo=github--example--app` or `ticket=EX-123`.", file=sys.stderr)
        return 2
    filters = parse_find_filters(filters_raw)
    payload = recall_payload(filters, limit=limit, stale_days=stale_days)
    if output_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print(render_recall_markdown(payload))
    return 1 if "errors" in payload else 0


def short_issue(path: Path, message: str) -> dict[str, str]:
    return {"path": path.relative_to(REPO_ROOT).as_posix(), "message": message}


def scan_unchecked_followups(roots: Iterable[str]) -> list[dict[str, str]]:
    regex = re.compile(r"^- \[ \]\s*(.+)")
    findings: list[dict[str, str]] = []
    for root_name in roots:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        paths = [root] if root.is_file() else sorted(root.rglob("*.md"))
        for path in paths:
            if not path.is_file() or path.suffix != ".md":
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            in_fence = False
            for line_number, line in enumerate(lines, start=1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                match = regex.match(line)
                if match:
                    findings.append(
                        {
                            "path": path.relative_to(REPO_ROOT).as_posix(),
                            "line": str(line_number),
                            "message": "unchecked follow-up",
                            "text": match.group(1).strip(),
                        }
                    )
    return findings


def render_followups_index(followups: list[dict[str, str]]) -> str:
    lines = generated_header("Follow-up Index")
    lines.extend(
        [
            "This generated index collects unchecked follow-ups from durable records.",
            "Use it as the maintenance queue for deliberate current work;",
            "archive stale reminders as plain bullets.",
            "",
            f"Open follow-ups: {len(followups)}",
            "",
            "| Source | Line | Follow-up |",
            "| --- | ---: | --- |",
        ]
    )
    for item in followups:
        path = item["path"]
        source = f"[{path}](../{path})"
        lines.append(f"| {source} | {item['line']} | {table_cell(item.get('text', ''))} |")
    return "\n".join(lines) + "\n"


def scan_markdown_patterns(pattern: str, roots: Iterable[str]) -> list[dict[str, str]]:
    regex = re.compile(pattern)
    findings: list[dict[str, str]] = []
    for root_name in roots:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        paths = [root] if root.is_file() else sorted(root.rglob("*.md"))
        for path in paths:
            if not path.is_file() or path.suffix != ".md":
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            in_fence = False
            for line_number, line in enumerate(lines, start=1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                if regex.search(line):
                    findings.append(
                        {
                            "path": path.relative_to(REPO_ROOT).as_posix(),
                            "line": str(line_number),
                            "message": regex.pattern,
                        }
                    )
    return findings


def index_mismatches(records: list[Record]) -> list[dict[str, str]]:
    outputs = build_index_outputs(records)
    mismatches: list[dict[str, str]] = []
    for path, content in outputs.items():
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            mismatches.append(short_issue(path, "generated index is stale"))
    return mismatches


def doctor_payload(stale_days: int = 180) -> dict[str, Any]:
    validation_issues = validate()
    records, parse_issues = load_records(include_parse_errors=True)
    today = date.today()
    warnings: list[dict[str, str]] = []

    for issue in parse_issues:
        warnings.append(short_issue(issue.path, issue.message))

    for record in records:
        stale = stale_reason(record, stale_days, today)
        if stale:
            warnings.append(short_issue(record.path, stale))

        raw_until = record.frontmatter.get("raw_retained_until")
        if raw_until and as_scalar(raw_until).lower() != "never":
            retained_until = parse_date_value(raw_until)
            if retained_until and retained_until < today:
                warnings.append(short_issue(record.path, f"raw_retained_until expired on {retained_until.isoformat()}"))

        if record.kind == "summary":
            retrieval_fields = [
                record.frontmatter.get("organization"),
                record.frontmatter.get("project"),
                record.frontmatter.get("repo"),
                record.frontmatter.get("repositories"),
                record.frontmatter.get("topic"),
                record.frontmatter.get("topics"),
            ]
            if not any(as_list(value) for value in retrieval_fields if value is not None):
                warnings.append(short_issue(record.path, "summary has no org/project/repo/topic retrieval metadata"))

    unchecked = scan_unchecked_followups(FOLLOWUP_SCAN_ROOTS)
    placeholders = scan_markdown_patterns(r"\b(TODO|FIXME|PLACEHOLDER|XXX)\b", ["."])
    possible_secrets = scan_markdown_patterns(
        r"(?i)((api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}|BEGIN .*PRIVATE KEY)",
        ["."],
    )

    return {
        "generated_on": today.isoformat(),
        "hard_failures": {
            "validation": [issue.format() for issue in validation_issues],
            "stale_indexes": index_mismatches(records),
            "possible_secrets": possible_secrets,
        },
        "warnings": {
            "metadata_and_freshness": warnings,
            "unchecked_followups": unchecked,
            "placeholders": placeholders,
        },
        "counts": {
            "records": len(records),
            "validation_issues": len(validation_issues),
            "stale_indexes": len(index_mismatches(records)),
            "possible_secrets": len(possible_secrets),
            "metadata_and_freshness": len(warnings),
            "unchecked_followups": len(unchecked),
            "placeholders": len(placeholders),
        },
    }


def render_doctor_markdown(payload: dict[str, Any], max_items: int = 20) -> str:
    lines = ["# Braingent Doctor", "", f"Generated: {payload['generated_on']}", ""]
    counts = payload["counts"]
    lines.extend(
        [
            "## Summary",
            "",
            f"- Records: {counts['records']}",
            f"- Validation issues: {counts['validation_issues']}",
            f"- Stale indexes: {counts['stale_indexes']}",
            f"- Possible secrets: {counts['possible_secrets']}",
            f"- Metadata/freshness warnings: {counts['metadata_and_freshness']}",
            f"- Unchecked follow-ups: {counts['unchecked_followups']}",
            f"- Placeholders/TODO markers: {counts['placeholders']}",
            "",
        ]
    )

    for section, values in payload["hard_failures"].items():
        lines.extend([f"## Hard Failure: {section}", ""])
        if not values:
            lines.extend(["- None", ""])
            continue
        for item in values[:max_items]:
            if isinstance(item, str):
                lines.append(f"- {item}")
            else:
                suffix = f":{item['line']}" if "line" in item else ""
                lines.append(f"- `{item['path']}{suffix}` - {item['message']}")
        if len(values) > max_items:
            lines.append(f"- ... {len(values) - max_items} more")
        lines.append("")

    for section, values in payload["warnings"].items():
        lines.extend([f"## Warning: {section}", ""])
        if not values:
            lines.extend(["- None", ""])
            continue
        for item in values[:max_items]:
            suffix = f":{item['line']}" if "line" in item else ""
            message = item.get("text") or item["message"]
            lines.append(f"- `{item['path']}{suffix}` - {message}")
        if len(values) > max_items:
            lines.append(f"- ... {len(values) - max_items} more")
        lines.append("")

    return "\n".join(lines)


def run_doctor(output_json: bool = False, strict: bool = False, stale_days: int = 180) -> int:
    payload = doctor_payload(stale_days=stale_days)
    if output_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print(render_doctor_markdown(payload))
    hard_count = (
        payload["counts"]["validation_issues"]
        + payload["counts"]["stale_indexes"]
        + payload["counts"]["possible_secrets"]
    )
    warning_count = payload["counts"]["metadata_and_freshness"] + payload["counts"]["placeholders"]
    if hard_count:
        return 1
    if strict and warning_count:
        return 1
    return 0


def synthesis_scope(args: argparse.Namespace) -> tuple[str, str, tuple[str, ...], str]:
    provided = [value for value in (args.topic, args.repo, args.project) if value]
    if len(provided) != 1:
        raise SystemExit("Provide exactly one of --topic, --repo, or --project.")
    if args.topic:
        value = args.topic if args.topic.startswith("topic--") else f"topic--{args.topic}"
        return "topics", value, ("topic", "topics"), "Topic"
    if args.repo:
        value = args.repo if args.repo.startswith("repo--") else f"repo--{args.repo}"
        return "repositories", value, ("repo", "repositories"), "Repository"
    value = args.project
    return "projects", value, ("project", "projects"), "Project"


def render_synthesis(scope_label: str, key: str, records: list[Record], output_path: Path) -> str:
    lines = [
        f"# Synthesis: {key}",
        "",
        "<!-- Derived synthesis. Durable records remain source of truth. -->",
        "",
        f"Generated: {date.today().isoformat()}",
        f"Scope: {scope_label} `{key}`",
        "",
        "This page is a generated, source-indexed synthesis map. It may paraphrase",
        "source records for scanability; durable records remain the receipts.",
        "",
    ]
    grouped: dict[str, list[Record]] = {}
    for record in records:
        grouped.setdefault(record.kind or "unknown", []).append(record)
    for kind in sorted(grouped):
        lines.extend([f"## {kind.title()} Records", ""])
        for record in sorted(grouped[kind], key=lambda item: (item.date_sort, item.relpath), reverse=True):
            rel = Path(os.path.relpath(record.path, start=output_path.parent)).as_posix()
            lines.append(f"- [{record.title}]({rel}) - `{record.status}` - {display_value(record.date_sort)}")
            summary = record_summary(record)
            if summary:
                lines.append(f"  - {summary}")
        lines.append("")
    lines.extend(["## Source Records", ""])
    for record in sorted(records, key=lambda item: item.relpath):
        lines.append(f"- `{record.relpath}`")
    lines.append("")
    return "\n".join(lines)


def run_synthesize(args: argparse.Namespace) -> int:
    scope_dir, key, fields, scope_label = synthesis_scope(args)
    records, parse_issues = load_records(include_parse_errors=False)
    if parse_issues:
        print_issues(parse_issues)
        return 1
    matched = records_for_entity(records, *fields, value=key)
    if not matched:
        print(f"No records found for {scope_label.lower()} `{key}`.", file=sys.stderr)
        return 1
    output_dir = REPO_ROOT / "synthesis" / scope_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{key}.md"
    output_path.write_text(render_synthesis(scope_label, key, matched, output_path), encoding="utf-8")
    print(output_path.relative_to(REPO_ROOT).as_posix())
    return 0


def path_args(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if not path.is_absolute():
            path = REPO_ROOT / path
        if any(fnmatch.fnmatch(part, ".git") for part in path.parts):
            continue
        paths.append(path)
    return paths


def slugify_task_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "task"


def next_agent_task_id() -> str:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    next_id_path = TASKS_DIR / ".next-id"
    if next_id_path.exists():
        raw = next_id_path.read_text(encoding="utf-8").strip()
        number = int(raw) if raw else 1
    else:
        max_seen = 0
        for path in TASKS_DIR.rglob("BGT-*.md"):
            match = re.match(r"BGT-([0-9]{4,})--", path.name)
            if match:
                max_seen = max(max_seen, int(match.group(1)))
        number = max_seen + 1
    next_id_path.write_text(f"{number + 1}\n", encoding="utf-8")
    return f"BGT-{number:04d}"


def write_markdown_record(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    dumped = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=False).strip()
    path.write_text(f"---\n{dumped}\n---\n{body}", encoding="utf-8")


def task_files() -> list[Path]:
    if not TASKS_DIR.exists():
        return []
    return sorted(TASKS_DIR.glob("active/BGT-*.md")) + sorted(TASKS_DIR.glob("archive/*/BGT-*.md"))


def load_task_record(task_id: str) -> Record:
    normalized = task_id.upper()
    for path in task_files():
        frontmatter, body, error = split_frontmatter(path)
        if error:
            raise SystemExit(f"{path.relative_to(REPO_ROOT)}: {error}")
        if frontmatter and frontmatter.get("id") == normalized:
            return Record(path=path, frontmatter=frontmatter, body=body)
    raise SystemExit(f"Unknown agent task `{task_id}`.")


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def append_task_activity(body: str, actor: str, role: str, event: str, note: str) -> str:
    entry = f"- {now_iso()} | {actor} | role:{role} | event:{event} |\n  {note.strip()}\n"
    if "## Activity\n" not in body:
        return body.rstrip() + "\n\n## Activity\n\n" + entry
    activity_start = body.index("## Activity\n")
    next_heading = body.find("\n## ", activity_start + len("## Activity\n"))
    if next_heading == -1:
        return body.rstrip() + "\n\n" + entry
    return body[:next_heading].rstrip() + "\n\n" + entry + body[next_heading:]


def update_task_record(record: Record, frontmatter: dict[str, Any], body: str) -> None:
    frontmatter["updated"] = today_iso()
    write_markdown_record(record.path, frontmatter, body)


def default_task_body(task_id: str, actor: str) -> str:
    return f"""## Description

Describe what is being asked and why.

## Acceptance Criteria

- [ ] Verifiable success condition.

## Plan

1. Define the next concrete step.
   - -> verify: observable check.

## Dependencies

- Depends on: none
- Derived blockers: generated in `indexes/agent-task-graph.md`

## Activity

<!-- Append-only. Newest entries at the bottom. Never edit prior entries. -->

- {now_iso()} | {actor} | role:assignee | event:created |
  Created {task_id}.

## Linked Evidence

- Durable records:
- PRs:
- Commits:
- Commands:
"""


def cmd_task_new(args: argparse.Namespace) -> int:
    actor = args.assignee or args.as_agent or "agent--codex-cli"
    task_id = next_agent_task_id()
    path = TASKS_DIR / "active" / f"{task_id}--{slugify_task_title(args.title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    today = today_iso()
    repositories = args.repository or ["repo--example--owner--repo"]
    topics = args.topic or ["topic--ai-agent-memory"]
    ai_tools = args.ai_tool or ["Codex"]
    frontmatter: dict[str, Any] = {
        "id": task_id,
        "title": args.title,
        "record_kind": "agent-task",
        "status": "todo",
        "status_category": "active",
        "resolution": None,
        "type": args.type,
        "priority": args.priority,
        "assignee": args.assignee,
        "reviewer": args.reviewer,
        "observers": [],
        "claimed_by": None,
        "claimed_at": None,
        "created": today,
        "updated": today,
        "date": today,
        "timezone": "Asia/Singapore",
        "organization": args.organization,
        "project": args.project,
        "repositories": repositories,
        "ticket": args.ticket,
        "prs": [],
        "commits": [],
        "ai_tools": ai_tools,
        "people": [],
        "topics": topics,
        "tools": [],
        "parent": args.parent,
        "depends_on": args.depends_on,
        "duplicate_of": None,
        "closed": None,
        "visibility": args.visibility,
    }
    write_markdown_record(path, frontmatter, default_task_body(task_id, actor))
    print(path.relative_to(REPO_ROOT).as_posix())
    return 0


def cmd_task_claim(args: argparse.Namespace) -> int:
    record = load_task_record(args.id)
    fm = dict(record.frontmatter)
    fm["assignee"] = args.as_agent
    fm["claimed_by"] = args.as_agent
    fm["claimed_at"] = now_iso()
    if fm.get("status") in {"triage", "todo"}:
        fm["status"] = "in-progress"
        fm["status_category"] = "active"
    body = append_task_activity(record.body, args.as_agent, "assignee", "claimed", args.note or "Claimed task.")
    update_task_record(record, fm, body)
    print(record.path.relative_to(REPO_ROOT).as_posix())
    return 0


def cmd_task_comment(args: argparse.Namespace) -> int:
    record = load_task_record(args.id)
    body = append_task_activity(record.body, args.as_agent, args.role, "commented", args.message)
    update_task_record(record, dict(record.frontmatter), body)
    print(record.path.relative_to(REPO_ROOT).as_posix())
    return 0


def cmd_task_status(args: argparse.Namespace) -> int:
    record = load_task_record(args.id)
    if args.status == "closed" and not args.resolution:
        raise SystemExit("task-status closed requires --resolution.")
    if args.status != "closed" and args.resolution:
        raise SystemExit("--resolution is only valid when status is closed.")
    if args.resolution == "duplicate" and not args.duplicate_of:
        raise SystemExit("--resolution duplicate requires --duplicate-of.")
    fm = dict(record.frontmatter)
    fm["status"] = args.status
    fm["status_category"] = AGENT_TASK_STATUS_CATEGORIES[args.status]
    if args.status == "closed":
        fm["resolution"] = args.resolution
        fm["closed"] = today_iso()
        fm["duplicate_of"] = args.duplicate_of
    else:
        fm["resolution"] = None
        fm["closed"] = None
        fm["duplicate_of"] = None
    event = "closed" if args.status == "closed" else "status-changed"
    body = append_task_activity(record.body, args.as_agent, args.role, event, args.note or f"Status changed to {args.status}.")
    update_task_record(record, fm, body)
    print(record.path.relative_to(REPO_ROOT).as_posix())
    return 0


def cmd_task_list(args: argparse.Namespace) -> int:
    rows: list[Record] = []
    for path in task_files():
        frontmatter, body, error = split_frontmatter(path)
        if error or not frontmatter:
            continue
        record = Record(path=path, frontmatter=frontmatter, body=body)
        fm = record.frontmatter
        if args.status and fm.get("status") != args.status:
            continue
        if args.assignee and fm.get("assignee") != args.assignee:
            continue
        if args.reviewer and fm.get("reviewer") != args.reviewer:
            continue
        rows.append(record)
    if args.count:
        print(agent_task_count_line(rows))
        return 0
    for record in sorted(rows, key=agent_task_sort_key):
        fm = record.frontmatter
        print(
            f"{fm.get('id')}\t{fm.get('status')}\t{fm.get('priority')}\t"
            f"{display_value(fm.get('assignee'))}\t{record.relpath}\t{record.title}"
        )
    return 0


def cmd_task_archive(args: argparse.Namespace) -> int:
    record = load_task_record(args.id)
    fm = dict(record.frontmatter)
    body = record.body
    if fm.get("status") != "closed":
        if not args.resolution:
            raise SystemExit("task-archive requires --resolution unless task is already closed.")
        if args.resolution == "duplicate" and not args.duplicate_of:
            raise SystemExit("--resolution duplicate requires --duplicate-of.")
        fm["status"] = "closed"
        fm["status_category"] = "closed"
        fm["resolution"] = args.resolution
        fm["duplicate_of"] = args.duplicate_of
        fm["closed"] = today_iso()
        body = append_task_activity(body, args.as_agent, args.role, "closed", args.note or "Closed task.")
    archive_dir = TASKS_DIR / "archive" / today_iso()[:7]
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / record.path.name
    fm["updated"] = today_iso()
    write_markdown_record(record.path, fm, body)
    if record.path != target:
        record.path.rename(target)
    archived_record = Record(path=target, frontmatter=fm, body=body)
    archived_body = append_task_activity(archived_record.body, args.as_agent, args.role, "archived", args.note or "Archived task.")
    write_markdown_record(target, fm, archived_body)
    print(target.relative_to(REPO_ROOT).as_posix())
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    issues = validate(path_args(args.paths) if args.paths else None)
    if issues:
        print_issues(issues)
        return 1
    print("Braingent validation passed.")
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    return run_reindex(check=args.check, dashboard_e2e=args.dashboard_e2e)


def cmd_find(args: argparse.Namespace) -> int:
    return run_find(args.filters, output_json=args.json, paths_only=args.paths, count_only=args.count, limit=args.limit)


def cmd_recall(args: argparse.Namespace) -> int:
    return run_recall(args.filters, output_json=args.json, limit=args.limit, stale_days=args.stale_days)


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_doctor(output_json=args.json, strict=args.strict, stale_days=args.stale_days)


def cmd_synthesize(args: argparse.Namespace) -> int:
    return run_synthesize(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Braingent metadata helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate record frontmatter")
    validate_parser.add_argument("paths", nargs="*", help="optional Markdown files to validate")
    validate_parser.set_defaults(func=cmd_validate)

    reindex_parser = subparsers.add_parser("reindex", help="regenerate derived indexes")
    reindex_parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    reindex_parser.add_argument("--dashboard-e2e", action="store_true", help="run dashboard Playwright e2e after index checks")
    reindex_parser.set_defaults(func=cmd_reindex)

    find_parser = subparsers.add_parser("find", help="search records by structured filters")
    find_parser.add_argument("filters", nargs="*", help="filters like kind=decision org=example topic=ai-memory")
    find_parser.add_argument("--json", action="store_true", help="emit JSON")
    find_parser.add_argument("--paths", action="store_true", help="emit only paths")
    find_parser.add_argument("--count", action="store_true", help="emit only count")
    find_parser.add_argument("--limit", type=int, help="maximum results to emit")
    find_parser.set_defaults(func=cmd_find)

    recall_parser = subparsers.add_parser("recall", help="build a focused context pack")
    recall_parser.add_argument("filters", nargs="*", help="filters like repo=github--example--app ticket=EX-123")
    recall_parser.add_argument("--json", action="store_true", help="emit JSON")
    recall_parser.add_argument("--limit", type=int, default=8, help="number of must_read records to return")
    recall_parser.add_argument("--stale-days", type=int, default=180, help="age threshold for stale profile/learning records")
    recall_parser.set_defaults(func=cmd_recall)

    doctor_parser = subparsers.add_parser("doctor", help="report Braingent health checks")
    doctor_parser.add_argument("--json", action="store_true", help="emit JSON")
    doctor_parser.add_argument("--strict", action="store_true", help="exit non-zero on warnings")
    doctor_parser.add_argument("--stale-days", type=int, default=180, help="age threshold for stale profile/learning records")
    doctor_parser.set_defaults(func=cmd_doctor)

    synthesize_parser = subparsers.add_parser("synthesize", help="generate source-indexed synthesis pages")
    synthesize_scope_group = synthesize_parser.add_mutually_exclusive_group(required=True)
    synthesize_scope_group.add_argument("--topic", help="topic key, with or without topic-- prefix")
    synthesize_scope_group.add_argument("--repo", help="repository key, with or without repo-- prefix")
    synthesize_scope_group.add_argument("--project", help="project key")
    synthesize_parser.set_defaults(func=cmd_synthesize)

    task_new_parser = subparsers.add_parser("task-new", help="create an agent task")
    task_new_parser.add_argument("title")
    task_new_parser.add_argument("--type", default="task", choices=["task", "bug", "feature", "review", "decision", "spike", "chore"])
    task_new_parser.add_argument("--priority", default="medium", choices=["critical", "high", "medium", "low"])
    task_new_parser.add_argument("--assignee")
    task_new_parser.add_argument("--reviewer")
    task_new_parser.add_argument("--as", dest="as_agent")
    task_new_parser.add_argument("--organization", default="org--example")
    task_new_parser.add_argument("--project", default="project--example--memory")
    task_new_parser.add_argument("--repository", action="append")
    task_new_parser.add_argument("--topic", action="append")
    task_new_parser.add_argument("--ai-tool", action="append")
    task_new_parser.add_argument("--ticket")
    task_new_parser.add_argument("--parent")
    task_new_parser.add_argument("--depends-on", action="append", default=[])
    task_new_parser.add_argument("--visibility", default="private", choices=["private", "shareable", "public"])
    task_new_parser.set_defaults(func=cmd_task_new)

    task_claim_parser = subparsers.add_parser("task-claim", help="claim an agent task")
    task_claim_parser.add_argument("id")
    task_claim_parser.add_argument("--as", dest="as_agent", required=True)
    task_claim_parser.add_argument("--note")
    task_claim_parser.set_defaults(func=cmd_task_claim)

    task_comment_parser = subparsers.add_parser("task-comment", help="append an agent task activity comment")
    task_comment_parser.add_argument("id")
    task_comment_parser.add_argument("message")
    task_comment_parser.add_argument("--as", dest="as_agent", required=True)
    task_comment_parser.add_argument("--role", default="commenter")
    task_comment_parser.set_defaults(func=cmd_task_comment)

    task_status_parser = subparsers.add_parser("task-status", help="change an agent task status")
    task_status_parser.add_argument("id")
    task_status_parser.add_argument("status", choices=["triage", "todo", "in-progress", "in-review", "blocked", "closed"])
    task_status_parser.add_argument("--as", dest="as_agent", required=True)
    task_status_parser.add_argument("--role", default="assignee")
    task_status_parser.add_argument("--note")
    task_status_parser.add_argument("--resolution", choices=["completed", "wont_do", "duplicate", "superseded"])
    task_status_parser.add_argument("--duplicate-of")
    task_status_parser.set_defaults(func=cmd_task_status)

    task_list_parser = subparsers.add_parser("task-list", help="list agent tasks")
    task_list_parser.add_argument("--status", choices=["triage", "todo", "in-progress", "in-review", "blocked", "closed"])
    task_list_parser.add_argument("--assignee")
    task_list_parser.add_argument("--reviewer")
    task_list_parser.add_argument("--count", action="store_true", help="emit status counts only")
    task_list_parser.set_defaults(func=cmd_task_list)

    task_archive_parser = subparsers.add_parser("task-archive", help="close and archive an agent task")
    task_archive_parser.add_argument("id")
    task_archive_parser.add_argument("--resolution", choices=["completed", "wont_do", "duplicate", "superseded"])
    task_archive_parser.add_argument("--duplicate-of")
    task_archive_parser.add_argument("--as", dest="as_agent", required=True)
    task_archive_parser.add_argument("--role", default="assignee")
    task_archive_parser.add_argument("--note")
    task_archive_parser.set_defaults(func=cmd_task_archive)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

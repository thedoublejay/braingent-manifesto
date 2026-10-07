"""Epics: ad hoc groupings of work around one idea, anchored by a mutable page.

An epic lives at `orgs/<org>/epics/epic--<org>--<slug>/README.md`. Records join
an epic with an `epic:` frontmatter list of epic ids. The page links to tickets
and PRs, records cross-cutting decisions and keeps the config-to-enable ledger.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from braingent import config_ledger, core
from braingent.config_ledger import ConfigItem, ConfigLedgerError

EPIC_PREFIX = "epic--"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_WORDS = 4
DEFAULT_STATUSES = ("active", "paused", "done", "dropped")
DEFAULT_REQUIRED_FIELDS = ("title", "epic", "organization", "status", "created", "updated")
EPIC_TEMPLATE = Path("templates") / "epic.md"
FRONTMATTER_PATTERN = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)


@dataclass(frozen=True)
class Epic:
    record: core.Record

    @property
    def id(self) -> str:
        return self.record.path.parent.name

    @property
    def slug(self) -> str:
        return slug_of(self.id)

    @property
    def organization(self) -> str:
        return core.as_scalar(self.record.frontmatter.get("organization"))

    @property
    def status(self) -> str:
        return self.record.status

    @property
    def parent(self) -> str:
        value = self.record.frontmatter.get("parent_epic")
        return "" if core.is_nullish(value) else core.as_scalar(value)

    @property
    def updated(self) -> str:
        return core.as_scalar(self.record.frontmatter.get("updated"))

    @property
    def title(self) -> str:
        return self.record.title

    def config_items(self) -> list[ConfigItem]:
        return config_ledger.parse_blocks(self.record.body)


def validate_slug(value: str) -> str:
    slug = value.strip()
    if not SLUG_PATTERN.match(slug):
        raise ValueError(f"epic slug `{value}` must be lowercase kebab-case matching ^[a-z0-9][a-z0-9-]*$")
    if len(slug.split("-")) > MAX_SLUG_WORDS:
        raise ValueError(f"epic slug `{value}` must be {MAX_SLUG_WORDS} words or fewer")
    return slug


def slug_of(value: str) -> str:
    """Accept a bare slug or a full `epic--<org>--<slug>` id and return the slug."""

    text = value.strip()
    return text.rsplit("--", 1)[-1] if text.startswith(EPIC_PREFIX) else text


def epic_id(org: str, slug: str) -> str:
    return f"{EPIC_PREFIX}{org.removeprefix('org--')}--{validate_slug(slug)}"


def is_epic_page(record: core.Record) -> bool:
    try:
        parts = record.path.relative_to(core.REPO_ROOT).parts
    except ValueError:
        return False
    return (
        len(parts) == 5
        and parts[0] == "orgs"
        and parts[2] == "epics"
        and parts[3].startswith(EPIC_PREFIX)
        and parts[4] == "README.md"
    )


def epics_from_records(records: list[core.Record]) -> list[Epic]:
    return sorted((Epic(record) for record in records if is_epic_page(record)), key=lambda epic: epic.id)


def load_epics() -> list[Epic]:
    records, _ = core.load_records()
    return epics_from_records(records)


def resolve_epic_id(value: str) -> str:
    """Resolve a bare slug or id to an existing epic id; fall back to `epic--<value>`."""

    if not value or value.startswith(EPIC_PREFIX):
        return value
    matches = sorted(core.REPO_ROOT.glob(f"orgs/*/epics/{EPIC_PREFIX}*--{value}"))
    if len(matches) == 1:
        return matches[0].name
    return f"{EPIC_PREFIX}{value}"


def find_epic(epics: list[Epic], value: str) -> Epic:
    resolved = resolve_epic_id(value)
    matches = [epic for epic in epics if epic.id == resolved or (not value.startswith(EPIC_PREFIX) and epic.slug == value)]
    if not matches:
        raise LookupError(f"no epic matches `{value}`")
    if len(matches) > 1:
        raise LookupError(f"`{value}` is ambiguous: {', '.join(epic.id for epic in matches)}; pass the full id")
    return matches[0]


def member_records(records: list[core.Record], epic: Epic) -> list[core.Record]:
    return [
        record
        for record in records
        if not is_epic_page(record) and epic.id in {core.as_scalar(item) for item in core.as_list(record.frontmatter.get("epic"))}
    ]


def validate_epic_page(record: core.Record, taxonomy: dict[str, Any]) -> list[core.ValidationIssue]:
    fm = record.frontmatter
    path = record.path
    issues: list[core.ValidationIssue] = []

    required = taxonomy.get("required_fields", {}).get("epic", DEFAULT_REQUIRED_FIELDS)
    for name in required:
        if core.is_nullish(fm.get(name)):
            issues.append(core.ValidationIssue(path, f"missing required field `{name}` for epic"))

    if fm.get("record_kind") != "profile":
        issues.append(core.ValidationIssue(path, "epic page `record_kind` must be `profile`"))

    directory = path.parent.name
    declared = core.as_scalar(fm.get("epic"))
    if declared and declared != directory:
        issues.append(core.ValidationIssue(path, f"`epic` value `{declared}` does not match directory `{directory}`"))
    try:
        slug = validate_slug(slug_of(directory))
    except ValueError as exc:
        issues.append(core.ValidationIssue(path, str(exc)))
        slug = slug_of(directory)

    statuses = taxonomy.get("statuses", {}).get("epic", DEFAULT_STATUSES)
    status = core.as_scalar(fm.get("status"))
    if status and status not in statuses:
        issues.append(core.ValidationIssue(path, f"invalid status `{status}` for epic; allowed: {', '.join(statuses)}"))

    for name in ("organization", "parent_epic"):
        value = fm.get(name)
        spec = taxonomy.get("entity_fields", {}).get(name)
        if spec and not core.is_nullish(value):
            issues.extend(core.validate_entity_values(core.Record(path, fm, record.body), name, value, spec))

    labels = [core.as_scalar(item) for item in core.as_list(fm.get("labels"))]
    if labels and f"epic:{slug}" not in labels:
        issues.append(core.ValidationIssue(path, f"`labels` should include `epic:{slug}`", severity="warning"))

    if config_ledger.config_section(record.body) is None:
        issues.append(
            core.ValidationIssue(
                path,
                f"missing `{config_ledger.SECTION_HEADING}` section; write `None` when nothing must be set",
                severity="warning",
            )
        )
    try:
        config_ledger.parse_blocks(record.body)
    except ConfigLedgerError as exc:
        issues.append(core.ValidationIssue(path, f"malformed config-to-enable block: {exc}"))
    return issues


def render_epics_index(records: list[core.Record], epics: list[Epic]) -> str:
    lines = core.generated_header("Epic Index")
    lines.extend(
        [
            "| Epic | Key | Status | Parent | Records | Open Config Items | Updated |",
            "| --- | --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for epic in epics:
        try:
            open_items = sum(1 for item in epic.config_items() if item.is_open)
        except ConfigLedgerError:
            open_items = 0
        name = core.index_link(epic.title, epic.record.path)
        lines.append(
            f"| {name} | `{epic.id}` | {core.display_value(epic.status)} | {core.display_value(epic.parent)} | "
            f"{len(member_records(records, epic))} | {open_items} | {core.display_value(epic.updated)} |"
        )
    return "\n".join(lines) + "\n"


def render_config_ledger(epics: list[Epic]) -> str:
    lines = core.generated_header("Config Ledger")
    lines.append("Config that must be set before epic work is live. Values stay in source control or a secret store.")
    lines.append("")
    rendered = False
    for epic in epics:
        try:
            items = epic.config_items()
        except ConfigLedgerError:
            continue
        if not items:
            continue
        rendered = True
        lines.extend([f"## {epic.id}", "", *config_ledger.render_table(items), ""])
    if not rendered:
        lines.extend(["No config items recorded.", ""])
    return "\n".join(lines).rstrip("\n") + "\n"


def render_active_epics(epics: list[Epic]) -> list[str]:
    active = [epic for epic in epics if epic.status == "active"]
    lines = ["", "## Active epics", ""]
    if not active:
        return [*lines, "- None"]
    for epic in active:
        lines.append(f"- `{epic.id}`: {epic.title}")
    return lines


def config_item_rows(epics: list[Epic]) -> list[tuple[str, ConfigItem]]:
    rows: list[tuple[str, ConfigItem]] = []
    for epic in epics:
        try:
            rows.extend((epic.id, item) for item in epic.config_items())
        except ConfigLedgerError:
            continue
    return rows


def scaffold_epic(
    root: Path,
    org: str,
    slug: str,
    *,
    title: str | None = None,
    parent: str | None = None,
    today: date | None = None,
) -> Path:
    org_key = org if org.startswith("org--") else f"org--{org}"
    if not (root / "orgs" / org_key).is_dir():
        raise FileNotFoundError(f"organization `{org_key}` does not exist under orgs/")
    identifier = epic_id(org_key, slug)
    directory = root / "orgs" / org_key / "epics" / identifier
    if directory.exists():
        raise FileExistsError(f"{directory.relative_to(root).as_posix()} already exists")
    template_path = root / EPIC_TEMPLATE
    if not template_path.is_file():
        raise FileNotFoundError(f"missing template {EPIC_TEMPLATE.as_posix()}")
    parent_value = "null"
    if parent:
        parent_value = parent if parent.startswith(EPIC_PREFIX) else epic_id(org_key, parent)
    stamp = (today or date.today()).isoformat()
    text = template_path.read_text(encoding="utf-8")
    replacements = {
        "<epic-title>": title or slug.replace("-", " ").capitalize(),
        "<epic-id>": identifier,
        "<org-key>": org_key,
        "<slug>": slug,
        "<parent-epic-id-or-null>": parent_value,
        "<yyyy-mm-dd>": stamp,
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    directory.mkdir(parents=True)
    page = directory / "README.md"
    page.write_text(text, encoding="utf-8")
    return page


def with_ledger_section(rendered: str, epic_key: str, records: list[core.Record]) -> str:
    """Insert the epic page's config ledger before `## Source Records` in a synthesis page."""

    page = next((record for record in records if is_epic_page(record) and record.path.parent.name == epic_key), None)
    if page is None:
        return rendered
    try:
        items = config_ledger.parse_blocks(page.body)
    except ConfigLedgerError:
        return rendered
    table = config_ledger.render_table(items) if items else ["- None"]
    section = "\n".join(["## Config To Enable", "", *table, "", "## Source Records"])
    return rendered.replace("## Source Records", section, 1)


def default_gh_runner(arguments: list[str]) -> str:
    completed = subprocess.run(["gh", *arguments], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise ConfigLedgerError(f"gh {' '.join(arguments[:2])} failed: {completed.stderr.strip() or completed.returncode}")
    return completed.stdout


def run_config_ledger(
    epic_value: str,
    owners: list[str],
    *,
    sync: bool = False,
    output_json: bool = False,
    runner: Callable[[list[str]], str] = default_gh_runner,
) -> int:
    records, parse_issues = core.load_records(include_parse_errors=False)
    if parse_issues:
        core.print_issues(parse_issues)
        return 1
    try:
        epic = find_epic(epics_from_records(records), epic_value)
        page_items = epic.config_items()
        pr_items = config_ledger.collect_pr_items(
            epic.slug, owners, runner, lambda message: print(message, file=sys.stderr)
        )
    except (LookupError, ConfigLedgerError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    merged = config_ledger.sort_items(config_ledger.merge_items([page_items, pr_items]))

    if sync:
        if not merged and not config_ledger.has_none_marker(epic.record.body):
            print("No config items found; page left unchanged.", file=sys.stderr)
        elif merged:
            shutil.copyfile(epic.record.path, epic.record.path.with_name(f"{epic.record.path.name}.bak"))
            text = epic.record.path.read_text(encoding="utf-8")
            head = FRONTMATTER_PATTERN.match(text)
            split = head.end() if head else 0
            epic.record.path.write_text(text[:split] + config_ledger.replace_section(text[split:], merged), encoding="utf-8")
            print(f"Updated {epic.record.relpath} (backup: {epic.record.relpath}.bak)", file=sys.stderr)

    if output_json:
        print(json.dumps({"epic": epic.id, "items": [item.to_dict() for item in merged]}, indent=2))
    else:
        print("\n".join(config_ledger.render_table(merged)))
    return 0

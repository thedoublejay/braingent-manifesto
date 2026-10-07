"""Config-to-enable ledger: parse, validate, merge and render `config-to-enable/v1` blocks.

The same fenced YAML block appears in PR bodies, ticket descriptions and epic
pages. This module knows nothing about where a block came from.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from typing import Any

import yaml

BLOCK_MARKER = "config-to-enable/v1"
SECTION_HEADING = "## Config to enable"
KINDS = ("env", "flag", "tf_var", "helm_value", "db_setting", "db_role", "operator_step", "verify_check")
STATUSES = ("pending", "pr-open", "applied", "verified", "not-needed", "dormant")
STATUS_ORDER = ("pending", "pr-open", "applied", "dormant", "verified", "not-needed")
OPEN_STATUSES = ("pending", "pr-open", "applied")
PROGRESS_RANK = {"pending": 0, "pr-open": 1, "applied": 2, "verified": 3}
TERMINAL_STATUSES = ("not-needed", "dormant")
TABLE_COLUMNS = ("key", "kind", "repo/path", "env", "target", "introduced_by", "enabled_by", "status", "verify")

BLOCK_PATTERN = re.compile(
    rf"^```(?:ya?ml)?[ \t]*\r?\n(?P<body>[ \t]*#[ \t]*{re.escape(BLOCK_MARKER)}[^\n]*\n.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
SECTION_PATTERN = re.compile(rf"^{re.escape(SECTION_HEADING)}[ \t]*\r?\n(?P<body>.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


class ConfigLedgerError(ValueError):
    """Raised when a config-to-enable block is malformed."""


@dataclass(frozen=True)
class ConfigItem:
    key: str
    kind: str
    status: str
    service: str | None = None
    repo: str | None = None
    path: str | None = None
    env: str | None = None
    default: str | None = None
    target: str | None = None
    introduced_by: str | None = None
    enabled_by: str | None = None
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    verify: str | None = None

    @property
    def identity(self) -> tuple[str, str]:
        return (self.key, self.env or "")

    @property
    def is_open(self) -> bool:
        return self.status in OPEN_STATUSES

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"key": self.key, "kind": self.kind}
        for name in ("service", "repo", "path", "env", "default", "target", "introduced_by", "enabled_by"):
            value = getattr(self, name)
            if value is not None:
                data[name] = value
        if self.depends_on:
            data["depends_on"] = list(self.depends_on)
        data["status"] = self.status
        if self.verify is not None:
            data["verify"] = self.verify
        return data


def _scalar(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text or None


def _parse_item(raw: Any, label: str) -> ConfigItem:
    if not isinstance(raw, dict):
        raise ConfigLedgerError(f"{label}: item must be a mapping")
    for name in ("key", "kind", "status"):
        if _scalar(raw.get(name)) is None:
            raise ConfigLedgerError(f"{label}: missing required field `{name}`")
    kind = str(_scalar(raw["kind"]))
    status = str(_scalar(raw["status"]))
    if kind not in KINDS:
        raise ConfigLedgerError(f"{label}: unknown kind `{kind}`; allowed: {', '.join(KINDS)}")
    if status not in STATUSES:
        raise ConfigLedgerError(f"{label}: unknown status `{status}`; allowed: {', '.join(STATUSES)}")
    depends_raw = raw.get("depends_on")
    if depends_raw is None:
        depends_on: tuple[str, ...] = ()
    elif isinstance(depends_raw, list):
        depends_on = tuple(text for text in (_scalar(item) for item in depends_raw) if text)
    else:
        raise ConfigLedgerError(f"{label}: `depends_on` must be a list")
    return ConfigItem(
        key=str(_scalar(raw["key"])),
        kind=kind,
        status=status,
        service=_scalar(raw.get("service")),
        repo=_scalar(raw.get("repo")),
        path=_scalar(raw.get("path")),
        env=_scalar(raw.get("env")),
        default=_scalar(raw.get("default")),
        target=_scalar(raw.get("target")),
        introduced_by=_scalar(raw.get("introduced_by")),
        enabled_by=_scalar(raw.get("enabled_by")),
        depends_on=depends_on,
        verify=_scalar(raw.get("verify")),
    )


def parse_blocks(text: str) -> list[ConfigItem]:
    """Return every item from every `config-to-enable/v1` block in `text`."""

    items: list[ConfigItem] = []
    for index, match in enumerate(BLOCK_PATTERN.finditer(text), start=1):
        label = f"config block {index}"
        try:
            loaded = yaml.safe_load(match.group("body"))
        except yaml.YAMLError as exc:
            raise ConfigLedgerError(f"{label}: invalid YAML ({exc})") from exc
        if loaded is None:
            continue
        if not isinstance(loaded, list):
            raise ConfigLedgerError(f"{label}: block must be a YAML list of items")
        for position, raw in enumerate(loaded, start=1):
            items.append(_parse_item(raw, f"{label} item {position}"))
    return items


def config_section(body: str) -> str | None:
    match = SECTION_PATTERN.search(body)
    return match.group("body") if match else None


def has_none_marker(body: str) -> bool:
    section = config_section(body)
    if section is None:
        return False
    lines = [line.strip() for line in section.splitlines() if line.strip() and not line.strip().startswith("<!--")]
    return lines == ["None"]


def merge_pair(existing: ConfigItem, incoming: ConfigItem) -> ConfigItem:
    """Merge two items for the same (key, env); `incoming` is the later source."""

    existing_terminal = existing.status in TERMINAL_STATUSES
    incoming_terminal = incoming.status in TERMINAL_STATUSES
    if existing_terminal and incoming_terminal:
        winner, other = incoming, existing
    elif incoming_terminal:
        winner, other = (incoming, existing) if existing.status == "pending" else (existing, incoming)
    elif existing_terminal:
        winner, other = (existing, incoming) if incoming.status == "pending" else (incoming, existing)
    elif PROGRESS_RANK[incoming.status] > PROGRESS_RANK[existing.status]:
        winner, other = incoming, existing
    else:
        winner, other = existing, incoming
    filled = {
        name: getattr(other, name)
        for name in ("service", "repo", "path", "env", "default", "target", "introduced_by", "enabled_by", "verify")
        if getattr(winner, name) is None and getattr(other, name) is not None
    }
    depends_on = tuple(dict.fromkeys(winner.depends_on + other.depends_on))
    return replace(winner, depends_on=depends_on, **filled)


def merge_items(sources: Iterable[Iterable[ConfigItem]]) -> list[ConfigItem]:
    """Fold sources in order into one item per (key, env), keeping first-seen order."""

    merged: dict[tuple[str, str], ConfigItem] = {}
    for source in sources:
        for item in source:
            current = merged.get(item.identity)
            merged[item.identity] = item if current is None else merge_pair(current, item)
    return list(merged.values())


def sort_items(items: Iterable[ConfigItem]) -> list[ConfigItem]:
    return sorted(items, key=lambda item: (STATUS_ORDER.index(item.status), item.key, item.env or ""))


def render_blocks(items: Iterable[ConfigItem]) -> str:
    """Render items as a fenced `config-to-enable/v1` block, or `None` when empty."""

    listed = [item.to_dict() for item in items]
    if not listed:
        return "None"
    dumped = yaml.safe_dump(listed, sort_keys=False, default_flow_style=False, allow_unicode=True, width=120)
    return f"```yaml\n# {BLOCK_MARKER}\n{dumped}```"


def replace_section(body: str, items: Iterable[ConfigItem]) -> str:
    """Replace the `## Config to enable` section content, leaving every other section untouched."""

    match = SECTION_PATTERN.search(body)
    content = f"{SECTION_HEADING}\n\n{render_blocks(items)}\n\n"
    if match is None:
        separator = "" if body.endswith("\n\n") else ("\n" if body.endswith("\n") else "\n\n")
        return f"{body}{separator}{content}"
    return f"{body[: match.start()]}{content}{body[match.end():]}"


def _cell(value: str | None) -> str:
    return (value or "-").replace("|", "\\|").replace("\n", " ")


def table_row(item: ConfigItem) -> list[str]:
    location = " ".join(part for part in (item.repo, item.path) if part) or None
    return [
        f"`{item.key}`",
        item.kind,
        _cell(location),
        _cell(item.env),
        _cell(item.target),
        _cell(item.introduced_by),
        _cell(item.enabled_by),
        item.status,
        _cell(item.verify),
    ]


def render_table(items: Iterable[ConfigItem]) -> list[str]:
    lines = [f"| {' | '.join(TABLE_COLUMNS)} |", f"| {' | '.join('---' for _ in TABLE_COLUMNS)} |"]
    lines.extend(f"| {' | '.join(table_row(item))} |" for item in sort_items(items))
    return lines


GhRunner = Callable[[list[str]], str]


def collect_pr_items(
    epic_slug: str,
    owners: list[str],
    runner: GhRunner,
    warn: Callable[[str], None],
) -> list[ConfigItem]:
    """Collect config items from PR bodies labelled `epic:<slug>` via `gh search prs`."""

    fields = "number,repository,url,body,state"
    scopes: list[list[str]] = [["--owner", owner] for owner in owners] or [[]]
    items: list[ConfigItem] = []
    for scope in scopes:
        command = ["search", "prs", "--label", f"epic:{epic_slug}", *scope, "--json", fields, "--limit", "100"]
        try:
            payload = json.loads(runner(command) or "[]")
        except json.JSONDecodeError as exc:
            raise ConfigLedgerError(f"gh returned invalid JSON ({exc})") from exc
        if not isinstance(payload, list):
            raise ConfigLedgerError("gh returned an unexpected payload; expected a JSON list")
        for pr in sorted(payload, key=lambda entry: (str(_repository_name(entry)), int(entry.get("number", 0)))):
            reference = f"{_repository_name(pr)}#{pr.get('number')}"
            try:
                items.extend(parse_blocks(str(pr.get("body") or "")))
            except ConfigLedgerError as exc:
                warn(f"{reference}: skipped, {exc}")
    return items


def _repository_name(pr: dict[str, Any]) -> str:
    repository = pr.get("repository")
    if isinstance(repository, dict):
        return str(repository.get("name") or repository.get("nameWithOwner") or "unknown")
    return str(repository or "unknown")

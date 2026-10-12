"""Weekly plan: one human-written Markdown file per ISO week.

``weekly/YYYY-Www.md`` holds what matters this week, in the human's words:
``## Priorities`` (ordered, most important first), ``## Notes`` (reminders and
context that would otherwise be forgotten) and ``## Not this week`` (work agents
must not start without asking). Agents read it to decide what to pick up next.

The ``## Progress`` block is generated from the week's daily logs and rebuilt on
every read or write. A new week's file carries over last week's unticked
priorities and notes, so nothing silently drops off between weeks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta, tzinfo
from pathlib import Path
from typing import Any

from braingent import daily

WEEKLY_DIR = "weekly"
PROGRESS_START = "<!-- braingent:weekly-progress:start -->"
PROGRESS_END = "<!-- braingent:weekly-progress:end -->"
PROGRESS_PATTERN = re.compile(
    rf"^{re.escape(PROGRESS_START)}\r?\n.*?^{re.escape(PROGRESS_END)}[ \t]*(?:\r?\n|\Z)",
    re.MULTILINE | re.DOTALL,
)
SECTIONS = {
    "priorities": "Priorities",
    "notes": "Notes",
    "not-this-week": "Not this week",
}
CARRIED_SECTIONS = ("priorities", "notes")
SECTION_HINTS = {
    "priorities": "Human-owned. Ordered, most important first. Tick with [x] when done. Agents read this to decide what to work on next.",
    "notes": "Human-owned. Reminders, context and anything that would otherwise be forgotten. Agents add here only when asked.",
    "not-this-week": "Human-owned. Work agents must not start this week without asking.",
}
ITEM_PATTERN = re.compile(r"^(?:[-*]|\d+\.)[ \t]+(?:\[([ xX])\][ \t]+)?(.+?)[ \t]*$")
CARRIED_SUFFIX = re.compile(r" \(from \d{4}-W\d{2}\)$")
WEEK_FILE_PATTERN = re.compile(r"^\d{4}-W\d{2}\.md$")


@dataclass(frozen=True)
class Item:
    text: str
    done: bool | None

    def line(self) -> str:
        box = "" if self.done is None else ("[x] " if self.done else "[ ] ")
        return f"- {box}{self.text}"


def week_key(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def week_days(day: date) -> list[date]:
    monday = day - timedelta(days=day.weekday())
    return [monday + timedelta(days=offset) for offset in range(7)]


def week_path(root: Path, day: date) -> Path:
    return root / WEEKLY_DIR / f"{week_key(day)}.md"


def human_range(day: date) -> str:
    days = week_days(day)
    start, end = days[0], days[-1]
    if start.year != end.year:
        return f"{daily.human_date(start)} to {daily.human_date(end)}"
    if start.month != end.month:
        return f"{start.day} {start:%B} to {daily.human_date(end)}"
    return f"{start.day} to {daily.human_date(end)}"


def section_pattern(title: str) -> re.Pattern[str]:
    return re.compile(rf"^## {re.escape(title)}[ \t]*\r?\n(.*?)(?=^## |^<!-- braingent:|\Z)", re.MULTILINE | re.DOTALL)


def parse_items(text: str, section: str) -> list[Item]:
    match = section_pattern(SECTIONS[section]).search(text)
    if match is None:
        return []
    items: list[Item] = []
    for line in match.group(1).splitlines():
        if item := ITEM_PATTERN.match(line):
            box, body = item.groups()
            items.append(Item(body, None if box is None else box != " "))
    return items


def previous_week_file(root: Path, day: date) -> Path | None:
    directory = root / WEEKLY_DIR
    if not directory.is_dir():
        return None
    key = week_key(day)
    earlier = sorted(path for path in directory.iterdir() if WEEK_FILE_PATTERN.match(path.name) and path.stem < key)
    return earlier[-1] if earlier else None


def carried_items(root: Path, day: date) -> dict[str, list[Item]]:
    source = previous_week_file(root, day)
    if source is None:
        return {}
    with daily.locked(source) as handle:
        text = handle.read()
    carried: dict[str, list[Item]] = {}
    for section in CARRIED_SECTIONS:
        open_items = [item for item in parse_items(text, section) if item.done is False]
        carried[section] = [
            Item(item.text if CARRIED_SUFFIX.search(item.text) else f"{item.text} (from {source.stem})", False)
            for item in open_items
        ]
    return carried


def new_week(root: Path, day: date, tz: tzinfo) -> str:
    carried = carried_items(root, day)
    parts = [f"# Weekly plan: {week_key(day)} ({human_range(day)})", "", f"Timezone: {tz}"]
    for section, title in SECTIONS.items():
        parts += ["", f"## {title}", "", f"<!-- {SECTION_HINTS[section]} -->"]
        if items := carried.get(section):
            parts += [""] + [item.line() for item in items]
    return "\n".join(parts) + "\n"


def progress(root: Path, day: date) -> dict[str, Any]:
    per_day: list[dict[str, Any]] = []
    done: dict[str, tuple[date, daily.Event]] = {}
    spawned = 0
    latest: daily.Status | None = None
    for current in week_days(day):
        path = daily.day_path(root, current)
        if not path.is_file():
            continue
        with daily.locked(path) as handle:
            status = daily.derive_status(daily.parse_events(handle.read()))
        for event in status.buckets["done"]:
            done[event.key] = (current, event)
        spawned += len(status.spawned)
        latest = status
        per_day.append({"date": current.isoformat(), "done": len(status.buckets["done"]), "spawned": len(status.spawned)})
    open_counts = {name: len(latest.buckets[name]) if latest else 0 for name in daily.UNFINISHED}
    return {
        "days": per_day,
        "done": [{"date": when.isoformat(), "ref": event.ref, "text": event.text, "kind": event.kind, "epic": event.epic} for when, event in done.values()],
        "spawned": spawned,
        "open": open_counts,
    }


def render_progress(summary: dict[str, Any]) -> str:
    open_counts = summary["open"]
    lines = [
        PROGRESS_START,
        "## Progress",
        "",
        "<!-- Generated from this week's daily logs by braingent. Edits here are overwritten. -->",
        "",
        f"Done: {len(summary['done'])} · Spawned: {summary['spawned']} · Open now: "
        f"{open_counts['ongoing']} ongoing, {open_counts['review']} in review, "
        f"{open_counts['blocked']} blocked, {open_counts['todo']} todo",
        "",
        "### By day",
        "",
    ]
    lines += [
        f"- {date.fromisoformat(entry['date']):%a} {daily.human_date(date.fromisoformat(entry['date']))}: "
        f"{entry['done']} done, {entry['spawned']} spawned"
        for entry in summary["days"]
    ] or ["- No daily logs yet"]
    lines += ["", f"### Done this week ({len(summary['done'])})", ""]
    lines += [
        f"- {'[' + entry['ref'] + '] ' if entry['ref'] else ''}{entry['text']}"
        f"{' (dropped)' if entry['kind'] == 'dropped' else ''}{' · epic:' + entry['epic'] if entry['epic'] else ''}"
        for entry in summary["done"]
    ] or ["- None"]
    lines.append(PROGRESS_END)
    return "\n".join(lines) + "\n"


def with_progress(text: str, block: str) -> str:
    existing = PROGRESS_PATTERN.search(text)
    if existing is not None:
        return f"{text[:existing.start()]}{block}{text[existing.end():]}"
    return f"{text.rstrip()}\n\n{block}"


def add_to_section(text: str, section: str, item: Item) -> str:
    title = SECTIONS[section]
    match = section_pattern(title).search(text)
    if match is None:
        insert_at = PROGRESS_PATTERN.search(text)
        head, tail = (text[:insert_at.start()], text[insert_at.start():]) if insert_at else (text, "")
        return f"{head.rstrip()}\n\n## {title}\n\n{item.line()}\n\n{tail}"
    body = match.group(1).rstrip()
    gap = "\n" if body and not ITEM_PATTERN.match(body.splitlines()[-1]) else ""
    lead = f"{body}\n{gap}" if body else "\n"
    return f"{text[:match.start(1)]}{lead}{item.line()}\n\n{text[match.end(1):].lstrip(chr(10))}"


def update_week(root: Path, day: date, tz: tzinfo, section: str | None = None, entry: str | None = None) -> Path:
    path = week_path(root, day)
    with daily.locked(path) as handle:
        text = handle.read() or new_week(root, day, tz)
        if section is not None and entry is not None:
            text = add_to_section(text, section, Item(entry, None if section == "not-this-week" else False))
        daily.rewrite(handle, with_progress(text, render_progress(progress(root, day))))
    return path


def add_item(root: Path, section: str, text: str, *, day: date, tz: tzinfo) -> Path:
    if section not in SECTIONS:
        raise ValueError(f"unknown section {section!r}; use one of: {', '.join(SECTIONS)}")
    body = daily.clean(text)
    if not body:
        raise ValueError("item text must not be empty")
    return update_week(root, day, tz, section, body)


def summarise(root: Path, day: date, tz: tzinfo | None = None) -> dict[str, Any]:
    path = update_week(root, day, tz or daily.resolve_tz(None))
    with daily.locked(path) as handle:
        text = handle.read()

    def as_dicts(section: str) -> list[dict[str, Any]]:
        return [{"text": item.text, "done": item.done} for item in parse_items(text, section)]

    return {
        "week": week_key(day),
        "range": human_range(day),
        "path": path.relative_to(root).as_posix(),
        "priorities": as_dicts("priorities"),
        "notes": as_dicts("notes"),
        "not_this_week": as_dicts("not-this-week"),
        "progress": progress(root, day),
    }

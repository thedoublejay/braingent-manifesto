"""Daily log: one Markdown file per day of what every agent did.

Agents only ever append one-line events to the ``## Log`` section of
``daily/YYYY-MM-DD.md``. The ``## Status`` block (ongoing, in review, blocked,
todo, done, spawned) is derived from those events and regenerated on every
write, so several CLIs can log concurrently without editing the same lines.
``## Goals`` belongs to the human and is never touched.

A new day's file carries over yesterday's unfinished items as ``carry-over``
events, so nothing silently drops off between days.
"""

from __future__ import annotations

import contextlib
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, tzinfo
from pathlib import Path
from typing import IO, Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl.
    fcntl = None  # type: ignore[assignment]

DAILY_DIR = "daily"
DEFAULT_SPRAWL_THRESHOLD = 10
CARRY_ACTOR = "carry-over"
STATUS_START = "<!-- braingent:daily-status:start -->"
STATUS_END = "<!-- braingent:daily-status:end -->"
LOG_HEADING = "## Log"

KINDS = ("todo", "started", "review", "blocked", "done", "dropped", "spawned", "note")
BUCKET_OF = {
    "todo": "todo",
    "spawned": "todo",
    "started": "ongoing",
    "review": "review",
    "blocked": "blocked",
    "done": "done",
    "dropped": "done",
}
BUCKETS = (
    ("ongoing", "Ongoing"),
    ("review", "In review"),
    ("blocked", "Blocked"),
    ("todo", "Todo"),
    ("done", "Done"),
)
UNFINISHED = ("ongoing", "review", "blocked", "todo")
EVENT_PATTERN = re.compile(r"^- (\d{2}:\d{2}) · (\S+) · (\S+) · (\S+) · (.*)$")
DAY_FILE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


@dataclass(frozen=True)
class Event:
    time: str
    actor: str
    kind: str
    ref: str | None
    text: str

    @property
    def key(self) -> str:
        return self.ref or self.text.strip().lower()

    def line(self) -> str:
        return f"- {self.time} · {self.actor} · {self.kind} · {self.ref or '-'} · {self.text}"


@dataclass
class Status:
    buckets: dict[str, list[Event]] = field(default_factory=lambda: {name: [] for name, _ in BUCKETS})
    spawned: list[Event] = field(default_factory=list)
    spawned_untouched: int = 0
    carried: int = 0


def resolve_tz(name: str | None) -> tzinfo:
    if not name:
        return local_tz()
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown timezone {name!r}; use an IANA name such as 'Asia/Singapore'") from exc


def local_tz() -> tzinfo:
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        _, marker, key = localtime.resolve().as_posix().partition("zoneinfo/")
        if marker:
            with contextlib.suppress(ZoneInfoNotFoundError, ValueError):
                return ZoneInfo(key)
    local = datetime.now().astimezone().tzinfo
    assert local is not None
    return local


def day_path(root: Path, day: date) -> Path:
    return root / DAILY_DIR / f"{day.isoformat()}.md"


def human_date(day: date) -> str:
    return f"{day.day} {day:%B %Y}"


def clean(value: str) -> str:
    return " ".join(value.split())


def parse_events(text: str) -> list[Event]:
    events: list[Event] = []
    for line in text.splitlines():
        match = EVENT_PATTERN.match(line)
        if match and match.group(3) in KINDS:
            time, actor, kind, ref, body = match.groups()
            events.append(Event(time, actor, kind, None if ref == "-" else ref, body))
    return events


def derive_status(events: list[Event]) -> Status:
    latest: dict[str, tuple[int, Event]] = {}
    for index, event in enumerate(events):
        if event.kind != "note":
            latest[event.key] = (index, event)
    status = Status()
    for _, event in sorted(latest.values(), key=lambda pair: pair[0]):
        status.buckets[BUCKET_OF[event.kind]].append(event)
    status.spawned = [event for event in events if event.kind == "spawned"]
    status.spawned_untouched = sum(1 for _, event in latest.values() if event.kind == "spawned")
    status.carried = sum(1 for event in events if event.actor == CARRY_ACTOR)
    return status


def render_item(event: Event) -> str:
    ref = f"[{event.ref}] " if event.ref else ""
    suffix = " (dropped)" if event.kind == "dropped" else ""
    return f"- {ref}{event.text}{suffix} · {event.actor} · {event.time}"


def render_status(status: Status, sprawl_threshold: int) -> str:
    lines = [
        STATUS_START,
        "## Status",
        "",
        "<!-- Generated from the log by braingent. Edits here are overwritten. -->",
        "",
        f"Spawned today: {len(status.spawned)} ({status.spawned_untouched} untouched) · Carried over: {status.carried}",
    ]
    if len(status.spawned) >= sprawl_threshold:
        lines += [
            "",
            f"> Sprawl: {len(status.spawned)} tickets or PRs spawned today (threshold {sprawl_threshold}). "
            "Triage these before starting new work.",
        ]
    sections = [(title, status.buckets[name]) for name, title in BUCKETS] + [("Spawned today", status.spawned)]
    for title, events in sections:
        lines += ["", f"### {title} ({len(events)})", ""]
        lines += [render_item(event) for event in events] or ["- None"]
    lines.append(STATUS_END)
    return "\n".join(lines)


def with_status(text: str, sprawl_threshold: int) -> str:
    block = render_status(derive_status(parse_events(text)), sprawl_threshold)
    if STATUS_START in text and STATUS_END in text:
        head, rest = text.split(STATUS_START, 1)
        tail = rest.split(STATUS_END, 1)[1]
        return f"{head}{block}{tail}"
    head, sep, tail = text.partition(LOG_HEADING)
    return f"{head.rstrip()}\n\n{block}\n\n{sep}{tail}"


def previous_day_file(root: Path, day: date) -> Path | None:
    directory = root / DAILY_DIR
    if not directory.is_dir():
        return None
    earlier = sorted(
        path for path in directory.iterdir() if DAY_FILE_PATTERN.match(path.name) and path.stem < day.isoformat()
    )
    return earlier[-1] if earlier else None


def carried_events(root: Path, day: date) -> list[Event]:
    source = previous_day_file(root, day)
    if source is None:
        return []
    status = derive_status(parse_events(source.read_text(encoding="utf-8")))
    return [
        Event("00:00", CARRY_ACTOR, "todo" if event.kind == "spawned" else event.kind, event.ref, event.text)
        for name in UNFINISHED
        for event in status.buckets[name]
    ]


def new_day(root: Path, day: date, tz: tzinfo) -> str:
    carried = "\n".join(event.line() for event in carried_events(root, day))
    return (
        "---\n"
        "record_kind: daily-log\n"
        f"date: {day.isoformat()}\n"
        f"timezone: {tz}\n"
        "---\n\n"
        f"# Daily log: {human_date(day)}\n\n"
        "## Goals\n\n"
        "<!-- Human-owned. Up to three outcomes for today. Agents never edit this section. -->\n\n"
        f"{LOG_HEADING}\n\n"
        "<!-- Append-only. One event per line: - HH:MM · agent · kind · ref · text -->\n"
        + (f"\n{carried}\n" if carried else "")
    )


@contextlib.contextmanager
def locked(path: Path) -> Iterator[IO[str]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with path.open("r+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield handle
        finally:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_UN)


def rewrite(handle: IO[str], text: str) -> None:
    handle.seek(0)
    handle.write(text)
    handle.truncate()


def update_day(root: Path, day: date, tz: tzinfo, sprawl_threshold: int, event: Event | None = None) -> Path:
    path = day_path(root, day)
    with locked(path) as handle:
        text = handle.read() or new_day(root, day, tz)
        if event is not None:
            text = text.rstrip("\n") + "\n" + event.line() + "\n"
        rewrite(handle, with_status(text, sprawl_threshold))
    return path


def log_event(
    root: Path,
    kind: str,
    text: str,
    *,
    actor: str,
    ref: str | None = None,
    now: datetime | None = None,
    tz: tzinfo | None = None,
    sprawl_threshold: int = DEFAULT_SPRAWL_THRESHOLD,
) -> Path:
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; use one of: {', '.join(KINDS)}")
    body = clean(text)
    if not body:
        raise ValueError("event text must not be empty")
    zone = tz or resolve_tz(None)
    moment = (now or datetime.now(zone)).astimezone(zone)
    ref_value = "-".join(ref.split()) if ref and ref.strip() else None
    event = Event(moment.strftime("%H:%M"), "-".join(actor.split()), kind, ref_value, body)
    return update_day(root, moment.date(), zone, sprawl_threshold, event)


def refresh(root: Path, day: date, sprawl_threshold: int = DEFAULT_SPRAWL_THRESHOLD, tz: tzinfo | None = None) -> Path:
    return update_day(root, day, tz or resolve_tz(None), sprawl_threshold)


def summarise(
    root: Path, day: date, sprawl_threshold: int = DEFAULT_SPRAWL_THRESHOLD, tz: tzinfo | None = None
) -> dict[str, Any]:
    path = refresh(root, day, sprawl_threshold, tz)
    status = derive_status(parse_events(path.read_text(encoding="utf-8")))

    def as_dict(event: Event) -> dict[str, Any]:
        return {"time": event.time, "actor": event.actor, "kind": event.kind, "ref": event.ref, "text": event.text}

    return {
        "date": day.isoformat(),
        "path": path.relative_to(root).as_posix(),
        "counts": {name: len(status.buckets[name]) for name, _ in BUCKETS},
        "items": {name: [as_dict(event) for event in status.buckets[name]] for name, _ in BUCKETS},
        "spawned": len(status.spawned),
        "spawned_untouched": status.spawned_untouched,
        "carried": status.carried,
        "sprawl_threshold": sprawl_threshold,
        "sprawl": len(status.spawned) >= sprawl_threshold,
    }

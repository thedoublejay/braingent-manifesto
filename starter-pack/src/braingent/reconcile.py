"""Check open daily-log items against their pull requests, without closing anything.

A merged pull request moves its item to `merged`, which stays open until someone logs `verified`
or `done`. A lookup that fails leaves the item untouched and is reported as unknown.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from datetime import date, datetime, tzinfo
from pathlib import Path
from typing import Any

from braingent import daily

PR_REF = re.compile(r"^(?:([\w.-]+)/)?([\w.-]+)#(\d+)$")
OPEN_BUCKETS = ("ongoing", "review", "todo")
ACTOR = "reconcile"
DEFAULT_LIMIT = 50


def default_runner(arguments: list[str]) -> str:
    completed = subprocess.run(["gh", *arguments], capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"gh exited {completed.returncode}")
    return completed.stdout


def pr_state(ref: str, owners: list[str], runner: Callable[[list[str]], str]) -> tuple[str, str]:
    """Return (state, detail): merged, closed, open, or unknown when no lookup succeeded."""

    match = PR_REF.match(ref)
    if match is None:
        return "unknown", "not a pull request reference"
    owner, repo, number = match.groups()
    last_error = "no owner configured; set [config_ledger] owners or use owner/repo#n"
    matches: list[tuple[str, str]] = []
    for candidate in [owner] if owner else dict.fromkeys(owners):
        try:
            payload = json.loads(runner(["pr", "view", number, "--repo", f"{candidate}/{repo}", "--json", "state,url"]))
            if not isinstance(payload, dict) or payload.get("state") not in {"OPEN", "CLOSED", "MERGED"}:
                raise ValueError("invalid pull request state response")
            matches.append((str(payload["state"]).lower(), str(payload.get("url") or "")))
        except (RuntimeError, ValueError, KeyError, OSError) as exc:
            last_error = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
    if len(matches) > 1:
        return "unknown", "ambiguous owner; use owner/repo#n"
    if matches:
        return matches[0]
    return "unknown", last_error


def run(
    root: Path,
    day: date,
    tz: tzinfo,
    owners: list[str],
    *,
    apply: bool = False,
    limit: int = DEFAULT_LIMIT,
    output_json: bool = False,
    sprawl_threshold: int = daily.DEFAULT_SPRAWL_THRESHOLD,
    stale_after_days: int = 0,
    runner: Callable[[list[str]], str] | None = None,
    now: datetime | None = None,
) -> int:
    if limit < 1:
        raise ValueError("limit must be greater than zero")
    runner = runner or default_runner
    path = daily.day_path(root, day)
    if apply:
        daily.refresh(root, day, sprawl_threshold, tz, stale_after_days)
    events = daily.parse_events(path.read_text(encoding="utf-8")) if path.is_file() else daily.carried_events(
        root, day, stale_after_days, persist_stale=False
    )
    status = daily.derive_status(events)
    snapshot = {event.key: event for event in events}
    candidates = [event for name in OPEN_BUCKETS for event in status.buckets[name] if event.ref and PR_REF.match(event.ref)]
    results: list[dict[str, Any]] = []
    for event in candidates[:limit]:
        state, detail = pr_state(event.ref or "", owners, runner)
        logged = False
        if state == "merged" and apply:
            moment = (now or datetime.now(tz)).astimezone(tz)
            replacement = daily.Event(moment.strftime("%H:%M"), ACTOR, "merged", event.ref, event.text, event.epic)
            logged = daily.log_if_current(
                root, day, snapshot[event.key], replacement, tz, sprawl_threshold=sprawl_threshold, stale_after_days=stale_after_days,
            )
        results.append({"ref": event.ref, "was": event.kind, "state": state, "detail": detail, "logged": logged})
    summary = {
        "checked": len(results),
        "skipped": max(len(candidates) - limit, 0),
        "merged": sum(1 for row in results if row["state"] == "merged"),
        "unknown": sum(1 for row in results if row["state"] == "unknown"),
        "applied": apply,
        "items": results,
    }
    if output_json:
        print(json.dumps(summary, indent=2))
        return 0
    print(
        f"checked {summary['checked']} pull request items ({summary['skipped']} not checked, over the limit): "
        f"{summary['merged']} merged, {summary['unknown']} unknown. "
        + ("Merged items were logged as `merged` and stay open." if apply else "Nothing was logged; rerun with --apply.")
    )
    for row in results:
        if row["state"] in {"merged", "closed", "unknown"}:
            print(f"- {row['ref']}: {row['state']}" + (f" ({row['detail']})" if row["state"] == "unknown" else ""))
    return 0

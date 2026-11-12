from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from braingent import daily, weekly

ZONE = ZoneInfo("UTC")


def at(day: date, hhmm: str = "09:00") -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=ZONE)


class DailyStateTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.day = date(2026, 10, 5)
        self.addCleanup(self._tmp.cleanup)

    def log(self, kind: str, text: str, ref: str | None, day: date | None = None, epic: str | None = None, stale: int = 0, hhmm: str = "09:00") -> Path:
        return daily.log_event(
            self.root, kind, text, actor="agent--one", ref=ref, epic=epic, now=at(day or self.day, hhmm), tz=ZONE, stale_after_days=stale
        )

    def carried_refs(self, day: date) -> set[str | None]:
        text = daily.day_path(self.root, day).read_text(encoding="utf-8")
        return {event.ref for event in daily.parse_events(text) if event.actor == daily.CARRY_ACTOR}


class MergedDeployedVerifiedTests(DailyStateTestCase):
    def test_merged_and_deployed_stay_open_and_verified_closes(self) -> None:
        self.log("started", "Feature", "EX-1")
        self.log("merged", "Feature", "EX-1", hhmm="10:00")
        summary = daily.summarise(self.root, self.day, tz=ZONE)
        self.assertEqual((summary["counts"]["landed"], summary["counts"]["done"], summary["closed"]), (1, 0, 0))
        text = daily.day_path(self.root, self.day).read_text(encoding="utf-8")
        self.assertIn("### Merged, not yet verified (1)", text)
        self.assertIn("- [EX-1] Feature (merged)", text)

        next_day = self.day + timedelta(days=1)
        self.log("deployed", "Feature", "EX-1", day=next_day)
        self.assertEqual(daily.summarise(self.root, next_day, tz=ZONE)["counts"]["landed"], 1)
        self.log("verified", "Feature", "EX-1", day=next_day, hhmm="11:00")
        summary = daily.summarise(self.root, next_day, tz=ZONE)
        self.assertEqual((summary["counts"]["landed"], summary["counts"]["done"], summary["closed"]), (0, 1, 1))

    def test_a_merged_item_is_carried_to_the_next_day(self) -> None:
        self.log("merged", "Feature", "EX-1")
        next_day = self.day + timedelta(days=1)
        self.log("note", "morning", None, day=next_day)
        self.assertEqual(self.carried_refs(next_day), {"EX-1"})

    def test_status_line_reports_closed_and_net(self) -> None:
        self.log("spawned", "A", "EX-1")
        self.log("spawned", "B", "EX-2")
        self.log("spawned", "C", "EX-3")
        self.log("done", "A", "EX-1", hhmm="10:00")
        text = daily.day_path(self.root, self.day).read_text(encoding="utf-8")
        self.assertIn("Spawned today: 3 (2 untouched) · Closed today: 1 · Net: +2 · Carried over: 0", text)


class StaleQueueTests(DailyStateTestCase):
    def advance(self, days: int, stale: int) -> date:
        current = self.day
        for _ in range(days):
            current += timedelta(days=1)
            self.log("note", "tick", None, day=current, stale=stale)
        return current

    def test_off_by_default_everything_is_carried(self) -> None:
        self.log("started", "Old work", "EX-1")
        last = self.advance(20, stale=0)
        self.assertEqual(self.carried_refs(last), {"EX-1"})
        self.assertFalse(daily.stale_path(self.root).exists())

    def test_untouched_items_move_to_the_stale_file_and_are_not_closed(self) -> None:
        self.log("started", "Old work", "EX-1")
        self.log("blocked", "Waiting on access", "EX-2")
        within = self.advance(3, stale=3)
        self.assertEqual(self.carried_refs(within), {"EX-1", "EX-2"})
        after = self.advance(4, stale=3)
        self.assertEqual(self.carried_refs(after), {"EX-2"})
        stale = daily.read_stale(self.root)
        self.assertEqual([(event.ref, event.kind) for _, event in stale], [("EX-1", "started")])
        summary = daily.summarise(self.root, after, tz=ZONE, stale_after_days=3)
        self.assertEqual((summary["stale"], summary["counts"]["done"]), (1, 0))
        self.assertIn("Stale: 1 (see daily/stale.md)", daily.day_path(self.root, after).read_text(encoding="utf-8"))

    def test_touching_a_stale_item_brings_it_back(self) -> None:
        self.log("started", "Old work", "EX-1")
        day = self.advance(7, stale=3)
        self.assertEqual(len(daily.read_stale(self.root)), 1)
        self.log("review", "Old work", "EX-1", day=day, stale=3, hhmm="10:00")
        self.assertEqual(daily.summarise(self.root, day, tz=ZONE, stale_after_days=3)["counts"]["review"], 1)
        next_day = day + timedelta(days=1)
        self.log("note", "tick", None, day=next_day, stale=3)
        self.assertEqual(self.carried_refs(next_day), {"EX-1"})
        self.assertEqual(daily.read_stale(self.root), [])

    def test_items_under_a_weekly_priority_never_go_stale(self) -> None:
        self.log("started", "Priority work", "EX-1", epic="live-fire")
        self.log("started", "Other work", "EX-2", epic="side-quest")
        current = self.day
        for _ in range(7):
            current += timedelta(days=1)
            weekly.add_item(self.root, "priorities", "Ship the pilot", day=current, tz=ZONE, epic="live-fire") if not weekly.priority_epics(self.root, current) else None
            self.log("note", "tick", None, day=current, stale=3)
        self.assertEqual(self.carried_refs(current), {"EX-1"})
        self.assertEqual([event.ref for _, event in daily.read_stale(self.root)], ["EX-2"])


class WeeklyPriorityEpicTests(DailyStateTestCase):
    def test_priority_progress_counts_its_epics(self) -> None:
        monday = date(2026, 10, 12)
        weekly.add_item(self.root, "priorities", "Ship the pilot", day=monday, tz=ZONE, epic="live-fire")
        weekly.add_item(self.root, "priorities", "Untagged goal", day=monday, tz=ZONE)
        self.log("spawned", "A", "EX-1", day=monday, epic="live-fire")
        self.log("spawned", "B", "EX-2", day=monday, epic="live-fire")
        self.log("spawned", "C", "EX-3", day=monday, epic="side-quest")
        self.log("spawned", "D", "EX-4", day=monday)
        self.log("done", "A", "EX-1", day=monday, epic="live-fire", hhmm="10:00")
        summary = weekly.summarise(self.root, monday, ZONE)
        first, second = summary["priorities"]
        self.assertEqual(first["text"], "Ship the pilot epic:live-fire")
        self.assertEqual((first["epics"], first["progress"]), (["live-fire"], {"done": 1, "open": 1, "spawned": 2}))
        self.assertEqual(second, {"text": "Untagged goal", "done": False})
        text = weekly.week_path(self.root, monday).read_text(encoding="utf-8")
        self.assertIn("### By priority", text)
        self.assertIn("- 1. epic:live-fire: 1 done, 1 open, 2 spawned", text)
        self.assertIn("- Spawned outside these priorities: 2 of 4", text)
        self.assertIn("Spawned outside weekly priorities: 2", daily.day_path(self.root, monday).read_text(encoding="utf-8"))

    def test_no_tagged_priority_leaves_the_views_unchanged(self) -> None:
        monday = date(2026, 10, 12)
        weekly.add_item(self.root, "priorities", "Untagged goal", day=monday, tz=ZONE)
        self.log("spawned", "A", "EX-1", day=monday, epic="live-fire")
        self.assertNotIn("### By priority", weekly.week_path(self.root, monday).read_text(encoding="utf-8"))
        self.assertNotIn("outside weekly priorities", daily.day_path(self.root, monday).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

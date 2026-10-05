from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from braingent import config as bgconfig
from braingent import daily

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SGT = ZoneInfo("Asia/Singapore")


def at(day: date, hhmm: str) -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=SGT)


class DailyConfigTests(unittest.TestCase):
    def test_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = bgconfig.load_config(Path(tmp) / "repo", home=Path(tmp) / "home")
            self.assertIsNone(cfg.daily_timezone)
            self.assertEqual(cfg.daily_sprawl_threshold, 10)

    def test_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            (root / ".braingent").mkdir(parents=True)
            (root / ".braingent" / "config.toml").write_text(
                '[daily]\ntimezone = "Asia/Singapore"\nsprawl_threshold = 4\n', encoding="utf-8"
            )
            cfg = bgconfig.load_config(root, home=Path(tmp) / "home")
            self.assertEqual(cfg.daily_timezone, "Asia/Singapore")
            self.assertEqual(cfg.daily_sprawl_threshold, 4)


class DailyLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.day = date(2026, 10, 6)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def log(self, kind: str, text: str, ref: str | None = None, actor: str = "agent--claude-code", hhmm: str = "09:00", day: date | None = None) -> Path:
        return daily.log_event(self.root, kind, text, actor=actor, ref=ref, now=at(day or self.day, hhmm), tz=SGT)

    def test_first_event_creates_day_file_with_goals_and_log(self) -> None:
        path = self.log("started", "Verdict lock fix", ref="GET-1234", hhmm="09:42")
        self.assertEqual(path, self.root / "daily" / "2026-10-06.md")
        text = path.read_text(encoding="utf-8")
        self.assertIn("# Daily log: 6 October 2026", text)
        self.assertIn("## Goals", text)
        self.assertIn("- 09:42 · agent--claude-code · started · GET-1234 · Verdict lock fix", text)

    def test_event_text_is_flattened_to_one_line(self) -> None:
        path = self.log("note", "line one\nline two", ref="has space")
        events = daily.parse_events(path.read_text(encoding="utf-8"))
        self.assertEqual(events[-1].text, "line one line two")
        self.assertEqual(events[-1].ref, "has-space")

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.log("finished", "nope")

    def test_latest_event_per_ref_decides_bucket(self) -> None:
        self.log("spawned", "Ticket for flaky test", ref="GET-1", hhmm="09:00")
        self.log("started", "Verdict lock", ref="GET-2", hhmm="09:10")
        self.log("review", "Verdict lock PR", ref="GET-2", actor="agent--codex-cli", hhmm="10:00")
        self.log("done", "Verdict lock merged", ref="GET-2", hhmm="11:00")
        self.log("blocked", "Waiting on infra", ref="GET-3", hhmm="11:30")
        self.log("note", "General note", hhmm="11:40")
        path = self.log("todo", "Write migration", hhmm="12:00")
        status = daily.derive_status(daily.parse_events(path.read_text(encoding="utf-8")))
        self.assertEqual([item.ref for item in status.buckets["done"]], ["GET-2"])
        self.assertEqual([item.ref for item in status.buckets["blocked"]], ["GET-3"])
        self.assertEqual([item.text for item in status.buckets["todo"]], ["Ticket for flaky test", "Write migration"])
        self.assertEqual(status.buckets["ongoing"], [])
        self.assertEqual(len(status.spawned), 1)

    def test_status_block_is_regenerated_and_goals_preserved(self) -> None:
        path = self.log("started", "First task", ref="GET-1")
        text = path.read_text(encoding="utf-8").replace("## Goals\n", "## Goals\n\n- Ship the verdict fix\n", 1)
        path.write_text(text, encoding="utf-8")
        self.log("done", "First task", ref="GET-1", hhmm="10:00")
        text = path.read_text(encoding="utf-8")
        self.assertIn("- Ship the verdict fix", text)
        self.assertEqual(text.count(daily.STATUS_START), 1)
        status_block = text.split(daily.STATUS_START, 1)[1].split(daily.STATUS_END, 1)[0]
        self.assertIn("### Done (1)", status_block)
        self.assertIn("### Ongoing (0)", status_block)

    def test_sprawl_flag_trips_at_threshold(self) -> None:
        for index in range(3):
            self.log("spawned", f"Ticket {index}", ref=f"GET-{index}", hhmm=f"09:0{index}")
        path = daily.refresh(self.root, self.day, sprawl_threshold=3)
        text = path.read_text(encoding="utf-8")
        self.assertIn("Sprawl: 3 tickets or PRs spawned today", text)
        summary = daily.summarise(self.root, self.day, sprawl_threshold=3)
        self.assertTrue(summary["sprawl"])
        self.assertEqual(summary["spawned"], 3)
        self.assertEqual(summary["spawned_untouched"], 3)

    def test_next_day_carries_over_unfinished_items_only(self) -> None:
        self.log("started", "Long running", ref="GET-1")
        self.log("done", "Finished", ref="GET-2")
        self.log("spawned", "New ticket", ref="GET-3")
        self.log("note", "Just a note")
        tomorrow = date(2026, 10, 7)
        path = self.log("started", "Fresh work", ref="GET-9", day=tomorrow)
        events = daily.parse_events(path.read_text(encoding="utf-8"))
        carried = [event for event in events if event.actor == daily.CARRY_ACTOR]
        self.assertEqual({(event.ref, event.kind) for event in carried}, {("GET-1", "started"), ("GET-3", "todo")})
        status = daily.derive_status(events)
        self.assertEqual(status.spawned, [])
        self.assertEqual(status.carried, 2)

    def test_carry_over_skips_gap_days(self) -> None:
        self.log("blocked", "Waiting", ref="GET-1")
        path = self.log("note", "Back after weekend", day=date(2026, 10, 9))
        events = daily.parse_events(path.read_text(encoding="utf-8"))
        self.assertIn(("GET-1", "blocked"), {(event.ref, event.kind) for event in events})


class DailyCliTests(unittest.TestCase):
    def run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)
        return subprocess.run(
            [sys.executable, "-m", "braingent", "--root", str(root), *args],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )

    def test_log_then_status_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for marker in ("preferences", "templates", "workflows"):
                (root / marker).mkdir()
            (root / "preferences" / "taxonomy.yml").write_text("record_scan_roots: []\n", encoding="utf-8")
            logged = self.run_cli(root, "daily-log", "started", "CLI task", "--ref", "GET-7", "--as", "agent--codex-cli", "--date", "2026-10-06")
            self.assertEqual(logged.stdout.strip(), "daily/2026-10-06.md")
            status = self.run_cli(root, "daily-status", "--date", "2026-10-06", "--json")
            payload = json.loads(status.stdout)
            self.assertEqual(payload["counts"]["ongoing"], 1)
            self.assertEqual(payload["path"], "daily/2026-10-06.md")
            self.assertFalse(payload["sprawl"])


if __name__ == "__main__":
    unittest.main()

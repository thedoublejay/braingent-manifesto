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

from braingent import daily, weekly

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SGT = ZoneInfo("Asia/Singapore")


def at(day: date, hhmm: str) -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=SGT)


class WeeklyPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.day = date(2026, 10, 14)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def add(self, section: str, text: str, day: date | None = None) -> Path:
        return weekly.add_item(self.root, section, text, day=day or self.day, tz=SGT)

    def log(self, kind: str, text: str, ref: str, day: date, hhmm: str = "09:00") -> None:
        daily.log_event(self.root, kind, text, actor="agent--claude-code", ref=ref, now=at(day, hhmm), tz=SGT)

    def test_week_key_and_range_use_iso_weeks(self) -> None:
        self.assertEqual(weekly.week_key(date(2026, 10, 12)), "2026-W42")
        self.assertEqual(weekly.week_key(date(2026, 10, 18)), "2026-W42")
        self.assertEqual(weekly.week_key(date(2026, 10, 19)), "2026-W43")
        self.assertEqual(weekly.human_range(self.day), "12 to 18 October 2026")
        self.assertEqual(weekly.human_range(date(2026, 10, 1)), "28 September to 4 October 2026")
        self.assertEqual(weekly.human_range(date(2026, 12, 30)), "28 December 2026 to 3 January 2027")

    def test_first_read_creates_week_file_with_human_sections(self) -> None:
        summary = weekly.summarise(self.root, self.day, SGT)
        path = self.root / "weekly" / "2026-W42.md"
        self.assertEqual(summary["path"], "weekly/2026-W42.md")
        text = path.read_text(encoding="utf-8")
        self.assertIn("# Weekly plan: 2026-W42 (12 to 18 October 2026)", text)
        for heading in ("## Priorities", "## Notes", "## Not this week", "## Progress"):
            self.assertIn(heading, text)
        self.assertEqual(summary["priorities"], [])

    def test_add_item_appends_in_order_and_keeps_other_sections(self) -> None:
        self.add("priorities", "Compliance M1")
        self.add("priorities", "Live Fire")
        self.add("notes", "Renew the staging cert")
        self.add("not-this-week", "Dashboard redesign")
        summary = weekly.summarise(self.root, self.day, SGT)
        self.assertEqual(summary["priorities"], [{"text": "Compliance M1", "done": False}, {"text": "Live Fire", "done": False}])
        self.assertEqual(summary["notes"], [{"text": "Renew the staging cert", "done": False}])
        self.assertEqual(summary["not_this_week"], [{"text": "Dashboard redesign", "done": None}])
        text = (self.root / "weekly" / "2026-W42.md").read_text(encoding="utf-8")
        self.assertIn("## Priorities\n\n<!--", text)
        self.assertIn("-->\n\n- [ ] Compliance M1\n- [ ] Live Fire\n\n## Notes", text)

    def test_human_edits_survive_progress_regeneration(self) -> None:
        path = self.add("priorities", "Compliance M1")
        text = path.read_text(encoding="utf-8").replace("- [ ] Compliance M1", "- [x] Compliance M1\n- Free text bullet")
        path.write_text(text, encoding="utf-8")
        self.log("done", "Lock fix merged", "GET-1", self.day)
        weekly.summarise(self.root, self.day, SGT)
        after = path.read_text(encoding="utf-8")
        self.assertIn("- [x] Compliance M1\n- Free text bullet", after)
        self.assertEqual(after.count("## Progress"), 1)

    def test_progress_rolls_up_the_weeks_daily_logs(self) -> None:
        monday, tuesday = date(2026, 10, 12), date(2026, 10, 13)
        self.log("started", "Lock fix", "GET-1", monday)
        self.log("spawned", "Follow-up", "GET-2", monday, "10:00")
        self.log("done", "Lock fix", "GET-1", tuesday)
        self.log("blocked", "Waiting on IAM", "GET-3", tuesday, "11:00")
        self.log("done", "Last week work", "GET-9", date(2026, 10, 9))
        progress = weekly.summarise(self.root, self.day, SGT)["progress"]
        self.assertEqual([entry["ref"] for entry in progress["done"]], ["GET-1"])
        self.assertEqual(progress["spawned"], 1)
        self.assertEqual(progress["open"]["blocked"], 1)
        self.assertEqual([entry["date"] for entry in progress["days"]], ["2026-10-12", "2026-10-13"])
        self.assertIn("- [GET-1] Lock fix", (self.root / "weekly" / "2026-W42.md").read_text(encoding="utf-8"))

    def test_new_week_carries_unticked_priorities_and_notes_once(self) -> None:
        last_week = date(2026, 10, 7)
        path = self.add("priorities", "Finish DB locking", day=last_week)
        self.add("priorities", "Ship epics", day=last_week)
        self.add("notes", "Ask about the cert", day=last_week)
        self.add("not-this-week", "Redesign", day=last_week)
        path.write_text(path.read_text(encoding="utf-8").replace("- [ ] Ship epics", "- [x] Ship epics"), encoding="utf-8")
        summary = weekly.summarise(self.root, self.day, SGT)
        self.assertEqual(summary["priorities"], [{"text": "Finish DB locking (from 2026-W41)", "done": False}])
        self.assertEqual(summary["notes"], [{"text": "Ask about the cert (from 2026-W41)", "done": False}])
        self.assertEqual(summary["not_this_week"], [])
        later = weekly.summarise(self.root, date(2026, 10, 21), SGT)
        self.assertEqual(later["priorities"], [{"text": "Finish DB locking (from 2026-W41)", "done": False}])

    def test_rejects_unknown_section_and_empty_text(self) -> None:
        with self.assertRaises(ValueError):
            self.add("goals", "nope")
        with self.assertRaises(ValueError):
            self.add("notes", "   ")


class WeeklyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for marker in ("preferences", "templates", "workflows", ".braingent"):
            (self.root / marker).mkdir()
        (self.root / "preferences" / "taxonomy.yml").write_text("record_scan_roots: []\n", encoding="utf-8")
        (self.root / ".braingent" / "config.toml").write_text('[daily]\ntimezone = "Asia/Singapore"\n', encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
        return subprocess.run(
            [sys.executable, "-m", "braingent", "--root", str(self.root), *args],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_weekly_add_then_weekly_json(self) -> None:
        added = self.run_cli("weekly-add", "Compliance M1", "--section", "priorities", "--date", "2026-10-14")
        self.assertEqual(added.returncode, 0, added.stderr)
        self.assertEqual(added.stdout.strip(), "weekly/2026-W42.md")
        shown = self.run_cli("weekly", "--date", "2026-10-12", "--json")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(json.loads(shown.stdout)["priorities"], [{"text": "Compliance M1", "done": False}])
        text = self.run_cli("weekly", "--date", "2026-10-18")
        self.assertIn("1. [ ] Compliance M1", text.stdout)


if __name__ == "__main__":
    unittest.main()

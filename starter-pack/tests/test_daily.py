from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock
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
        self.assertIn("Timezone: Asia/Singapore", text)
        self.assertFalse(text.startswith("---"))
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

    def test_goals_and_other_sections_are_not_events(self) -> None:
        path = self.log("started", "Actual work", ref="GET-1")
        text = path.read_text(encoding="utf-8")
        text = text.replace("## Goals\n", "## Goals\n\n- 09:00 · human · done · GET-1 · Goal example\n", 1)
        text += "\n## Notes\n\n- 10:00 · human · done · GET-1 · Another example\n"
        path.write_text(text, encoding="utf-8")
        self.log("note", "Still working")
        summary = daily.summarise(self.root, self.day, tz=SGT)
        self.assertEqual(summary["counts"]["ongoing"], 1)
        self.assertEqual(summary["counts"]["done"], 0)
        events = daily.parse_events(path.read_text(encoding="utf-8"))
        self.assertEqual([event.text for event in events], ["Actual work", "Still working"])
        self.assertTrue(path.read_text(encoding="utf-8").endswith("· Another example\n"))

    def test_markers_in_event_text_do_not_corrupt_status(self) -> None:
        body = f"Explain {daily.STATUS_START} and {daily.STATUS_END}"
        path = self.log("started", body, ref="GET-1")
        original_line = daily.parse_events(path.read_text(encoding="utf-8"))[0].line()
        self.log("done", "Explained markers", ref="GET-1")
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.splitlines().count(daily.STATUS_START), 1)
        self.assertEqual(text.splitlines().count(daily.STATUS_END), 1)
        self.assertEqual(text.splitlines().count(original_line), 1)
        self.assertEqual([event.kind for event in daily.parse_events(text)], ["started", "done"])

    def test_empty_actor_is_rejected_before_creating_file(self) -> None:
        for actor in ("", " ", "\n\t"):
            with self.subTest(actor=actor), self.assertRaises(ValueError):
                self.log("started", "Invalid metadata", actor=actor, ref="GET-1")
        self.assertFalse((self.root / "daily").exists())

    def test_summary_and_carry_over_read_under_lock(self) -> None:
        path = self.log("started", "Long running", ref="GET-1")
        with mock.patch.object(daily, "locked", wraps=daily.locked) as acquire:
            daily.summarise(self.root, self.day, tz=SGT)
            self.assertEqual([call.args[0] for call in acquire.call_args_list], [path, path])
        with mock.patch.object(daily, "locked", wraps=daily.locked) as acquire:
            self.log("note", "Tomorrow", day=date(2026, 10, 7))
            self.assertIn(path, [call.args[0] for call in acquire.call_args_list])

    def test_windows_locks_the_day_file_and_flushes_before_unlock(self) -> None:
        windows = mock.Mock(LK_LOCK=1, LK_UNLCK=0)
        path = daily.day_path(self.root, self.day)

        def check_unlock(descriptor: int, mode: int, count: int) -> None:
            if mode == windows.LK_UNLCK:
                self.assertEqual(path.read_text(encoding="utf-8"), "Logged event\n")

        windows.locking.side_effect = check_unlock
        with mock.patch.object(daily, "fcntl", None), mock.patch.dict(sys.modules, {"msvcrt": windows}):
            with daily.locked(path) as handle:
                windows.locking.assert_called_once_with(handle.fileno(), windows.LK_LOCK, 1)
                handle.write("Logged event\n")
                descriptor = handle.fileno()
            self.assertEqual(windows.locking.call_args_list[-1], mock.call(descriptor, windows.LK_UNLCK, 1))
        self.assertEqual(path.read_text(encoding="utf-8"), "Logged event\n")

    def test_crlf_goals_are_preserved_byte_for_byte(self) -> None:
        path = self.log("started", "First task", ref="GET-1")
        text = path.read_text(encoding="utf-8").replace("\n", "\r\n")
        path.write_bytes(text.encode("utf-8"))
        original_goals = path.read_bytes().split(daily.STATUS_START.encode())[0]
        self.log("done", "First task", ref="GET-1")
        self.assertEqual(path.read_bytes().split(daily.STATUS_START.encode())[0], original_goals)
        self.assertEqual(daily.summarise(self.root, self.day, tz=SGT)["counts"]["done"], 1)

    def test_concurrent_writers_keep_every_event(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)
        script = (
            "import sys; from pathlib import Path; from datetime import datetime; "
            "from zoneinfo import ZoneInfo; from braingent import daily; "
            "zone = ZoneInfo('Asia/Singapore'); "
            "daily.log_event(Path(sys.argv[1]), 'started', 'Task ' + sys.argv[2], "
            "actor='agent-' + sys.argv[2], ref='TASK-' + sys.argv[2], "
            "now=datetime(2026, 10, 6, 9, tzinfo=zone), tz=zone)"
        )
        processes = [
            subprocess.Popen(
                [sys.executable, "-c", script, str(self.root), str(index)],
                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            for index in range(12)
        ]
        for process in processes:
            _, stderr = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, stderr)
        summary = daily.summarise(self.root, self.day, tz=SGT)
        self.assertEqual(summary["counts"]["ongoing"], 12)
        path = daily.day_path(self.root, self.day)
        events = daily.parse_events(path.read_text(encoding="utf-8"))
        self.assertEqual({event.ref for event in events}, {f"TASK-{index}" for index in range(12)})
        self.assertEqual(len(events), 12)

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


class DailyEpicTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.day = date(2026, 10, 6)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def log(self, kind: str, text: str, ref: str | None = None, epic: str | None = None, hhmm: str = "09:00") -> Path:
        return daily.log_event(self.root, kind, text, actor="agent--claude-code", ref=ref, epic=epic, now=at(self.day, hhmm), tz=SGT)

    def test_epic_round_trips_through_the_log_line(self) -> None:
        path = self.log("started", "Index audit", ref="app-repo#12", epic="db-audit")
        text = path.read_text(encoding="utf-8")
        self.assertIn("- 09:00 · agent--claude-code · started · app-repo#12 · Index audit · epic:db-audit", text)
        (event,) = daily.parse_events(text)
        self.assertEqual((event.text, event.epic), ("Index audit", "db-audit"))
        self.assertEqual(event.line(), "- 09:00 · agent--claude-code · started · app-repo#12 · Index audit · epic:db-audit")

    def test_epic_id_is_reduced_to_its_slug(self) -> None:
        path = self.log("note", "Link", epic="epic--acme--db-audit")
        self.assertEqual(daily.parse_events(path.read_text(encoding="utf-8"))[0].epic, "db-audit")

    def test_invalid_epic_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.log("note", "Bad", epic="Not A Slug")

    def test_lines_without_an_epic_still_parse_and_render_unchanged(self) -> None:
        legacy = "- 09:42 · agent--claude-code · started · GET-1234 · Verdict lock fix"
        text = f"# Daily log\n\n## Log\n\n{legacy}\n"
        (event,) = daily.parse_events(text)
        self.assertIsNone(event.epic)
        self.assertEqual(event.line(), legacy)
        path = self.log("started", "No epic", ref="GET-2")
        self.assertNotIn("epic:", path.read_text(encoding="utf-8"))
        self.assertNotIn("### By epic", path.read_text(encoding="utf-8"))

    def test_text_containing_epic_text_mid_line_is_preserved(self) -> None:
        path = self.log("note", "mentions epic:x in passing and more", epic="db-audit")
        (event,) = daily.parse_events(path.read_text(encoding="utf-8"))
        self.assertEqual((event.text, event.epic), ("mentions epic:x in passing and more", "db-audit"))

    def test_per_epic_rollup_counts_spawned_and_untouched(self) -> None:
        self.log("spawned", "Ticket A", ref="GET-1", epic="db-audit")
        self.log("spawned", "Ticket B", ref="GET-2", epic="db-audit")
        self.log("started", "Ticket B", ref="GET-2", epic="db-audit")
        self.log("spawned", "Ticket C", ref="GET-3", epic="performance")
        summary = daily.summarise(self.root, self.day, tz=SGT)
        self.assertEqual(summary["epics"], {"db-audit": {"spawned": 2, "untouched": 1}, "performance": {"spawned": 1, "untouched": 1}})
        text = daily.day_path(self.root, self.day).read_text(encoding="utf-8")
        self.assertIn("- epic:db-audit: 2 spawned (1 untouched)", text)

    def test_sprawl_warning_names_driving_epics(self) -> None:
        for index in range(3):
            self.log("spawned", f"Ticket {index}", ref=f"GET-{index}", epic="db-audit")
        self.log("spawned", "Other", ref="GET-9", epic="performance")
        path = daily.update_day(self.root, self.day, SGT, sprawl_threshold=4)
        self.assertIn("> Spawned by epic: db-audit (3), performance (1).", path.read_text(encoding="utf-8"))

    def test_carry_over_keeps_the_epic(self) -> None:
        self.log("started", "Long running", ref="GET-1", epic="db-audit")
        next_day = date(2026, 10, 7)
        path = daily.log_event(self.root, "note", "Next day", actor="agent--claude-code", now=at(next_day, "09:00"), tz=SGT)
        carried = [event for event in daily.parse_events(path.read_text(encoding="utf-8")) if event.actor == daily.CARRY_ACTOR]
        self.assertEqual([event.epic for event in carried], ["db-audit"])


if __name__ == "__main__":
    unittest.main()

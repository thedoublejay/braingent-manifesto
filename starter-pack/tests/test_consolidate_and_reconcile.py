from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from braingent import capture, consolidate, core, daily, reconcile

PACK_ROOT = Path(__file__).resolve().parents[1]
ZONE = ZoneInfo("UTC")
DAY = date(2026, 10, 5)
NOW = datetime(2026, 10, 5, 9, 0, tzinfo=ZONE)


def record_text(title: str, kind: str, status: str, extra: str = "") -> str:
    return (
        f"---\ntitle: {title}\nrecord_kind: {kind}\nstatus: {status}\ndate: 2026-10-07\ntimezone: UTC\n"
        f"organization: org--acme\nproject: null\n{extra}---\n\n# {title}\n\nBody.\n"
    )


class DreamTests(unittest.TestCase):
    def test_cyclic_and_self_supersession_need_a_decision(self) -> None:
        for field in ("supersedes", "superseded_by"):
            with self.subTest(field=field):
                prefix = f"orgs/org--acme/records/{field}"
                first = self.write(f"{field}-a.md", "Cache policy alpha", "decision", "accepted", f"{field}: {prefix}-b.md\n")
                second = self.write(f"{field}-b.md", "Cache policy beta", "decision", "accepted", f"{field}: {first}\n")
                own = self.write(f"{field}-self.md", "Cache policy self", "decision", "accepted", f"{field}: {prefix}-self.md\n")
                before = {path: (self.root / path).read_bytes() for path in (first, second, own)}
                pending = [item for item in consolidate.proposals() if item.path in before]
                self.assertEqual({item.path for item in pending}, set(before))
                self.assertTrue(all(item.kind == "state-relation" and item.change is None for item in pending))
                self.assertEqual(self.run_cli("--apply", *[item.id for item in pending])[0], 1)
                self.assertEqual({path: (self.root / path).read_bytes() for path in before}, before)

    def test_mixed_supersession_cycle_is_not_applied(self) -> None:
        first = "orgs/org--acme/records/a.md"
        second = self.write("b.md", "Cache policy beta", "decision", "accepted")
        self.write("a.md", "Cache policy alpha", "decision", "accepted", f"supersedes: {second}\nsuperseded_by: {second}\n")
        pending = consolidate.proposals()
        self.assertEqual({item.path for item in pending}, {first, second})
        self.assertTrue(all(item.change is None for item in pending))

    def test_a_failed_batch_restores_already_written_records(self) -> None:
        half, old, _ = self.seed()
        pending = [item.id for item in consolidate.proposals() if item.change is not None]
        originals = {self.root / name: (self.root / name).read_bytes() for name in (half, old)}
        replace = capture.replace_bytes
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("write failed")
            replace(path, content)

        with patch.object(capture, "replace_bytes", side_effect=fail_second), self.assertRaises(SystemExit):
            self.run_cli("--apply", *pending)
        for path, content in originals.items():
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(Path(f"{path}.bak").read_bytes(), content)

    def test_link_proposal_expires_when_its_target_changes(self) -> None:
        _, old, _ = self.seed()
        wanted = next(item.id for item in consolidate.proposals() if item.kind == "link-superseded-by")
        path = self.root / old
        path.write_text(path.read_text(encoding="utf-8").replace("status: accepted", "status: rejected"), encoding="utf-8")
        code, out = self.run_cli("--apply", wanted)
        self.assertEqual(code, 1, out)
        self.assertEqual(self.status_of(old), ("rejected", None))

    def test_competing_successors_need_a_decision(self) -> None:
        _, old, _ = self.seed()
        self.write("2026-10-01--decision--vendor-c.md", "Cache layer moves to Vendor C", "decision", "accepted", f"supersedes: {old}\n")
        pending = [item for item in consolidate.proposals() if item.path == old]
        self.assertTrue(pending)
        self.assertTrue(all(item.change is None for item in pending))
        self.assertEqual(self.run_cli("--apply", *[item.id for item in pending])[0], 1)
        self.assertEqual(self.status_of(old), ("accepted", None))

    def test_apply_keeps_a_backup_of_the_original_record(self) -> None:
        half, _, _ = self.seed()
        before = (self.root / half).read_bytes()
        wanted = next(item.id for item in consolidate.proposals() if item.kind == "mark-superseded")
        self.assertEqual(self.run_cli("--apply", wanted)[0], 0)
        self.assertEqual((self.root / f"{half}.bak").read_bytes(), before)

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        shutil.copytree(PACK_ROOT / "preferences", self.root / "preferences")
        (self.root / "templates").mkdir()
        (self.root / "workflows").mkdir()
        self.records = self.root / "orgs" / "org--acme" / "records"
        self.records.mkdir(parents=True)
        core.set_repo_root(self.root)
        self.addCleanup(core.set_repo_root, PACK_ROOT)
        self.addCleanup(self._tmp.cleanup)

    def write(self, name: str, title: str, kind: str, status: str, extra: str = "") -> str:
        (self.records / name).write_text(record_text(title, kind, status, extra), encoding="utf-8")
        return f"orgs/org--acme/records/{name}"

    def run_cli(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = core.main(["--root", str(self.root), "dream", *argv])
        return code, out.getvalue()

    def status_of(self, relpath: str) -> tuple[str, object]:
        frontmatter, _, _ = core.split_frontmatter(self.root / relpath)
        assert frontmatter is not None
        return frontmatter["status"], frontmatter.get("superseded_by")

    def seed(self) -> tuple[str, str, str]:
        new = self.write("2026-10-02--task--recheck.md", "Model access recheck", "task", "completed")
        half = self.write("2026-09-24--task--probe.md", "Model access probe", "task", "completed", f"superseded_by: {new}\n")
        old = self.write("2026-08-15--decision--vendor-a.md", "Cache layer is Vendor A", "decision", "accepted")
        self.write("2026-09-16--decision--vendor-b.md", "Cache layer moves to Vendor B", "decision", "accepted", f"supersedes: {old}\n")
        self.write("2026-10-03--learning--dangling.md", "Dangling", "learning", "active", "related_records: [orgs/org--acme/records/missing.md]\n")
        self.write("2026-10-04--review--first.md", "First review", "review", "completed", "source: acme/api#12\nsource_revision: abc1234\n")
        self.write("2026-10-04--review--second.md", "Second review", "review", "completed", "source: acme/api#12\nsource_revision: abc1234\n")
        return half, old, new

    def test_listing_proposes_and_changes_nothing(self) -> None:
        self.seed()
        before = {path.name: path.read_text(encoding="utf-8") for path in self.records.iterdir()}
        code, out = self.run_cli("--json")
        self.assertEqual(code, 0)
        kinds = sorted(item["kind"] for item in json.loads(out)["proposals"])
        self.assertEqual(kinds, ["broken-link", "duplicate-source", "link-superseded-by", "mark-superseded"])
        self.assertEqual({path.name: path.read_text(encoding="utf-8") for path in self.records.iterdir()}, before)
        _, text = self.run_cli()
        self.assertIn("Nothing has been changed.", text)

    def test_apply_makes_the_stated_change_and_only_that(self) -> None:
        half, old, _ = self.seed()
        by_kind = {item.kind: item for item in consolidate.proposals()}
        code, out = self.run_cli("--apply", by_kind["mark-superseded"].id, by_kind["link-superseded-by"].id)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.status_of(half)[0], "superseded")
        self.assertEqual(self.status_of(old), ("superseded", "orgs/org--acme/records/2026-09-16--decision--vendor-b.md"))
        self.assertEqual(sorted(item.kind for item in consolidate.proposals()), ["broken-link", "duplicate-source"])

    def test_a_proposal_whose_record_changed_is_not_applied(self) -> None:
        half, _, _ = self.seed()
        stale_id = next(item.id for item in consolidate.proposals() if item.kind == "mark-superseded")
        path = self.root / half
        path.write_text(path.read_text(encoding="utf-8").replace("status: completed", "status: active"), encoding="utf-8")
        code, out = self.run_cli("--apply", stale_id)
        self.assertEqual(code, 1)
        self.assertIn("no longer applies", out)
        self.assertEqual(self.status_of(half)[0], "active")

    def test_manual_proposals_cannot_be_applied_and_rejected_ones_stay_hidden(self) -> None:
        self.seed()
        manual = next(item.id for item in consolidate.proposals() if item.kind == "duplicate-source")
        code, out = self.run_cli("--apply", manual)
        self.assertEqual(code, 1)
        self.assertIn("needs a person or agent", out)
        self.run_cli("--reject", manual)
        self.assertNotIn(manual, [item.id for item in consolidate.proposals()])

    def test_live_decisions_on_one_subject_ask_for_their_relation(self) -> None:
        self.write("2026-08-15--decision--a.md", "Retention window ninety days", "decision", "accepted")
        self.write("2026-09-15--decision--b.md", "Retention window thirty days", "decision", "accepted")
        self.assertEqual([item.kind for item in consolidate.proposals()], ["state-relation"])

    def test_limit_bounds_the_listing(self) -> None:
        self.seed()
        _, out = self.run_cli("--limit", "1", "--json")
        payload = json.loads(out)
        self.assertEqual((payload["total"], len(payload["proposals"])), (4, 1))


class ReconcileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.calls: list[list[str]] = []
        for kind, text, ref in (
            ("started", "Retry change", "api#12"),
            ("review", "Cache change", "acme/web#7"),
            ("started", "Still open", "api#13"),
            ("started", "Lookup fails", "api#99"),
            ("blocked", "Blocked change", "api#14"),
            ("started", "Ticket work", "EX-5"),
        ):
            daily.log_event(self.root, kind, text, actor="agent--one", ref=ref, now=NOW, tz=ZONE)

    def runner(self, arguments: list[str]) -> str:
        self.calls.append(arguments)
        number, repo = arguments[2], arguments[4]
        if number == "99":
            raise RuntimeError("HTTP 502\nmore detail")
        if repo == "wrong/api":
            raise RuntimeError("not found")
        return json.dumps({"state": {"12": "MERGED", "7": "MERGED", "13": "OPEN"}[number], "url": f"https://example.test/{repo}/pull/{number}"})

    def reconcile(self, apply: bool) -> dict:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = reconcile.run(self.root, DAY, ZONE, ["wrong", "acme"], apply=apply, output_json=True, runner=self.runner, now=NOW)
        self.assertEqual(code, 0)
        return json.loads(out.getvalue())

    def counts(self) -> dict[str, int]:
        return daily.summarise(self.root, DAY, tz=ZONE)["counts"]

    def test_dry_run_reports_and_logs_nothing(self) -> None:
        before = daily.day_path(self.root, DAY).read_text(encoding="utf-8")
        summary = self.reconcile(apply=False)
        self.assertEqual((summary["checked"], summary["merged"], summary["unknown"]), (4, 2, 1))
        self.assertEqual(daily.day_path(self.root, DAY).read_text(encoding="utf-8"), before)
        self.assertEqual({call[2] for call in self.calls}, {"12", "7", "13", "99"})

    def test_apply_moves_merged_items_to_merged_and_closes_nothing(self) -> None:
        before = self.counts()
        summary = self.reconcile(apply=True)
        after = self.counts()
        self.assertEqual(after["landed"], 2)
        self.assertEqual(after["done"], before["done"])
        self.assertEqual(after["blocked"], 1)
        states = {row["ref"]: (row["state"], row["logged"]) for row in summary["items"]}
        self.assertEqual(states["api#12"], ("merged", True))
        self.assertEqual(states["api#13"], ("open", False))
        self.assertEqual(states["api#99"], ("unknown", False))
        self.assertEqual(next(row["detail"] for row in summary["items"] if row["ref"] == "api#99"), "HTTP 502")
        self.assertIn("· reconcile · merged · api#12 ·", daily.day_path(self.root, DAY).read_text(encoding="utf-8"))

    def test_a_second_run_does_not_log_twice(self) -> None:
        self.reconcile(apply=True)
        self.calls.clear()
        summary = self.reconcile(apply=True)
        self.assertEqual(summary["merged"], 0)
        self.assertNotIn("12", {call[2] for call in self.calls})

    def test_limit_is_reported_not_silent(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            reconcile.run(self.root, DAY, ZONE, ["acme"], limit=1, output_json=True, runner=self.runner, now=NOW)
        summary = json.loads(out.getvalue())
        self.assertEqual((summary["checked"], summary["skipped"]), (1, 3))

    def test_dry_run_on_a_new_day_creates_no_files(self) -> None:
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()):
            reconcile.run(self.root, date(2026, 10, 20), ZONE, ["acme"], runner=self.runner, stale_after_days=3)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(after, before)

    def test_ambiguous_owner_does_not_select_an_arbitrary_pr(self) -> None:
        def lookup(arguments: list[str]) -> str:
            return json.dumps({"state": "MERGED", "url": f"https://example.test/{arguments[4]}/pull/{arguments[2]}"})

        state, detail = reconcile.pr_state("api#12", ["first", "second"], lookup)
        self.assertEqual(state, "unknown")
        self.assertIn("ambiguous", detail)

    def test_historical_apply_logs_to_the_requested_day(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            reconcile.run(self.root, DAY, ZONE, ["acme"], apply=True, runner=self.runner)
        events = daily.parse_events(daily.day_path(self.root, DAY).read_text(encoding="utf-8"))
        self.assertTrue(any(event.kind == "merged" and event.ref == "api#12" for event in events))
        self.assertEqual(list((self.root / "daily").glob("????-??-??.md")), [daily.day_path(self.root, DAY)])

    def test_apply_preserves_a_newer_verified_event(self) -> None:
        def lookup(arguments: list[str]) -> str:
            if arguments[2] == "12":
                daily.log_event(self.root, "verified", "Verified during lookup", actor="agent--two", ref="api#12", now=NOW, tz=ZONE)
            return self.runner(arguments)

        with contextlib.redirect_stdout(io.StringIO()):
            reconcile.run(self.root, DAY, ZONE, ["acme"], apply=True, runner=lookup, now=NOW)
        status = daily.derive_status(daily.parse_events(daily.day_path(self.root, DAY).read_text(encoding="utf-8")))
        self.assertIn("api#12", {event.ref for event in status.buckets["done"]})

    def test_an_existing_note_does_not_block_reconciliation(self) -> None:
        daily.log_event(self.root, "note", "Existing context", actor="agent--two", ref="api#12", now=NOW, tz=ZONE)
        summary = self.reconcile(apply=True)
        self.assertTrue(next(row["logged"] for row in summary["items"] if row["ref"] == "api#12"))

    def test_non_positive_limit_writes_and_queries_nothing(self) -> None:
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        for limit in (0, -1):
            with self.subTest(limit=limit), self.assertRaisesRegex(ValueError, "limit must be greater than zero"):
                reconcile.run(self.root, DAY, ZONE, ["acme"], apply=True, limit=limit, runner=self.runner, now=NOW)
        self.assertEqual(self.calls, [])
        self.assertEqual({p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}, before)

    def test_cli_rejects_non_positive_limits(self) -> None:
        for command in ("daily-reconcile", "dream"):
            for limit in ("0", "-1"):
                with self.subTest(command=command, limit=limit), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as result:
                        core.build_parser().parse_args([command, "--limit", limit])
                    self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from braingent import capture, core

PACK_ROOT = Path(__file__).resolve().parents[1]
ENTITY = "project--acme--billing"
OUT = "orgs/org--acme/projects/project--acme--billing/records"


class CaptureTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        shutil.copytree(PACK_ROOT / "preferences", self.root / "preferences")
        shutil.copytree(PACK_ROOT / "templates", self.root / "templates")
        (self.root / "scripts").mkdir()
        shutil.copy2(PACK_ROOT / "scripts" / "new-record.sh", self.root / "scripts" / "new-record.sh")
        (self.root / "workflows").mkdir()
        (self.root / OUT).mkdir(parents=True)
        core.set_repo_root(self.root)
        self.addCleanup(core.set_repo_root, PACK_ROOT)
        self.addCleanup(self._tmp.cleanup)

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = core.main(["--root", str(self.root), "capture", *argv])
        return code, out.getvalue().strip(), err.getvalue()

    def frontmatter(self, relpath: str) -> dict:
        frontmatter, _, error = core.split_frontmatter(self.root / relpath)
        self.assertIsNone(error)
        assert frontmatter is not None
        return frontmatter

    def records(self) -> list[str]:
        return sorted(path.name for path in (self.root / OUT).glob("*.md"))


class SameSourceTests(CaptureTestCase):
    def test_a_retry_of_the_same_source_and_revision_creates_nothing(self) -> None:
        code, path, _ = self.run_cli("review", ENTITY, "Review of the billing retry change", OUT, "--source", "acme/billing-api#12", "--revision", "abc1234")
        self.assertEqual(code, 0)
        fm = self.frontmatter(path)
        self.assertEqual((fm["source"], fm["source_revision"]), ("acme/billing-api#12", "abc1234"))
        self.assertTrue(fm["captured_at"])

        code, again, err = self.run_cli("review", ENTITY, "Review of the billing retry change", OUT, "--source", "acme/billing-api#12", "--revision", "abc1234")
        self.assertEqual((code, again), (0, path))
        self.assertIn("already captured", err)
        self.assertEqual(len(self.records()), 1)

    def test_a_new_revision_of_the_same_source_is_a_new_record(self) -> None:
        _, first, _ = self.run_cli("review", ENTITY, "Review of the billing retry change", OUT, "--source", "acme/billing-api#12", "--revision", "abc1234")
        code, second, err = self.run_cli("review", ENTITY, "Review of the billing retry change", OUT, "--source", "acme/billing-api#12", "--revision", "def5678")
        self.assertEqual(code, 0)
        self.assertNotEqual(first, second)
        self.assertEqual(len(self.records()), 2)
        self.assertIn("similar records", err)
        self.assertIn(first, err)

    def test_without_a_source_nothing_is_deduplicated(self) -> None:
        self.run_cli("task", ENTITY, "Rotate the widget", OUT)
        self.run_cli("task", ENTITY, "Rotate the widget", OUT)
        self.assertEqual(len(self.records()), 2)

    def test_check_writes_nothing_and_reports_json(self) -> None:
        code, out, _ = self.run_cli("task", ENTITY, "Rotate the widget", OUT, "--check", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "clear")
        self.assertEqual(self.records(), [])


class DecisionConflictTests(CaptureTestCase):
    def first_decision(self) -> str:
        code, path, _ = self.run_cli("decision", ENTITY, "Identity provider is Vendor A", OUT)
        self.assertEqual(code, 0)
        target = self.root / path
        target.write_text(capture.set_frontmatter(target.read_text(encoding="utf-8"), {"status": "accepted"}), encoding="utf-8")
        return path

    def test_a_similar_live_decision_blocks_until_the_relation_is_stated(self) -> None:
        first = self.first_decision()
        code, out, err = self.run_cli("decision", ENTITY, "Identity provider moves to Vendor B", OUT)
        self.assertEqual((code, out), (capture.EXIT_CONFLICT, ""))
        self.assertIn(first, err)
        self.assertIn("--supersedes", err)
        self.assertEqual(len(self.records()), 1)

    def test_supersedes_links_both_records_and_only_then_changes_the_old_one(self) -> None:
        first = self.first_decision()
        code, second, err = self.run_cli("decision", ENTITY, "Identity provider moves to Vendor B", OUT, "--supersedes", first)
        self.assertEqual(code, 0)
        self.assertEqual(self.frontmatter(second)["supersedes"], first)
        old = self.frontmatter(first)
        self.assertEqual((old["status"], old["superseded_by"]), ("superseded", second))
        self.assertIn("marked superseded", err)
        self.assertIn("Identity provider is Vendor A", (self.root / first).read_text(encoding="utf-8"))

    def test_coexists_with_records_the_relation_and_quiets_the_conflict_warning(self) -> None:
        first = self.first_decision()
        code, second, _ = self.run_cli("decision", ENTITY, "Identity provider for the partner portal", OUT, "--coexists-with", first)
        self.assertEqual(code, 0)
        self.assertEqual(self.frontmatter(second)["coexists_with"], [first])
        self.assertEqual(self.frontmatter(first)["status"], "accepted")
        target = self.root / second
        target.write_text(capture.set_frontmatter(target.read_text(encoding="utf-8"), {"status": "accepted"}), encoding="utf-8")
        self.assertEqual([issue.message for issue in core.validate() if "implicit conflict" in issue.message], [])

    def test_unrelated_captures_without_touching_anything(self) -> None:
        first = self.first_decision()
        before = (self.root / first).read_text(encoding="utf-8")
        code, _, _ = self.run_cli("decision", ENTITY, "Identity provider logo placement", OUT, "--unrelated")
        self.assertEqual(code, 0)
        self.assertEqual((self.root / first).read_text(encoding="utf-8"), before)

    def test_a_decision_that_only_shares_one_word_does_not_block(self) -> None:
        self.first_decision()
        code, path, _ = self.run_cli("decision", ENTITY, "Queue backend for the notification provider", OUT)
        self.assertEqual(code, 0)
        self.assertTrue(path)

    def test_superseded_decisions_do_not_block(self) -> None:
        first = self.first_decision()
        self.run_cli("decision", ENTITY, "Identity provider moves to Vendor B", OUT, "--supersedes", first)
        code, _, err = self.run_cli("decision", ENTITY, "Identity provider moves to Vendor C", OUT, "--check")
        self.assertEqual(code, capture.EXIT_CONFLICT)
        self.assertNotIn("is-vendor-a", err.split("live decisions")[1])

    def test_supersedes_must_name_a_decision(self) -> None:
        self.run_cli("task", ENTITY, "Rotate the widget", OUT)
        task = f"{OUT}/{self.records()[0]}"
        with self.assertRaises(SystemExit):
            self.run_cli("decision", ENTITY, "Widget rotation policy", OUT, "--supersedes", task)


class SetFrontmatterTests(unittest.TestCase):
    def test_replaces_or_appends_and_keeps_other_lines(self) -> None:
        text = "---\ntitle: A  # keep\nstatus: proposed\n---\n\nBody with status: text.\n"
        updated = capture.set_frontmatter(text, {"status": "accepted", "source": "x#1"})
        self.assertEqual(updated, '---\ntitle: A  # keep\nstatus: "accepted"\nsource: "x#1"\n---\n\nBody with status: text.\n')


if __name__ == "__main__":
    unittest.main()

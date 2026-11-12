from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from braingent import core as braingent
from braingent import mcp_tools
from braingent.compressors import render_summary_depth


class RecordLikePathTests(unittest.TestCase):
    def test_attachments_are_not_record_like(self) -> None:
        path = braingent.REPO_ROOT / "repositories/repo--example--owner--repo/records/attachments/note.md"
        self.assertFalse(braingent.is_record_like_path(path))

    def test_durable_record_is_record_like(self) -> None:
        path = braingent.REPO_ROOT / "topics/topic--ai-memory/records/sample.md"
        self.assertTrue(braingent.is_record_like_path(path))


class ValidationSeverityTests(unittest.TestCase):
    def test_missing_task_commits_is_a_warning(self) -> None:
        record = braingent.Record(
            path=braingent.REPO_ROOT / "orgs/org--example/projects/project--example--memory/records/sample.md",
            frontmatter={
                "title": "Sample",
                "record_kind": "task",
                "status": "completed",
                "date": "2026-09-17",
                "timezone": "UTC",
                "organization": "org--example",
                "project": "project--example--memory",
                "ticket": None,
                "repositories": [],
                "prs": [],
                "ai_tools": ["Grok"],
            },
            body="",
        )
        issues = braingent.validate_record(record, braingent.load_taxonomy())
        messages = [issue.message for issue in issues]
        self.assertTrue(any("missing required field `commits`" in message for message in messages))
        self.assertTrue(all(issue.severity == "warning" for issue in issues if "commits" in issue.message))

    def test_missing_title_is_an_error(self) -> None:
        record = braingent.Record(
            path=braingent.REPO_ROOT / "topics/topic--ai-memory/records/sample.md",
            frontmatter={"record_kind": "note", "status": "active"},
            body="",
        )
        issues = braingent.validate_record(record, braingent.load_taxonomy())
        self.assertTrue(any(issue.severity == "error" and "title" in issue.message for issue in issues))


class SummaryDepthTests(unittest.TestCase):
    def test_render_summary_depth_is_short(self) -> None:
        text = "---\ntitle: hi\nsummary: short fact\n---\n\n## Goal\n\nlong\n\n## Archived\n\ndrop me\n"
        output = render_summary_depth(text, summary="short fact")
        self.assertIn("short fact", output)
        self.assertNotIn("drop me", output)
        self.assertLess(len(output), 400)

    def test_get_summary_uses_extract_not_full_body(self) -> None:
        record = mcp_tools.get(path="tests/fixtures/sample-records/repo-summary.md", depth="summary")
        self.assertNotIn("deprecated stuff", record["body"])
        self.assertIn("## Summary", record["body"])
        self.assertLess(len(record["body"]), 2000)


class RecallBoundTests(unittest.TestCase):
    def test_recall_omits_overflow_supporting_hits(self) -> None:
        records = []
        for index in range(30):
            records.append(
                braingent.Record(
                    path=braingent.REPO_ROOT / f"topics/topic--ai-memory/records/2026-09-17--note--n{index}.md",
                    frontmatter={
                        "title": f"Note {index}",
                        "record_kind": "note",
                        "status": "active",
                        "date": "2026-09-17",
                    },
                    body="body",
                )
            )
        with mock.patch.object(braingent, "load_records", return_value=(records, [])):
            payload = braingent.recall_payload({"record_kind": ["note"]}, limit=5, stale_days=180)
        self.assertEqual(5, len(payload["must_read"]))
        self.assertEqual(5, len(payload["supporting"]))
        self.assertEqual(20, payload["omitted"]["supporting"])

    def test_superseded_by_is_not_must_read(self) -> None:
        record = braingent.Record(
            path=braingent.REPO_ROOT / "topics/topic--ai-memory/records/old.md",
            frontmatter={
                "title": "Old",
                "record_kind": "decision",
                "status": "accepted",
                "date": "2026-08-15",
                "superseded_by": "new.md",
            },
            body="",
        )
        category, reason = braingent.recall_classification(record, stale_days=180)
        self.assertEqual("do_not_use", category)
        self.assertIn("superseded_by", reason)


class FollowupArchiveTests(unittest.TestCase):
    def test_archives_checkboxes_in_old_completed_followups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "record.md"
            path.write_text(
                "---\nstatus: completed\ndate: 2026-01-01\n---\n\n## Follow-ups\n\n- [ ] do later\n",
                encoding="utf-8",
            )
            record = braingent.Record(
                path=path,
                frontmatter={"status": "completed", "date": "2026-01-01", "record_kind": "task", "title": "x"},
                body=path.read_text(encoding="utf-8"),
            )
            changed = braingent.archive_stale_followups([record], today=date(2026, 9, 17), max_age_days=14)
            self.assertEqual(1, changed)
            self.assertIn("- do later", path.read_text(encoding="utf-8"))
            self.assertNotIn("- [ ] do later", path.read_text(encoding="utf-8"))


class GuideTests(unittest.TestCase):
    def test_guide_is_two_files(self) -> None:
        output = mcp_tools.guide()
        self.assertEqual(["AGENTS.md", "CURRENT_STATE.md"], output["files"])
        self.assertIn("Search before planning", output["content"])


if __name__ == "__main__":
    unittest.main()

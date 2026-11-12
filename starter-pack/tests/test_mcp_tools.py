from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from braingent import core as braingent
from braingent import mcp_tools

TOPIC_RECORD = "topics/topic--ai-memory/README.md"
LEARNING_FIXTURE = "tests/fixtures/sample-records/learning.md"


class McpToolTests(unittest.TestCase):
    def test_find_returns_matches_for_known_topic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_db = Path(tmp_dir) / "missing.db"
            with mock.patch.object(mcp_tools.braingent, "SQLITE_PATH", missing_db):
                results = mcp_tools.find(query={"topic": "ai-memory"}, limit=50)

        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 50)
        self.assertTrue(all("path" in item and "title" in item for item in results))
        self.assertTrue(any(item["path"] == TOPIC_RECORD for item in results))

    def test_find_empty_query_returns_compact_records(self) -> None:
        results = mcp_tools.find(query={}, limit=3)
        allowed = {"path", "title", "kind", "date", "org", "repo", "project", "ticket", "status"}

        self.assertEqual(3, len(results))
        self.assertTrue(all(set(item) <= allowed for item in results))

    def test_find_exact_filter_uses_sqlite_index_without_loading_records(self) -> None:
        record = braingent.Record(
            path=braingent.REPO_ROOT / "topics/topic--sample/records/2026-05-06--learning--indexed.md",
            frontmatter={
                "title": "Indexed lookup",
                "record_kind": "learning",
                "status": "active",
                "date": "2026-05-06",
                "topic": "topic--sample",
            },
            body="",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "braingent.db"
            braingent.write_sqlite_index([record], db_path=db_path)

            with (
                mock.patch.object(mcp_tools.braingent, "SQLITE_PATH", db_path),
                mock.patch.object(mcp_tools.braingent, "load_records", side_effect=AssertionError("loaded records")),
            ):
                results = mcp_tools.find(query={"topic": "sample"}, limit=5)

        self.assertEqual(
            [
                {
                    "path": "topics/topic--sample/records/2026-05-06--learning--indexed.md",
                    "title": "Indexed lookup",
                    "kind": "learning",
                    "date": "2026-05-06",
                    "org": "",
                    "repo": "",
                    "project": "",
                    "ticket": "",
                    "status": "active",
                }
            ],
            results,
        )

    def test_find_many_fallback_loads_records_once(self) -> None:
        records = [
            braingent.Record(
                path=braingent.REPO_ROOT / "topics/topic--sample/records/2026-05-06--learning--alpha.md",
                frontmatter={
                    "title": "Alpha",
                    "record_kind": "learning",
                    "status": "active",
                    "date": "2026-05-06",
                },
                body="alpha body",
            ),
            braingent.Record(
                path=braingent.REPO_ROOT / "topics/topic--sample/records/2026-05-06--learning--beta.md",
                frontmatter={
                    "title": "Beta",
                    "record_kind": "learning",
                    "status": "active",
                    "date": "2026-05-06",
                },
                body="beta body",
            ),
        ]
        with mock.patch.object(mcp_tools.braingent, "load_records", return_value=(records, [])) as load_records:
            results = mcp_tools.find_many([{"q": "alpha"}, {"q": "beta"}], limit=5)

        self.assertEqual(1, load_records.call_count)
        self.assertEqual(["Alpha", "Beta"], [record["title"] for record in results])

    def test_get_returns_record_with_frontmatter(self) -> None:
        record = mcp_tools.get(path=LEARNING_FIXTURE, depth="full")

        self.assertIn("---", record["body"])
        self.assertEqual("learning", record["frontmatter"]["record_kind"])
        self.assertEqual("full", record["depth"])

    def test_get_default_depth_is_summary(self) -> None:
        record = mcp_tools.get(path="tests/fixtures/sample-records/learning.md")

        self.assertEqual("summary", record["depth"])

    def test_get_with_summary_depth_drops_archived_sections(self) -> None:
        record = mcp_tools.get(path="tests/fixtures/sample-records/repo-summary.md", depth="summary")

        self.assertNotIn("## Archived", record["body"])
        self.assertNotIn("deprecated stuff", record["body"])
        self.assertIn("## Summary", record["body"])

    def test_get_rejects_path_outside_repo(self) -> None:
        with self.assertRaises(ValueError):
            mcp_tools.get(path="../../etc/passwd")

    def test_guide_returns_concatenated_read_first(self) -> None:
        output = mcp_tools.guide()

        self.assertIn("Search before planning", output["content"])
        self.assertEqual({"type": "ephemeral"}, output["cache_control"])
        self.assertEqual(["AGENTS.md", "CURRENT_STATE.md"], output["files"])

    def test_guide_response_is_json_serializable_with_cache_control(self) -> None:
        serialized = json.dumps(mcp_tools.guide())

        self.assertIn('"cache_control"', serialized)
        self.assertIn('"ephemeral"', serialized)

    def test_guide_is_byte_stable_across_calls(self) -> None:
        self.assertEqual(mcp_tools.guide()["content"], mcp_tools.guide()["content"])


if __name__ == "__main__":
    unittest.main()

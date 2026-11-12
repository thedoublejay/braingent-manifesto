from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.eval_tokens import count_tokens

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPACT = REPO_ROOT / "indexes" / "records-compact.json"
ROLLUP = REPO_ROOT / "indexes" / "records-rollup.md"


class CompactIndexTests(unittest.TestCase):
    def test_compact_exists_after_reindex(self) -> None:
        self.assertTrue(COMPACT.exists(), "run scripts/reindex.sh before this test")

    def test_compact_field_set_is_minimal(self) -> None:
        payload = json.loads(COMPACT.read_text(encoding="utf-8"))
        allowed = {"path", "title", "kind", "date", "org", "repo", "project", "ticket", "status"}

        self.assertIsInstance(payload, list)
        self.assertGreater(len(payload), 0)
        self.assertTrue(all(set(item) <= allowed for item in payload))

    def test_compact_is_smaller_than_full_records_json(self) -> None:
        compact_tokens = count_tokens(COMPACT.read_text(encoding="utf-8"))
        full_tokens = count_tokens((REPO_ROOT / "indexes" / "records.json").read_text(encoding="utf-8"))

        self.assertLess(compact_tokens, full_tokens * 0.35)

    def test_rollup_exists(self) -> None:
        self.assertTrue(ROLLUP.exists(), "run scripts/reindex.sh before this test")

    def test_rollup_under_8k_tokens(self) -> None:
        self.assertLessEqual(count_tokens(ROLLUP.read_text(encoding="utf-8")), 8_000)

    def test_rollup_groups_by_org(self) -> None:
        text = ROLLUP.read_text(encoding="utf-8")

        self.assertTrue(text.startswith("# Records Rollup"))
        self.assertIn("## `org--", text)


if __name__ == "__main__":
    unittest.main()

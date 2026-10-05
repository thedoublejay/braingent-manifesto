from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from braingent import core


class GeneratedIndexTests(unittest.TestCase):
    def record(self, record_date: str) -> core.Record:
        return core.Record(
            path=core.REPO_ROOT / "records" / f"{record_date}--note--sample.md",
            frontmatter={"title": "Sample", "record_kind": "note", "status": "active", "date": record_date},
            body="Sample record.",
        )

    def test_current_state_is_independent_of_generation_date(self) -> None:
        records = [self.record("2026-10-06")]
        with patch("braingent.core.date") as clock:
            clock.today.return_value = date(2026, 10, 5)
            before_midnight = core.render_current_state(records)
            clock.today.return_value = date(2026, 10, 6)
            after_midnight = core.render_current_state(records)

        self.assertEqual(before_midnight, after_midnight)

    def test_current_state_reports_latest_record_date(self) -> None:
        records = [self.record("2026-10-04"), self.record("2026-10-06")]

        self.assertIn("Latest record date: 2026-10-06", core.render_current_state(records))
        records.append(self.record("2026-10-07"))
        self.assertIn("Latest record date: 2026-10-07", core.render_current_state(records))

    def test_current_state_without_records_has_no_source_date(self) -> None:
        self.assertIn("Latest record date: -", core.render_current_state([]))


if __name__ == "__main__":
    unittest.main()

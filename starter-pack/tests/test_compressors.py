from __future__ import annotations

import unittest

from scripts.compressors import apply_pipeline
from scripts.compressors.dedupe import collapse_repeated_lines
from scripts.compressors.filters import drop_archived_sections
from scripts.compressors.group import collapse_link_lists
from scripts.compressors.truncate import head_per_section


class CompressorTests(unittest.TestCase):
    def test_apply_pipeline_no_strategies_is_identity_for_full_depth(self) -> None:
        text = "## Hello\n\nworld\n"

        self.assertEqual(text, apply_pipeline(text, record_kind="learning", depth="full"))

    def test_apply_pipeline_unknown_depth_raises(self) -> None:
        with self.assertRaises(ValueError):
            apply_pipeline("x", record_kind="learning", depth="bogus")

    def test_apply_pipeline_frontmatter_only_returns_only_frontmatter(self) -> None:
        text = "---\ntitle: hi\n---\n## body\n\nstuff\n"
        output = apply_pipeline(text, record_kind="learning", depth="frontmatter")

        self.assertIn("title: hi", output)
        self.assertNotIn("## body", output)

    def test_drop_archived_sections_removes_explicit_archive_block(self) -> None:
        text = "## Active\n\ncurrent\n\n## Archived\n\nold stuff\n\n## Notes\n\nstill relevant\n"

        output = drop_archived_sections(text, record_kind="task")

        self.assertIn("## Active", output)
        self.assertIn("## Notes", output)
        self.assertNotIn("## Archived", output)
        self.assertNotIn("old stuff", output)

    def test_drop_archived_sections_strips_closed_task_playbook(self) -> None:
        text = "---\nstatus: closed\n---\n## Playbook\n\nlong steps\n\n## Outcome\n\nshipped\n"

        output = drop_archived_sections(text, record_kind="task")

        self.assertNotIn("## Playbook", output)
        self.assertNotIn("long steps", output)
        self.assertIn("## Outcome", output)

    def test_collapse_link_lists_groups_runs_of_links(self) -> None:
        text = (
            "- [a](orgs/x/records/a.md)\n"
            "- [b](orgs/x/records/b.md)\n"
            "- [c](orgs/x/records/c.md)\n"
            "- [d](orgs/x/records/d.md)\n\n"
            "prose\n"
        )

        output = collapse_link_lists(text)

        self.assertIn("+3 more links collapsed", output)
        self.assertIn("[a]", output)
        self.assertIn("prose", output)

    def test_collapse_link_lists_leaves_short_lists_alone(self) -> None:
        text = "- [a](x.md)\n- [b](y.md)\n"

        self.assertEqual(text, collapse_link_lists(text))

    def test_collapse_repeated_lines_dedupes_consecutive_duplicates(self) -> None:
        output = collapse_repeated_lines("warn: foo\nwarn: foo\nwarn: foo\nok\n")

        self.assertIn("warn: foo", output)
        self.assertIn("(repeated 3x)", output)
        self.assertEqual(1, output.count("warn: foo"))

    def test_collapse_repeated_lines_leaves_unique_lines_alone(self) -> None:
        text = "a\nb\nc\n"

        self.assertEqual(text, collapse_repeated_lines(text))

    def test_head_per_section_truncates_long_sections(self) -> None:
        text = "## Big\n" + "".join(f"line {index}\n" for index in range(50))

        output = head_per_section(text, max_lines_per_section=10)

        self.assertIn("line 0", output)
        self.assertIn("line 9", output)
        self.assertNotIn("line 49", output)
        self.assertIn("_... (40 more lines truncated)_", output)

    def test_head_per_section_leaves_short_sections_alone(self) -> None:
        text = "## Small\n\nline a\nline b\n"

        self.assertEqual(text, head_per_section(text, max_lines_per_section=10))


if __name__ == "__main__":
    unittest.main()

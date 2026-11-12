from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from braingent import core

PACK_ROOT = Path(__file__).resolve().parents[1]


def record_text(title: str, extra: str = "") -> str:
    return (
        f"---\ntitle: {title}\nrecord_kind: note\nstatus: active\ndate: 2026-10-07\ntimezone: UTC\n"
        f"organization: org--acme\nproject: null\n{extra}---\n\n# {title}\n\nBody.\n"
    )


class ValidationBaselineTests(unittest.TestCase):
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

    def write(self, name: str, extra: str) -> None:
        (self.records / name).write_text(record_text(name, extra), encoding="utf-8")

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = core.main(["--root", str(self.root), *argv])
        return code, out.getvalue(), err.getvalue()

    def test_code_ignores_the_values_in_a_message(self) -> None:
        first = core.ValidationIssue(self.root / "a.md", "unknown frontmatter field `mystery`.", severity="warning")
        second = core.ValidationIssue(self.root / "b.md", "unknown frontmatter field `other_one`.", severity="warning")
        self.assertEqual(first.code, second.code)
        self.assertEqual(first.code, "unknown-frontmatter-field")
        self.assertNotEqual(first.code, core.ValidationIssue(self.root / "a.md", "missing required field `date` for task").code)

    def test_without_a_baseline_every_warning_is_listed(self) -> None:
        self.write("2026-10-07--note--a.md", "mystery: 1\n")
        code, _, err = self.run_cli("validate")
        self.assertEqual(code, 0)
        self.assertIn("unknown frontmatter field `mystery`", err)
        self.assertNotIn("new since the baseline", err)

    def test_baseline_summarises_old_warnings_and_lists_only_new_ones(self) -> None:
        self.write("2026-10-07--note--a.md", "mystery: 1\n")
        code, out, _ = self.run_cli("validate", "--update-baseline")
        self.assertEqual(code, 0)
        self.assertIn("with 1 warnings", out)
        baseline = json.loads((self.root / ".braingent" / "validation-baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(baseline["warnings"], {"unknown-frontmatter-field": {"orgs/org--acme/records/2026-10-07--note--a.md": 1}})

        _, _, err = self.run_cli("validate")
        self.assertIn("warnings: 1 (0 new since the baseline)", err)
        self.assertIn("- unknown-frontmatter-field: 1", err)
        self.assertNotIn("mystery", err)

        self.write("2026-10-07--note--a.md", "mystery: 1\nanother: 2\n")
        self.write("2026-10-07--note--b.md", "mystery: 1\n")
        _, _, err = self.run_cli("validate")
        self.assertIn("warnings: 3 (2 new since the baseline)", err)
        self.assertIn("- unknown-frontmatter-field: 3 (+2 new)", err)
        self.assertEqual(err.count("unknown frontmatter field `"), 2)
        self.assertIn("2026-10-07--note--b.md", err)

    def test_verbose_and_scoped_runs(self) -> None:
        self.write("2026-10-07--note--a.md", "mystery: 1\n")
        self.run_cli("validate", "--update-baseline")
        _, _, err = self.run_cli("validate", "--verbose")
        self.assertIn("unknown frontmatter field `mystery`", err)
        _, _, err = self.run_cli("validate", str(self.records / "2026-10-07--note--a.md"))
        self.assertIn("(0 new since the baseline)", err)
        with self.assertRaises(SystemExit):
            self.run_cli("validate", "--update-baseline", str(self.records / "2026-10-07--note--a.md"))

    def test_errors_still_fail_with_a_baseline(self) -> None:
        self.write("2026-10-07--note--a.md", "mystery: 1\n")
        self.run_cli("validate", "--update-baseline")
        (self.records / "2026-10-07--note--broken.md").write_text("---\ntitle: x\n", encoding="utf-8")
        code, _, _ = self.run_cli("validate")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


class PackageCliTests(unittest.TestCase):
    def python_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC_DIR)
        return env

    def test_module_help_works_outside_memory_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [sys.executable, "-m", "braingent", "--help"],
                cwd=tmp_dir,
                env=self.python_env(),
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertIn("Braingent metadata helper", result.stdout)

    def test_root_option_runs_command_from_outside_memory_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "braingent",
                    "--root",
                    str(REPO_ROOT),
                    "find",
                    "repo=example--owner--repo",
                    "--limit",
                    "1",
                ],
                cwd=tmp_dir,
                env=self.python_env(),
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertIn("repo--example--owner--repo", result.stdout)

    def test_env_root_runs_command_from_outside_memory_repo(self) -> None:
        env = self.python_env()
        env["BRAINGENT_ROOT"] = str(REPO_ROOT)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [sys.executable, "-m", "braingent", "find", "repo=example--owner--repo", "--limit", "1"],
                cwd=tmp_dir,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

        self.assertIn("repo--example--owner--repo", result.stdout)

    def test_init_creates_memory_repo_from_package_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "memory"
            result = subprocess.run(
                [sys.executable, "-m", "braingent", "init", str(target)],
                cwd=tmp_dir,
                env=self.python_env(),
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("Initialized Braingent memory repo", result.stdout)
            self.assertTrue((target / "preferences" / "taxonomy.yml").exists())
            self.assertTrue((target / "templates" / "task-record.md").exists())
            self.assertTrue((target / "workflows" / "retrieve-context.md").exists())
            self.assertTrue((target / "indexes" / "records.json").exists())
            self.assertTrue((target / ".braingent-template-manifest.json").exists())

    def test_update_reports_template_state_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "memory"
            subprocess.run(
                [sys.executable, "-m", "braingent", "init", str(target)],
                cwd=tmp_dir,
                env=self.python_env(),
                text=True,
                capture_output=True,
                check=True,
            )

            result = subprocess.run(
                [sys.executable, "-m", "braingent", "update", str(target), "--dry-run"],
                cwd=tmp_dir,
                env=self.python_env(),
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("unchanged:", result.stdout)
            self.assertIn("Dry run only", result.stdout)

    def test_qa_generate_runs_from_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ticket = Path(tmp_dir) / "ticket.md"
            ticket.write_text(
                "# SYN-001 Filter approvals\n\n"
                "## Acceptance Criteria\n\n"
                "- Reviewers see only approvals assigned to themselves by default.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "braingent",
                    "qa",
                    "generate",
                    str(ticket),
                    "--ticket-key",
                    "SYN-001",
                    "--no-diff",
                    "--design-context",
                    "--print",
                ],
                cwd=tmp_dir,
                env=self.python_env(),
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn("# Test Plan: SYN-001", result.stdout)
            self.assertIn("TC-001", result.stdout)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from braingent import config as bgconfig
from braingent import core


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class LoadConfigTests(unittest.TestCase):
    def test_defaults_when_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            cfg = bgconfig.load_config(root, home=home)
            # No config files: built-in safety patterns and documented defaults apply.
            self.assertEqual(cfg.forbid_patterns, bgconfig.BUILTIN_FORBID_PATTERNS)
            self.assertEqual(cfg.forbid_paths, ())
            self.assertEqual(cfg.doctor_stale_days, 180)
            self.assertEqual(cfg.recall_limit, 8)
            self.assertEqual(cfg.recall_stale_days, 180)
            self.assertEqual(cfg.task_id_prefix, "BGT")
            self.assertEqual(cfg.task_id_pad, 4)
            self.assertEqual(cfg.issues, ())

    def test_repo_overrides_user_for_scalars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            _write(home, ".braingent/config.toml", "[doctor]\nstale_days = 30\n")
            _write(root, ".braingent/config.toml", "[doctor]\nstale_days = 90\n")
            cfg = bgconfig.load_config(root, home=home)
            self.assertEqual(cfg.doctor_stale_days, 90)  # repo-local wins over user-level

    def test_forbid_patterns_are_additive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            _write(home, ".braingent/config.toml", '[safety]\nforbid_patterns = ["USERPAT-[0-9]+"]\n')
            _write(root, ".braingent/config.toml", '[safety]\nforbid_patterns = ["REPOPAT-[0-9]+"]\n')
            cfg = bgconfig.load_config(root, home=home)
            builtins = bgconfig.BUILTIN_FORBID_PATTERNS
            self.assertEqual(cfg.forbid_patterns[: len(builtins)], builtins)  # built-ins kept, never replaced
            self.assertIn("USERPAT-[0-9]+", cfg.forbid_patterns)
            self.assertIn("REPOPAT-[0-9]+", cfg.forbid_patterns)

    def test_invalid_regex_dropped_and_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            _write(root, ".braingent/config.toml", '[safety]\nforbid_patterns = ["(unclosed"]\n')
            cfg = bgconfig.load_config(root, home=home)
            self.assertNotIn("(unclosed", cfg.forbid_patterns)
            self.assertTrue(any("invalid forbid_patterns" in issue for issue in cfg.issues))

    def test_bad_scalar_type_falls_back_and_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            _write(root, ".braingent/config.toml", "[doctor]\nstale_days = -5\n")
            cfg = bgconfig.load_config(root, home=home)
            self.assertEqual(cfg.doctor_stale_days, 180)  # invalid value ignored, default kept
            self.assertTrue(any("stale_days" in issue for issue in cfg.issues))

    def test_malformed_toml_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            _write(root, ".braingent/config.toml", "this is = not = valid ==\n")
            cfg = bgconfig.load_config(root, home=home)
            self.assertTrue(any("could not parse" in issue for issue in cfg.issues))

    def test_task_id_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            home = Path(tmp) / "home"
            _write(root, ".braingent/config.toml", '[task_ids]\nprefix = "ENG"\npad = 5\n')
            cfg = bgconfig.load_config(root, home=home)
            self.assertEqual(cfg.task_id_prefix, "ENG")
            self.assertEqual(cfg.task_id_pad, 5)


class DoctorSafetyTests(unittest.TestCase):
    def test_builtin_pattern_catches_aws_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "rec.md").write_text("access key AKIAIOSFODNN7EXAMPLE noted\n", encoding="utf-8")
            saved_root, saved_cfg = core.REPO_ROOT, core.CONFIG
            try:
                core.REPO_ROOT = root
                core.CONFIG = bgconfig.DEFAULT_CONFIG
                findings = core.forbidden_content_findings()
            finally:
                core.REPO_ROOT, core.CONFIG = saved_root, saved_cfg
            self.assertTrue(findings)  # built-in AKIA pattern fires with no config

    def test_configured_pattern_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "rec.md").write_text("internal ref ACME-SECRET-42 here\n", encoding="utf-8")
            saved_root, saved_cfg = core.REPO_ROOT, core.CONFIG
            try:
                core.REPO_ROOT = root
                core.CONFIG = bgconfig.BraingentConfig(forbid_patterns=("ACME-SECRET-[0-9]+",))
                findings = core.forbidden_content_findings()
            finally:
                core.REPO_ROOT, core.CONFIG = saved_root, saved_cfg
            self.assertTrue(findings)  # custom config pattern fires


class TaskIdConfigTests(unittest.TestCase):
    def test_next_agent_task_id_uses_prefix_and_pad(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks"
            tasks.mkdir()
            saved_tasks, saved_cfg = core.TASKS_DIR, core.CONFIG
            try:
                core.TASKS_DIR = tasks
                core.CONFIG = bgconfig.BraingentConfig(task_id_prefix="ENG", task_id_pad=5)
                self.assertEqual(core.next_agent_task_id(), "ENG-00001")
            finally:
                core.TASKS_DIR, core.CONFIG = saved_tasks, saved_cfg

    def test_validation_regex_follows_config(self) -> None:
        saved_cfg = core.CONFIG
        try:
            core.CONFIG = bgconfig.BraingentConfig(task_id_prefix="ENG")
            regex = core.agent_task_id_regex()
            self.assertTrue(regex.match("ENG-0001"))
            self.assertFalse(regex.match("BGT-0001"))
        finally:
            core.CONFIG = saved_cfg


if __name__ == "__main__":
    unittest.main()

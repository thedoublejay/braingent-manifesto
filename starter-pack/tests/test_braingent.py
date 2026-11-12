from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_TOKENS_PATH = REPO_ROOT / "scripts" / "eval_tokens.py"

sys.path.insert(0, str(REPO_ROOT / "src"))

from braingent import core as braingent

eval_spec = importlib.util.spec_from_file_location("eval_tokens", EVAL_TOKENS_PATH)
assert eval_spec is not None and eval_spec.loader is not None
eval_tokens = importlib.util.module_from_spec(eval_spec)
sys.modules[eval_spec.name] = eval_tokens
eval_spec.loader.exec_module(eval_tokens)


class BraingentToolTests(unittest.TestCase):
    def record(self, name: str, frontmatter: dict[str, object]) -> braingent.Record:
        return braingent.Record(path=REPO_ROOT / "tests" / "fixtures" / name, frontmatter=frontmatter, body="")

    def agent_task(self, task_id: str = "BGT-9999", **overrides: object) -> braingent.Record:
        frontmatter: dict[str, object] = {
            "id": task_id,
            "title": "Agent task sample",
            "record_kind": "agent-task",
            "status": "todo",
            "status_category": "active",
            "resolution": None,
            "type": "task",
            "priority": "medium",
            "assignee": "agent--codex-cli",
            "reviewer": "agent--claude-code",
            "observers": [],
            "claimed_by": None,
            "claimed_at": None,
            "created": "2026-04-30",
            "updated": "2026-04-30",
            "date": "2026-04-30",
            "timezone": "UTC",
            "organization": "org--example",
            "project": "project--example--memory",
            "repositories": ["repo--example--owner--repo"],
            "ticket": None,
            "prs": [],
            "commits": [],
            "ai_tools": ["Codex"],
            "people": [],
            "topics": ["topic--ai-memory"],
            "tools": [],
            "parent": None,
            "depends_on": [],
            "duplicate_of": None,
            "closed": None,
            "visibility": "private",
        }
        frontmatter.update(overrides)
        body = """## Description

Sample.

## Acceptance Criteria

- [ ] Works.

## Plan

1. Test.

## Dependencies

- Depends on: none

## Activity

- 2026-04-30T10:00:00+08:00 | agent--codex-cli | role:assignee | event:created |
  Created.

## Linked Evidence

- Commands:
"""
        return braingent.Record(path=REPO_ROOT / "tasks" / "active" / f"{task_id}--sample.md", frontmatter=frontmatter, body=body)

    def test_project_shorthand_resolves_unique_project_suffix(self) -> None:
        self.assertEqual(
            ("project", "project--example--memory"),
            braingent.normalize_filter("project", "memory"),
        )
        self.assertEqual(
            ("project", "project--example--memory"),
            braingent.normalize_filter("project", "example--memory"),
        )

    def test_repo_shorthand_resolves_unique_repository_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.object(braingent, "REPO_ROOT", Path(tmp)):
            (Path(tmp) / "repositories" / "repo--github--owner-a--sample").mkdir(parents=True)

            self.assertEqual(
                ("repositories", "repo--github--owner-a--sample"),
                braingent.normalize_filter("repo", "sample"),
            )

    def test_repo_shorthand_does_not_resolve_ambiguous_repository_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.object(braingent, "REPO_ROOT", Path(tmp)):
            for owner in ("owner-a", "owner-b"):
                (Path(tmp) / "repositories" / f"repo--github--{owner}--sample").mkdir(parents=True)

            self.assertEqual(
                ("repositories", "repo--sample"),
                braingent.normalize_filter("repo", "sample"),
            )

    def test_recall_sort_keeps_priority_then_newer_records(self) -> None:
        old = self.record(
            "old.md",
            {"title": "old", "record_kind": "task", "status": "completed", "date": "2026-01-01"},
        )
        new = self.record(
            "new.md",
            {"title": "new", "record_kind": "task", "status": "completed", "date": "2026-04-01"},
        )

        self.assertEqual([new, old], sorted([old, new], key=braingent.recall_sort_key))

    def test_token_counter_returns_stable_counts(self) -> None:
        self.assertEqual(0, eval_tokens.count_tokens(""))
        self.assertGreater(eval_tokens.count_tokens("alpha beta gamma"), 0)

    def test_measure_session_sums_file_costs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="braingent-token-measure.") as tmp:
            first = Path(tmp) / "first.md"
            second = Path(tmp) / "second.md"
            first.write_text("alpha beta", encoding="utf-8")
            second.write_text("gamma", encoding="utf-8")

            result = eval_tokens.measure_session([first, second])

        self.assertEqual(2, len(result["files"]))
        self.assertEqual(len(b"alpha betagamma"), result["total_bytes"])
        self.assertEqual(sum(item["tokens"] for item in result["files"]), result["total_tokens"])

    def test_compact_record_json_uses_nine_field_projection(self) -> None:
        record = self.record(
            "compact.md",
            {
                "title": "Compact sample",
                "summary": "This should not appear in compact output.",
                "record_kind": "task",
                "status": "completed",
                "date": "2026-05-05",
                "organization": "org--example",
                "project": "project--example--memory",
                "repositories": ["repo--example--owner--repo"],
                "ticket": "BGT-1000",
                "topics": ["topic--ai-memory"],
            },
        )

        compact = braingent.compact_record_to_json(record)

        self.assertEqual(
            ["path", "title", "kind", "date", "org", "repo", "project", "ticket", "status"],
            list(compact.keys()),
        )
        self.assertEqual("Compact sample", compact["title"])
        self.assertEqual("task", compact["kind"])
        self.assertEqual("org--example", compact["org"])
        self.assertNotIn("summary", compact)
        self.assertNotIn("frontmatter", compact)

    def test_records_compact_json_is_minified_projection(self) -> None:
        record = self.record(
            "compact-json.md",
            {
                "title": "Compact JSON sample",
                "record_kind": "task",
                "status": "completed",
                "date": "2026-05-05",
            },
        )

        text = braingent.records_compact_json([record])
        payload = json.loads(text)

        self.assertEqual("\n", text[-1])
        self.assertNotIn("\n  ", text)
        self.assertEqual(1, len(payload))
        self.assertEqual(
            ["path", "title", "kind", "date", "org", "repo", "project", "ticket", "status"],
            list(payload[0].keys()),
        )

    def test_records_rollup_caps_each_organization(self) -> None:
        records = [
            self.record(
                f"rollup-{index:02d}.md",
                {
                    "title": f"Rollup sample {index:02d}",
                    "record_kind": "task",
                    "status": "completed",
                    "date": f"2026-05-{(index % 28) + 1:02d}",
                    "organization": "org--example",
                },
            )
            for index in range(35)
        ]

        text = braingent.render_records_rollup(records)
        visible_records = sum(1 for line in text.splitlines() if line.startswith("- `task`"))

        self.assertEqual(braingent.RECORDS_ROLLUP_PER_ORG_LIMIT, visible_records)
        omitted = 35 - braingent.RECORDS_ROLLUP_PER_ORG_LIMIT
        self.assertIn(f"- {omitted} older records omitted from this compact rollup.", text)

    def test_stale_reason_detects_old_profiles(self) -> None:
        profile = self.record(
            "profile.md",
            {"title": "profile", "record_kind": "profile", "status": "active", "last_reviewed": "2025-01-01"},
        )

        self.assertEqual(
            "profile last_reviewed is 480 days old",
            braingent.stale_reason(profile, stale_days=180, today=date(2026, 4, 26)),
        )

    def test_agent_task_validation_accepts_valid_task(self) -> None:
        task = self.agent_task()

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertEqual([], [issue.format() for issue in issues])

    def test_agent_task_validation_rejects_closed_without_resolution(self) -> None:
        task = self.agent_task(status="closed", status_category="closed", closed="2026-04-30")

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertIn("closed agent-task requires resolution", "\n".join(issue.message for issue in issues))

    def test_agent_task_validation_rejects_invalid_status(self) -> None:
        task = self.agent_task(status="waiting")

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertIn("invalid status `waiting` for agent-task", "\n".join(issue.message for issue in issues))

    def test_agent_task_validation_rejects_wrong_status_category(self) -> None:
        task = self.agent_task(status="blocked", status_category="triage")

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertIn("`status_category` must be `active`", "\n".join(issue.message for issue in issues))

    def test_agent_task_validation_rejects_unknown_agent(self) -> None:
        task = self.agent_task(assignee="agent--unknown")

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertIn("`assignee` has unknown agent ID `agent--unknown`", "\n".join(issue.message for issue in issues))

    def test_agent_task_validation_rejects_forbidden_labels(self) -> None:
        task = self.agent_task(labels=["extra"])

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertIn("unknown frontmatter field `labels`", "\n".join(issue.message for issue in issues))

    def test_agent_task_validation_rejects_malformed_activity_timestamp(self) -> None:
        task = self.agent_task()
        task = braingent.Record(
            path=task.path,
            frontmatter=task.frontmatter,
            body=task.body.replace("2026-04-30T10:00:00+08:00", "2026-04-30 10:00"),
        )

        issues = braingent.validate_record(task, braingent.load_taxonomy())

        self.assertIn("malformed activity entry", "\n".join(issue.message for issue in issues))

    def test_agent_task_collection_rejects_unknown_dependency(self) -> None:
        task = self.agent_task(depends_on=["BGT-0000"])

        issues = braingent.validate_agent_task_collection([task])

        self.assertIn("`depends_on` references unknown agent-task `BGT-0000`", "\n".join(issue.message for issue in issues))

    def test_agent_task_collection_rejects_duplicate_id(self) -> None:
        first = self.agent_task()
        second = self.agent_task()

        issues = braingent.validate_agent_task_collection([first, second])

        self.assertIn("duplicate agent-task id `BGT-9999`", "\n".join(issue.message for issue in issues))

    def test_agent_task_collection_rejects_parent_recursion(self) -> None:
        parent = self.agent_task("BGT-9001", parent="BGT-9000")
        child = self.agent_task("BGT-9002", parent="BGT-9001")
        root = self.agent_task("BGT-9000")

        issues = braingent.validate_agent_task_collection([root, parent, child])

        self.assertIn("parent chains deeper than one level", "\n".join(issue.message for issue in issues))

    def test_new_record_outputs_validate_for_all_record_kinds(self) -> None:
        cases = [
            ("task", "project--example--memory", "Task sample"),
            ("review", "repo--example--owner--repo", "Review sample"),
            ("decision", "project--example--memory", "Decision sample"),
            ("learning", "topic--ai-memory", "Learning sample"),
            ("interaction", "org--example", "Interaction sample"),
            ("version", "tool--codex", "Version sample"),
            ("note", "project--example--memory", "Note sample"),
            ("summary", "project--example--memory", "Summary sample"),
            ("profile", "repo--example--owner--repo", "Profile sample"),
            ("ticket-stub", "ticket--jira--example-123", "Ticket sample"),
        ]

        with tempfile.TemporaryDirectory(prefix="braingent-new-record.") as tmp:
            for kind, entity, title in cases:
                with self.subTest(kind=kind):
                    result = subprocess.run(
                        [str(REPO_ROOT / "scripts" / "new-record.sh"), kind, entity, title, tmp],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    path = Path(result.stdout.strip())
                    issues = braingent.issue_errors(braingent.validate([path]))
                    self.assertEqual([], [issue.format() for issue in issues])

                    text = path.read_text(encoding="utf-8")
                    self.assertIn(f'title: "{title}"', text)
                    if kind not in {"profile", "ticket-stub"}:
                        self.assertRegex(text, r"(?m)^timezone: [A-Za-z_]+(?:/[A-Za-z_]+)*$")


if __name__ == "__main__":
    unittest.main()

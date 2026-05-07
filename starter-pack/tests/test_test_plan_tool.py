from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "tools" / "tool--test-plan" / "test_plan.py"

spec = importlib.util.spec_from_file_location("test_plan_tool", TOOL_PATH)
assert spec is not None
test_plan_tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = test_plan_tool
assert spec.loader is not None
spec.loader.exec_module(test_plan_tool)


class TestPlanToolTests(unittest.TestCase):
    def write_ticket(self, text: str) -> Path:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as tmp:
            tmp.write(text)
            return Path(tmp.name)

    def test_run_returns_exit_code_for_input_error(self) -> None:
        path = self.write_ticket("# Bug\n\nFix this.")
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = test_plan_tool.run([str(path), "--ticket-key", "SYN-000", "--no-diff"])

        self.assertEqual(2, exit_code)
        self.assertIn("error: Refusing to generate", stderr.getvalue())

    def test_read_source_accepts_inline_text_with_pathish_tokens(self) -> None:
        text = r"Verify /healthz, C:\temp\notes, and release 1.2.3 remain visible in the UI."

        source = test_plan_tool.read_source(text, "Ticket")

        self.assertEqual("inline", source.path)
        self.assertEqual(text, source.text)

    def test_read_source_rejects_missing_clear_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = Path(tmp_dir) / "missing-ticket.md"

            with self.assertRaises(test_plan_tool.InputError):
                test_plan_tool.read_source(str(missing), "Ticket")

    def test_refuses_unclear_ticket_without_ac(self) -> None:
        path = self.write_ticket("# Bug\n\nFix this.")
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(path), "--ticket-key", "SYN-000", "--no-diff"])

        with self.assertRaises(test_plan_tool.InputError):
            test_plan_tool.build_model(args)

    def test_no_diff_generates_ac_only_markdown(self) -> None:
        path = self.write_ticket(
            """# SYN-001 Filter approvals

## Acceptance Criteria

- Reviewers see only approvals assigned to themselves by default.
- Leads can switch to All reviewers and see approvals across reviewers.
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(path), "--ticket-key", "SYN-001", "--no-diff", "--design-context"])

        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)
        rendered = test_plan_tool.render_plan(model, scenarios)

        self.assertEqual(2, len(scenarios))
        self.assertTrue(all(scenario.classification == "AC-only" for scenario in scenarios))
        self.assertIn("## AC Coverage Matrix", rendered)
        self.assertIn("TC-001", rendered)
        self.assertIn("Gather Step evidence commands: 0", rendered)
        self.assertIn("Implementation State: pre-implementation", rendered)
        self.assertIn("Diff Mode: no-diff / product-only evidence", rendered)
        self.assertIn("## Spec Matrix", rendered)
        self.assertIn("## AC Coverage Heatmap", rendered)
        self.assertIn("## Uncovered ACs", rendered)
        self.assertIn("## Reverse Traceability Index", rendered)

    def test_emit_formats_share_scenario_model(self) -> None:
        path = self.write_ticket(
            """# SYN-011 Export approvals

## Acceptance Criteria

- Users can export filtered approvals.
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(path), "--ticket-key", "SYN-011", "--no-diff", "--design-context"])
        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)

        xray = json.loads(test_plan_tool.render_output(model, scenarios, "xray-json"))
        testrail = test_plan_tool.render_output(model, scenarios, "testrail-csv")
        gherkin = test_plan_tool.render_output(model, scenarios, "gherkin")

        self.assertEqual("braingent-xray-json.v1", xray["schema"])
        self.assertEqual("SYN-011", xray["ticketKey"])
        self.assertEqual(1, len(xray["tests"]))
        self.assertIn("Title", testrail)
        self.assertIn("References", testrail)
        self.assertIn("Feature: SYN-011 QA test plan", gherkin)
        self.assertIn("@SPEC_001", gherkin)

    def test_output_path_uses_emit_format_extension(self) -> None:
        path = self.write_ticket(
            """# SYN-012

## Acceptance Criteria

- Users can save profile preferences.
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(path), "--ticket-key", "SYN-012", "--no-diff", "--emit-format", "gherkin"])
        model = test_plan_tool.build_model(args)

        self.assertEqual("syn-012--test-plan.feature", test_plan_tool.output_path_for(args, model).name)

    def test_budget_tokens_is_lenient_default_and_byte_override(self) -> None:
        parser = test_plan_tool.build_arg_parser()
        default_args = parser.parse_args(["# Ticket\n\n## Acceptance Criteria\n\n- Users can save preferences."])
        override_args = parser.parse_args(
            ["# Ticket\n\n## Acceptance Criteria\n\n- Users can save preferences.", "--budget-tokens", "200000"]
        )
        byte_args = parser.parse_args(
            [
                "# Ticket\n\n## Acceptance Criteria\n\n- Users can save preferences.",
                "--budget-tokens",
                "200000",
                "--evidence-budget-bytes",
                "1234",
            ]
        )

        self.assertEqual(160_000, default_args.budget_tokens)
        self.assertEqual(640_000, test_plan_tool.evidence_budget_bytes(default_args))
        self.assertEqual(800_000, test_plan_tool.evidence_budget_bytes(override_args))
        self.assertEqual(1234, test_plan_tool.evidence_budget_bytes(byte_args))

    def test_precheck_surfaces_uncovered_requirements(self) -> None:
        ac = test_plan_tool.AcceptanceCriterion("AC-1", "Users can archive an item.", "Ticket")
        model = test_plan_tool.GenerationInput(
            ticket_key="SYN-013",
            ticket=test_plan_tool.SourceDoc("Ticket", "inline", "# SYN-013"),
            sources=[],
            acceptance_criteria=[ac],
            implementation_state="pre-implementation",
            no_diff=True,
            base=None,
            head=None,
            memory_records=[],
            gather_evidence=[],
            evidence_pack=None,
            assumptions=[],
            gaps=[],
        )

        gaps = test_plan_tool.deterministic_precheck_gaps(model, [])

        self.assertIn("Precheck: AC-1 has no covering test case or explicit gap.", gaps)

    def test_acceptance_criteria_table_generates_cases(self) -> None:
        path = self.write_ticket(
            """# SYN-008 Discussions tab

## Acceptance Criteria

| # | Scenario | Expected behavior |
|---|---|---|
| 1 | Composer is empty | Send button is disabled. |
| 2 | User sends text | Message is posted with author/date and composer clears. |
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(path), "--ticket-key", "SYN-008", "--no-diff", "--design-context"])

        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)

        self.assertEqual(2, len(scenarios))
        self.assertEqual(
            "Composer is empty -> Send button is disabled.",
            model.acceptance_criteria[0].text,
        )
        self.assertTrue(all(scenario.classification == "AC-only" for scenario in scenarios))

    def test_given_when_then_table_preferred_over_requirements_bullets(self) -> None:
        path = self.write_ticket(
            """# SYN-014 Discussions tab

## Requirements

- Empty state
- Composer
- Message display

## Acceptance Criteria

| Given | When | Then |
| --- | --- | --- |
| User is on the Discussions tab with no messages | Tab loads | Empty state displays and composer is auto-focused. |
| User is on the Discussions tab with an empty composer | User views the Send button | Send button is disabled. |
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(path), "--ticket-key", "SYN-014", "--no-diff", "--design-context"])

        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)

        self.assertEqual(2, len(model.acceptance_criteria))
        self.assertEqual(2, len(scenarios))
        self.assertEqual(
            "Given User is on the Discussions tab with no messages; when Tab loads; then Empty state displays and composer is auto-focused.",
            model.acceptance_criteria[0].text,
        )
        self.assertNotIn("Empty state", [criterion.text for criterion in model.acceptance_criteria])

    def test_ac_matrix_matches_exact_source_identifiers(self) -> None:
        ac_1 = test_plan_tool.AcceptanceCriterion("AC-1", "First behavior", "Ticket")
        ac_10 = test_plan_tool.AcceptanceCriterion("AC-10", "Tenth behavior", "Ticket")
        scenario = test_plan_tool.Scenario(
            ident="TC-010",
            title="Tenth behavior",
            classification="AC-only",
            case_type="Manual UI",
            priority="Medium",
            sources=["AC-10: Tenth behavior (Ticket)"],
            preconditions=[],
            steps=[],
            expected_result="Tenth behavior works.",
            data_variations=[],
            automation_candidate="Maybe",
        )
        model = test_plan_tool.GenerationInput(
            ticket_key="SYN-009",
            ticket=test_plan_tool.SourceDoc("Ticket", "inline", "# SYN-009"),
            sources=[],
            acceptance_criteria=[ac_1, ac_10],
            implementation_state="pre-implementation",
            no_diff=True,
            base=None,
            head=None,
            memory_records=[],
            gather_evidence=[],
            evidence_pack=None,
            assumptions=[],
            gaps=[],
        )

        matrix = test_plan_tool.render_ac_matrix(model, [scenario])

        self.assertIn("| AC-1 | First behavior | - | gap |", matrix)
        self.assertIn("| AC-10 | Tenth behavior | TC-010 | covered |", matrix)

    def test_allow_missing_ac_generates_requirement_case(self) -> None:
        path = self.write_ticket(
            """# Export approvals

Reviewers can export the filtered approvals table so offline audit checks use the same records shown in the browser.
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args(
            [str(path), "--ticket-key", "SYN-003", "--allow-missing-ac", "--no-diff", "--design-context"]
        )

        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)

        self.assertEqual(1, len(scenarios))
        self.assertTrue(scenarios[0].sources[0].startswith("REQ-1:"))
        self.assertEqual("AC-only", scenarios[0].classification)

    def test_supporting_source_without_requirement_becomes_gap(self) -> None:
        ticket = self.write_ticket(
            """# SYN-004

## Acceptance Criteria

- Users can filter approvals by reviewer.
"""
        )
        source = self.write_ticket("Meeting note: follow up with QA after release.")
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(ticket), "--ticket-key", "SYN-004", "--source", str(source), "--no-diff"])

        model = test_plan_tool.build_model(args)

        self.assertTrue(any("Source 1 did not yield explicit requirement rows" in gap for gap in model.gaps))

    def test_compact_memory_search_returns_warning_not_fake_record(self) -> None:
        ticket = self.write_ticket(
            """# SYN-005

## Acceptance Criteria

- Users can filter approvals by reviewer.
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(ticket), "--no-diff"])
        args.ticket_key = None
        args.memory_query = ["q=approval"]

        from scripts import mcp_tools

        with mock.patch.object(mcp_tools, "find_many", side_effect=RuntimeError("index drift")):
            result = test_plan_tool.compact_memory_search(args, "")

        self.assertEqual([], result.records)
        self.assertEqual(["Braingent memory lookup degraded for `q=approval`: index drift."], result.warnings)

    def test_memory_lookup_warning_surfaces_as_gap_not_mem_row(self) -> None:
        ticket = self.write_ticket(
            """# SYN-006

## Acceptance Criteria

- Users can filter approvals by reviewer.
"""
        )
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(ticket), "--ticket-key", "SYN-006", "--no-diff", "--memory-query", "q=approval"])

        from scripts import mcp_tools

        with mock.patch.object(mcp_tools, "find_many", side_effect=RuntimeError("index drift")):
            model = test_plan_tool.build_model(args)

        rendered = test_plan_tool.render_plan(model, test_plan_tool.build_scenarios(model))

        self.assertEqual([], model.memory_records)
        self.assertTrue(any("Braingent memory lookup degraded" in gap for gap in model.gaps))
        self.assertNotIn("memory-query-error", rendered)
        self.assertNotIn("| MEM-1 |", rendered)

    def test_matching_evidence_marks_ac_as_both_and_keeps_unmatched_code_only(self) -> None:
        ac = test_plan_tool.AcceptanceCriterion(
            ident="AC-1",
            text="Approval filter preserves pagination state",
            source="Ticket",
        )
        model = test_plan_tool.GenerationInput(
            ticket_key="SYN-002",
            ticket=test_plan_tool.SourceDoc("Ticket", "inline", "# SYN-002"),
            sources=[],
            acceptance_criteria=[ac],
            implementation_state="post-implementation",
            no_diff=False,
            base="main",
            head="HEAD",
            memory_records=[],
            gather_evidence=[
                test_plan_tool.EvidenceItem(
                    label="pack",
                    command="gather-step pack ApprovalFilter",
                    text="ApprovalFilter preserves pagination state across sort changes.",
                    ok=True,
                ),
                test_plan_tool.EvidenceItem(
                    label="impact",
                    command="gather-step impact DownstreamExport",
                    text="DownstreamExport reads a changed approval export contract.",
                    ok=True,
                )
            ],
            evidence_pack=None,
            assumptions=[],
            gaps=[],
        )

        scenarios = test_plan_tool.build_scenarios(model)

        self.assertEqual("Both", scenarios[0].classification)
        self.assertEqual("Code-only", scenarios[1].classification)

    def test_evidence_pack_generates_code_only_case_and_surfaces_truncation(self) -> None:
        ticket = self.write_ticket(
            """# SYN-007

## Acceptance Criteria

- Users can update their profile display name.
"""
        )
        pack = {
            "manifest_summary": {
                "evidence_pack_version": "0.1-draft",
                "generated_at": "2026-05-06T00:00:00Z",
                "base_ref": "main",
                "head_ref": "HEAD",
                "total_rows": 1,
                "truncated_rows": 1,
                "dropped_kinds": ["metric"],
                "budget_tokens": 100,
                "used_tokens": 90,
                "confidence_histogram": {"high": 1, "medium": 0, "low": 0, "unresolved": 0},
                "unsupported_surfaces": [],
            },
            "rows": [
                {
                    "row_id": "QE-001",
                    "surface": "backend",
                    "source_kind": "endpoint",
                    "symbol": "GET /approvals/export",
                    "citations": [{"kind": "file_span", "repo": "repo", "path": "src/api.ts", "line_start": 10, "line_end": 20}],
                    "callers": [],
                    "consumers": ["QE-002"],
                    "confidence": "high",
                    "truncated": True,
                    "unsupported": False,
                    "token_estimate": 42,
                    "notes": ["Export endpoint changed."],
                }
            ],
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as tmp:
            json.dump(pack, tmp)
            pack_path = Path(tmp.name)
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(ticket), "--ticket-key", "SYN-007", "--evidence-pack", str(pack_path)])

        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)
        rendered = test_plan_tool.render_plan(model, scenarios)

        self.assertEqual(1, model.evidence_pack["manifest_summary"]["total_rows"])
        self.assertTrue(any("truncated rows" in gap for gap in model.gaps))
        self.assertTrue(any(scenario.classification == "Code-only" for scenario in scenarios))
        self.assertIn("QA Evidence Pack: 1 rows, 1 truncated", rendered)
        self.assertIn("QE-001", rendered)

    def test_canonical_gather_step_evidence_pack_is_normalized(self) -> None:
        ticket = self.write_ticket(
            """# SYN-009

## Acceptance Criteria

- Users can update their profile display name.
"""
        )
        pack = {
            "event": "qa_evidence_completed",
            "schema_version": "qa-evidence.v1",
            "target": "ProfilePage",
            "base_ref": "main",
            "head_ref": "HEAD",
            "manifest_summary": {
                "row_count": 2,
                "gap_count": 1,
                "pack_modes": ["planning", "review", "change_impact"],
                "truncated": True,
                "omitted_rows": 1,
                "dropped_kinds": [],
            },
            "rows": [
                {
                    "id": "GS-EVID-FLAG",
                    "kind": "feature_flag",
                    "source": "workspace_scan",
                    "citation": {
                        "kind": "file_line",
                        "repo": "frontend",
                        "path": "src/flags.ts",
                        "line": 12,
                    },
                    "subject": {
                        "surface": "feature_flag",
                        "category": "feature_flag",
                        "name": "ProfilePage",
                        "reason": "const enabled = useFlag(flagName);",
                    },
                    "support": {"method": "heuristic_scan", "score": 0},
                },
                {
                    "id": "GS-EVID-ROUTE",
                    "kind": "route_definition",
                    "source": "planning_pack",
                    "citation": {
                        "kind": "symbol",
                        "repo": "frontend",
                        "path": "src/ProfilePage.tsx",
                        "line": 30,
                        "symbol_name": "ProfilePage",
                    },
                    "subject": {"surface": "route", "name": "ProfilePage"},
                    "support": {"method": "static_analyzer", "score": 920},
                },
            ],
            "gaps": [
                {
                    "id": "GS-GAP-001",
                    "source_resolver": "workspace_scan",
                    "kind": "scan_limit_truncated",
                    "message": "The workspace scan reached --scan-limit before traversal completed.",
                    "blocks_complete_coverage": True,
                }
            ],
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as tmp:
            json.dump(pack, tmp)
            pack_path = Path(tmp.name)
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(ticket), "--ticket-key", "SYN-009", "--evidence-pack", str(pack_path)])

        model = test_plan_tool.build_model(args)
        scenarios = test_plan_tool.build_scenarios(model)
        rendered = test_plan_tool.render_plan(model, scenarios)

        summary = model.evidence_pack["manifest_summary"]
        self.assertEqual("qa-evidence.v1", summary["evidence_pack_version"])
        self.assertEqual(2, summary["total_rows"])
        self.assertEqual(1, summary["truncated_rows"])
        self.assertEqual("unresolved", model.evidence_pack["rows"][0]["confidence"])
        self.assertEqual("feature_flag", model.evidence_pack["rows"][0]["source_kind"])
        self.assertTrue(any("scan_limit_truncated" in gap for gap in model.gaps))
        self.assertTrue(any(scenario.classification == "Code-only" for scenario in scenarios))
        self.assertIn("QA Evidence Pack: 2 rows, 1 truncated", rendered)
        self.assertIn("GS-EVID-FLAG", rendered)

    def test_native_gather_step_qa_evidence_output_becomes_row_evidence(self) -> None:
        ticket = self.write_ticket(
            """# SYN-010

## Acceptance Criteria

- Users can update their profile display name.
"""
        )
        pack = {
            "event": "qa_evidence_completed",
            "schema_version": "qa-evidence.v1",
            "target": "ProfilePage",
            "base_ref": "main",
            "head_ref": "HEAD",
            "manifest_summary": {
                "row_count": 1,
                "gap_count": 0,
                "pack_modes": ["planning", "review", "change_impact"],
                "truncated": False,
                "omitted_rows": 0,
                "dropped_kinds": [],
            },
            "rows": [
                {
                    "id": "GS-EVID-FLAG",
                    "kind": "feature_flag",
                    "source": "workspace_scan",
                    "citation": {
                        "kind": "file_line",
                        "repo": "frontend",
                        "path": "src/flags.ts",
                        "line": 12,
                    },
                    "subject": {
                        "surface": "feature_flag",
                        "category": "feature_flag",
                        "name": "ProfilePage",
                    },
                    "support": {"method": "heuristic_scan", "score": 0},
                }
            ],
            "gaps": [],
        }
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args(
            [
                str(ticket),
                "--ticket-key",
                "SYN-010",
                "--gather-workspace",
                "/tmp/workspace",
                "--gather-target",
                "ProfilePage",
                "--diff",
                "main..HEAD",
            ]
        )
        calls = []
        budgets = []

        def fake_run_command(command, budget):
            calls.append(command)
            budgets.append((command, budget))
            label = test_plan_tool.command_label(command)
            text = json.dumps(pack) if label == "qa-evidence" else "{}"
            return test_plan_tool.EvidenceItem(label=label, command=" ".join(command), text=text, ok=True)

        with mock.patch.object(test_plan_tool.shutil, "which", return_value="/usr/local/bin/gather-step"):
            with mock.patch.object(test_plan_tool, "run_command", side_effect=fake_run_command):
                model = test_plan_tool.build_model(args)

        command_names = [part for command in calls for part in command]
        self.assertIn("qa-evidence", command_names)
        self.assertNotIn("search", command_names)
        native_budget = next(budget for command, budget in budgets if "qa-evidence" in command)
        self.assertGreaterEqual(native_budget, 120_000)
        self.assertEqual("qa-evidence.v1", model.evidence_pack["manifest_summary"]["evidence_pack_version"])
        self.assertEqual("feature_flag", model.gather_evidence[0].label)
        self.assertEqual("GS-EVID-FLAG", model.gather_evidence[0].evidence_row_id)

    def test_invalid_evidence_pack_is_input_error(self) -> None:
        ticket = self.write_ticket(
            """# SYN-008

## Acceptance Criteria

- Users can export filtered approvals.
"""
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as tmp:
            tmp.write('{"manifest_summary": {}, "rows": []}')
            pack_path = Path(tmp.name)
        parser = test_plan_tool.build_arg_parser()
        args = parser.parse_args([str(ticket), "--ticket-key", "SYN-008", "--evidence-pack", str(pack_path)])

        with self.assertRaises(test_plan_tool.InputError):
            test_plan_tool.build_model(args)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest

from braingent import config_ledger
from braingent.config_ledger import ConfigItem, ConfigLedgerError

BLOCK = """```yaml
# config-to-enable/v1
- key: FEATURE_X_ENABLED
  kind: env
  service: app
  repo: infra-repo
  path: apps/app/values.yaml
  env: staging
  default: "false"
  target: "true"
  introduced_by: app-repo#12
  enabled_by: null
  depends_on: [OTHER_KEY]
  status: pending
  verify: "feature_x.batch > 0 within 1h"
```
"""


def item(key: str, status: str, **fields: str | None) -> ConfigItem:
    return ConfigItem(key=key, kind="env", status=status, **fields)  # type: ignore[arg-type]


class ParserTests(unittest.TestCase):
    def test_parses_a_valid_block(self) -> None:
        (parsed,) = config_ledger.parse_blocks(f"## Config to enable\n\n{BLOCK}")
        self.assertEqual(parsed.key, "FEATURE_X_ENABLED")
        self.assertEqual(parsed.default, "false")
        self.assertEqual(parsed.target, "true")
        self.assertIsNone(parsed.enabled_by)
        self.assertEqual(parsed.depends_on, ("OTHER_KEY",))
        self.assertTrue(parsed.is_open)

    def test_multiple_blocks_are_concatenated_and_other_fences_ignored(self) -> None:
        other = "```yaml\n- key: not-a-ledger\n```\n"
        second = BLOCK.replace("FEATURE_X_ENABLED", "FEATURE_Y_ENABLED")
        parsed = config_ledger.parse_blocks(f"{BLOCK}\n{other}\n{second}")
        self.assertEqual([entry.key for entry in parsed], ["FEATURE_X_ENABLED", "FEATURE_Y_ENABLED"])

    def test_unquoted_booleans_are_coerced(self) -> None:
        text = "```yaml\n# config-to-enable/v1\n- key: K\n  kind: flag\n  status: pending\n  default: false\n  target: true\n```\n"
        (parsed,) = config_ledger.parse_blocks(text)
        self.assertEqual((parsed.default, parsed.target), ("false", "true"))

    def test_invalid_kind_and_status_are_errors(self) -> None:
        for field, bad in (("kind", "secret"), ("status", "done")):
            with self.subTest(field=field):
                text = BLOCK.replace(f"{field}: {'env' if field == 'kind' else 'pending'}", f"{field}: {bad}")
                with self.assertRaisesRegex(ConfigLedgerError, f"unknown {field} `{bad}`"):
                    config_ledger.parse_blocks(text)

    def test_missing_required_field_is_an_error(self) -> None:
        text = "```yaml\n# config-to-enable/v1\n- key: K\n  kind: env\n```\n"
        with self.assertRaisesRegex(ConfigLedgerError, "missing required field `status`"):
            config_ledger.parse_blocks(text)

    def test_non_list_and_bad_yaml_are_errors(self) -> None:
        with self.assertRaisesRegex(ConfigLedgerError, "YAML list"):
            config_ledger.parse_blocks("```yaml\n# config-to-enable/v1\nkey: K\n```\n")
        with self.assertRaisesRegex(ConfigLedgerError, "invalid YAML"):
            config_ledger.parse_blocks("```yaml\n# config-to-enable/v1\n- key: [unclosed\n```\n")

    def test_none_marker(self) -> None:
        self.assertTrue(config_ledger.has_none_marker("## Config to enable\n\nNone\n\n## Log\n"))
        self.assertFalse(config_ledger.has_none_marker(f"## Config to enable\n\n{BLOCK}"))
        self.assertFalse(config_ledger.has_none_marker("## Log\n"))
        self.assertEqual(config_ledger.parse_blocks("## Config to enable\n\nNone\n"), [])


class MergeTests(unittest.TestCase):
    def test_most_advanced_status_wins_in_either_order(self) -> None:
        for first, second in (("pending", "applied"), ("applied", "pending")):
            with self.subTest(order=(first, second)):
                (merged,) = config_ledger.merge_items([[item("K", first)], [item("K", second)]])
                self.assertEqual(merged.status, "applied")

    def test_terminal_status_beats_pending_only_when_later(self) -> None:
        (later,) = config_ledger.merge_items([[item("K", "pending")], [item("K", "not-needed")]])
        (earlier,) = config_ledger.merge_items([[item("K", "not-needed")], [item("K", "pending")]])
        self.assertEqual(later.status, "not-needed")
        self.assertEqual(earlier.status, "not-needed")
        (dormant,) = config_ledger.merge_items([[item("K", "dormant")], [item("K", "pending")]])
        self.assertEqual(dormant.status, "dormant")

    def test_advanced_status_beats_terminal_and_later_terminal_wins_over_terminal(self) -> None:
        (advanced,) = config_ledger.merge_items([[item("K", "dormant")], [item("K", "verified")]])
        self.assertEqual(advanced.status, "verified")
        (kept,) = config_ledger.merge_items([[item("K", "verified")], [item("K", "dormant")]])
        self.assertEqual(kept.status, "verified")
        (terminal,) = config_ledger.merge_items([[item("K", "dormant")], [item("K", "not-needed")]])
        self.assertEqual(terminal.status, "not-needed")

    def test_fields_are_filled_from_the_other_source(self) -> None:
        page = item("K", "pr-open", env="staging", repo="infra-repo")
        pr = ConfigItem(key="K", kind="env", status="pending", env="staging", enabled_by="infra-repo#3", depends_on=("A",))
        (merged,) = config_ledger.merge_items([[page], [pr]])
        self.assertEqual(merged.status, "pr-open")
        self.assertEqual(merged.enabled_by, "infra-repo#3")
        self.assertEqual(merged.repo, "infra-repo")
        self.assertEqual(merged.depends_on, ("A",))

    def test_env_is_part_of_the_key(self) -> None:
        merged = config_ledger.merge_items([[item("K", "pending", env="staging")], [item("K", "applied", env="prod")]])
        self.assertEqual(sorted((entry.env or "", entry.status) for entry in merged), [("prod", "applied"), ("staging", "pending")])


class RenderTests(unittest.TestCase):
    def test_table_orders_open_statuses_before_verified(self) -> None:
        rows = config_ledger.render_table(
            [item("DONE", "verified"), item("NEW", "pending"), item("OFF", "dormant"), item("SKIP", "not-needed"), item("LIVE", "applied")]
        )
        keys = [row.split("|")[1].strip("` ") for row in rows[2:]]
        self.assertEqual(keys, ["NEW", "LIVE", "OFF", "DONE", "SKIP"])
        self.assertIn("| key | kind | repo/path | env | target |", rows[0])

    def test_render_blocks_round_trips(self) -> None:
        original = config_ledger.parse_blocks(BLOCK)
        self.assertEqual(config_ledger.parse_blocks(config_ledger.render_blocks(original)), original)
        self.assertEqual(config_ledger.render_blocks([]), "None")

    def test_replace_section_leaves_other_sections_untouched(self) -> None:
        body = "# Epic\n\n## Goal\n\nKeep me.\n\n## Config to enable\n\nNone\n\n## Log\n\n- keep this too\n"
        updated = config_ledger.replace_section(body, [item("K", "pending")])
        self.assertIn("## Goal\n\nKeep me.\n", updated)
        self.assertTrue(updated.endswith("## Log\n\n- keep this too\n"))
        self.assertEqual([entry.key for entry in config_ledger.parse_blocks(updated)], ["K"])

    def test_replace_section_appends_when_missing(self) -> None:
        updated = config_ledger.replace_section("# Epic\n\n## Goal\n\nText.\n", [item("K", "pending")])
        self.assertEqual([entry.key for entry in config_ledger.parse_blocks(updated)], ["K"])


class CollectTests(unittest.TestCase):
    def test_search_limit_is_an_error(self) -> None:
        payload = [{"number": n, "repository": {"name": "app-repo"}, "body": BLOCK} for n in range(100)]
        with self.assertRaisesRegex(ConfigLedgerError, "limit"):
            config_ledger.collect_pr_items("x", [], ["@me"], lambda _: json.dumps(payload), lambda _: None)

    def test_pr_numbers_are_sorted_numerically(self) -> None:
        payload = [
            {"number": 10, "repository": {"name": "app-repo"}, "body": BLOCK.replace("pending", "not-needed")},
            {"number": 9, "repository": {"name": "app-repo"}, "body": BLOCK.replace("pending", "dormant")},
        ]
        items = config_ledger.collect_pr_items("x", [], ["@me"], lambda _: json.dumps(payload), lambda _: None)
        self.assertEqual(config_ledger.merge_items([items])[0].status, "not-needed")

    def test_closed_unmerged_prs_are_excluded(self) -> None:
        payload = [
            {"number": 1, "repository": {"name": "app-repo"}, "url": "https://example.test/1", "body": BLOCK, "state": "closed"},
            {"number": 2, "repository": {"name": "app-repo"}, "url": "https://example.test/2", "body": BLOCK.replace("FEATURE_X", "FEATURE_Y"), "state": "closed"},
        ]

        def runner(args: list[str]) -> str:
            if args[:2] == ["search", "prs"]:
                return json.dumps(payload)
            return json.dumps({"state": "CLOSED" if args[2].endswith("/1") else "MERGED"})

        items = config_ledger.collect_pr_items("x", [], ["@me"], runner, lambda _: None)
        self.assertEqual([item.key for item in items], ["FEATURE_Y_ENABLED"])

    def test_collects_from_pr_bodies_with_injected_runner(self) -> None:
        calls: list[list[str]] = []
        payload = [
            {"number": 12, "repository": {"name": "app-repo"}, "url": "u", "state": "OPEN", "body": BLOCK},
            {"number": 13, "repository": {"name": "app-repo"}, "url": "u", "state": "OPEN", "body": "no block"},
            {"number": 14, "repository": {"name": "app-repo"}, "url": "u", "state": "OPEN", "body": "```yaml\n# config-to-enable/v1\n- key: K\n```\n"},
        ]

        def runner(arguments: list[str]) -> str:
            calls.append(arguments)
            return json.dumps(payload)

        warnings: list[str] = []
        items = config_ledger.collect_pr_items("checkout-latency", ["acme", "other"], ["@me"], runner, warnings.append)
        self.assertEqual(len(calls), 2)
        self.assertIn("epic:checkout-latency", calls[0])
        self.assertEqual(calls[0][calls[0].index("--author") + 1], "@me")
        self.assertEqual(calls[0][calls[0].index("--owner") + 1], "acme")
        self.assertEqual(calls[1][calls[1].index("--owner") + 1], "other")
        self.assertEqual({entry.key for entry in items}, {"FEATURE_X_ENABLED"})
        self.assertTrue(all("app-repo#14" in message for message in warnings))
        self.assertEqual(len(warnings), 2)

    def test_invalid_gh_output_is_an_error(self) -> None:
        with self.assertRaises(ConfigLedgerError):
            config_ledger.collect_pr_items("x", [], ["@me"], lambda _: "not json", lambda _: None)


class UntrustedInputTests(unittest.TestCase):
    def test_overlength_identity_is_rejected(self) -> None:
        for field in ("key", "env", "target"):
            text = BLOCK.replace("  status: pending", f"  {field}: {'K' * 300}A\n  status: pending")
            with self.subTest(field=field), self.assertRaisesRegex(ConfigLedgerError, "300"):
                config_ledger.parse_blocks(text)

    def test_one_query_per_author_and_owner(self) -> None:
        calls: list[list[str]] = []

        def runner(arguments: list[str]) -> str:
            calls.append(arguments)
            return "[]"

        config_ledger.collect_pr_items("x", ["acme"], ["@me", "trusted-bot[bot]"], runner, lambda _: None)
        self.assertEqual([call[call.index("--author") + 1] for call in calls], ["@me", "trusted-bot[bot]"])

    def test_default_author_is_me(self) -> None:
        calls: list[list[str]] = []

        def runner(arguments: list[str]) -> str:
            calls.append(arguments)
            return "[]"

        config_ledger.collect_pr_items("x", [], [], runner, lambda _: None)
        self.assertEqual(calls[0][calls[0].index("--author") + 1], config_ledger.DEFAULT_AUTHOR)

    def test_option_like_author_or_owner_is_rejected(self) -> None:
        for authors, owners in ((["--json"], []), (["a b"], []), (["@me"], ["-x"])):
            with self.subTest(authors=authors, owners=owners), self.assertRaises(ConfigLedgerError):
                config_ledger.collect_pr_items("x", owners, authors, lambda _: "[]", lambda _: None)

    def test_non_scalar_values_are_rejected(self) -> None:
        for field, value in (("service", "{a: b}"), ("verify", "[a, b]"), ("key", "[K]"), ("depends_on", "[{a: b}]"), ("depends_on", "[[x]]")):
            with self.subTest(field=field, value=value):
                text = f"```yaml\n# config-to-enable/v1\n- key: K\n  kind: env\n  status: pending\n  {field}: {value}\n```\n"
                with self.assertRaisesRegex(ConfigLedgerError, "scalar"):
                    config_ledger.parse_blocks(text)

    def test_values_are_flattened_and_bounded(self) -> None:
        text = (
            "```yaml\n# config-to-enable/v1\n- key: K\n  kind: env\n  status: pending\n"
            '  verify: "line one\\n## Injected heading\\n```\\nmore"\n'
            f"  target: {'x' * 300}\n"
            '  depends_on: ["a\\nb"]\n```\n'
        )
        (item,) = config_ledger.parse_blocks(text)
        self.assertEqual(item.verify, "line one ## Injected heading ``` more")
        self.assertEqual(len(item.target or ""), config_ledger.MAX_VALUE_LENGTH)
        self.assertEqual(item.depends_on, ("a b",))
        rendered = config_ledger.render_blocks([item])
        self.assertEqual(rendered.count("```"), 3)
        self.assertNotIn("\n## Injected", rendered)

    def test_table_cells_escape_pipes_and_backticks(self) -> None:
        item = ConfigItem(key="A`B|C", kind="env", status="pending", target="x|y`z`", verify="a | b")
        row = config_ledger.render_table([item])[2]
        self.assertTrue(row.startswith("| `A'B\\|C` |"))
        self.assertIn("x\\|y\\`z\\`", row)
        self.assertIn("a \\| b", row)
        self.assertEqual(len(row.replace("\\|", "").split("|")), 11)


if __name__ == "__main__":
    unittest.main()

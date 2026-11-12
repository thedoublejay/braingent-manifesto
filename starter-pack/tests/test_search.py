from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from braingent import core, mcp_tools, search

PACK_ROOT = Path(__file__).resolve().parents[1]


def record_text(title: str, kind: str, status: str, body: str, extra: str = "") -> str:
    return (
        f"---\ntitle: {title}\nrecord_kind: {kind}\nstatus: {status}\ndate: 2026-10-07\ntimezone: UTC\n"
        f"organization: org--acme\nproject: null\n{extra}---\n\n# {title}\n\n{body}\n"
    )


class SearchTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        shutil.copytree(PACK_ROOT / "preferences", self.root / "preferences")
        (self.root / "templates").mkdir()
        (self.root / "workflows").mkdir()
        self.records = self.root / "orgs" / "org--acme" / "records"
        self.records.mkdir(parents=True)
        for name in ("repo--github--acme--billing-api", "repo--github--acme--widget", "repo--github--other--widget"):
            (self.root / "repositories" / name).mkdir(parents=True)
        (self.root / "topics" / "topic--tenant-isolation").mkdir(parents=True)
        core.set_repo_root(self.root)
        self.addCleanup(core.set_repo_root, PACK_ROOT)
        self.addCleanup(self._tmp.cleanup)

    def write(self, name: str, title: str, body: str, kind: str = "learning", status: str = "active", extra: str = "") -> Path:
        path = self.records / name
        path.write_text(record_text(title, kind, status, body, extra), encoding="utf-8")
        return path

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = core.main(["--root", str(self.root), *argv])
        return code, out.getvalue(), err.getvalue()


class StrictFilterTests(SearchTestCase):
    def test_unknown_filter_key_fails_with_a_suggestion(self) -> None:
        self.write("2026-10-07--learning--a.md", "A", "Body.", extra="ticket: EX-1\n")
        code, out, err = self.run_cli("find", "tickets=EX-1", "--count")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("unknown filter `tickets`", err)
        self.assertIn("did you mean `ticket`", err)

    def test_recall_and_mcp_reject_unknown_keys_too(self) -> None:
        code, _, err = self.run_cli("recall", "bogus=1")
        self.assertEqual(code, 2)
        self.assertIn("unknown filter `bogus`", err)
        with self.assertRaises(core.FilterError):
            mcp_tools.find({"bogus": "1"})

    def test_known_keys_and_aliases_still_work(self) -> None:
        self.write("2026-10-07--learning--a.md", "A", "Body.", extra="ticket: EX-1\nrepositories: [repo--github--acme--billing-api]\n")
        for args in (["ticket=ex-1"], ["kind=learning"], ["repo=billing-api"], ["q=body"], ["Body"]):
            with self.subTest(args=args):
                code, out, _ = self.run_cli("find", *args, "--count")
                self.assertEqual((code, out.strip()), (0, "1"))

    def test_ambiguous_repository_name_lists_candidates(self) -> None:
        code, _, err = self.run_cli("find", "repo=widget", "--count")
        self.assertEqual(code, 2)
        self.assertIn("`widget` is ambiguous", err)
        self.assertIn("repo--github--acme--widget", err)
        self.assertIn("repo--github--other--widget", err)

    def test_zero_results_for_an_unknown_entity_hints_at_near_names(self) -> None:
        code, out, err = self.run_cli("find", "topic=tenant", "--count")
        self.assertEqual((code, out.strip()), (0, "0"))
        self.assertIn("no topics entry `topic--tenant`", err)
        self.assertIn("topic--tenant-isolation", err)


class SearchTests(SearchTestCase):
    def seed(self) -> None:
        self.write(
            "2026-09-16--decision--identity-moves-to-vendor-b.md", "Identity adapter moves to Vendor B",
            "We replace Vendor A for sign-in. Residency reasoning was wrong.", kind="decision", status="accepted",
            extra="ticket: EX-77\n",
        )
        self.write(
            "2026-08-15--decision--adopt-vendor-a.md", "Adopt Vendor A as the identity adapter",
            "Identity adapter identity adapter. Vendor A is the sign-in front door.", kind="decision", status="superseded",
        )
        self.write(
            "2026-10-01--learning--pool-timeouts.md", "Connection pool timeouts under burst",
            "The pool was exhausted. Mentions EX-77 in passing while reviewing reviewers.",
        )
        self.write("2026-10-02--task--unrelated.md", "Rotate the widget", "Nothing relevant here.", kind="task", status="completed")

    def test_ranked_search_prefers_current_over_superseded(self) -> None:
        self.seed()
        hits = search.search("identity adapter")
        self.assertEqual([Path(hit["path"]).name for hit in hits[:2]], [
            "2026-09-16--decision--identity-moves-to-vendor-b.md", "2026-08-15--decision--adopt-vendor-a.md",
        ])
        self.assertEqual((hits[0]["class"], hits[1]["class"]), ("candidate", "do_not_use"))
        self.assertTrue(hits[0]["snippet"])

    def test_any_term_may_match_and_stemming_applies(self) -> None:
        self.seed()
        names = [Path(hit["path"]).name for hit in search.search("why was the pool exhausted during review")]
        self.assertEqual(names[0], "2026-10-01--learning--pool-timeouts.md")

    def test_exact_identifier_in_metadata_outranks_a_body_mention(self) -> None:
        self.seed()
        names = [Path(hit["path"]).name for hit in search.search("EX-77")]
        self.assertEqual(names, ["2026-09-16--decision--identity-moves-to-vendor-b.md", "2026-10-01--learning--pool-timeouts.md"])

    def test_structured_filters_narrow_a_search(self) -> None:
        self.seed()
        hits = search.search("identity adapter", core.parse_find_filters(["kind=decision", "status=accepted"]))
        self.assertEqual(len(hits), 1)

    def test_query_syntax_characters_are_literal(self) -> None:
        self.seed()
        self.assertEqual(search.search('"NEAR( pool* AND -x:y'), search.search("NEAR pool AND x y"))

    def test_index_rebuilds_after_an_edit_and_a_delete(self) -> None:
        self.seed()
        self.assertTrue(search.search("widget"))
        path = self.write("2026-10-03--learning--fresh.md", "Fresh note", "A zebra crossing.")
        self.assertEqual(len(search.search("zebra")), 1)
        path.unlink()
        self.assertEqual(search.search("zebra"), [])

    def test_renaming_a_record_never_leaves_its_old_path_as_a_hit(self) -> None:
        self.seed()
        path = self.write("2026-10-03--learning--fresh.md", "Fresh note", "A zebra crossing.")
        self.assertEqual([hit["path"] for hit in search.search("zebra")], ["orgs/org--acme/records/2026-10-03--learning--fresh.md"])
        path.rename(path.with_name("2026-10-03--learning--renamed.md"))
        self.assertEqual([hit["path"] for hit in search.search("zebra")], ["orgs/org--acme/records/2026-10-03--learning--renamed.md"])

    def test_unavailable_search_is_a_one_line_error(self) -> None:
        self.seed()
        failing = unittest.mock.patch.object(search, "search", side_effect=search.SearchUnavailableError("full-text search is unavailable: no fts5"))
        with failing:
            code, out, err = self.run_cli("search", "pool")
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(err.strip(), "error: full-text search is unavailable: no fts5")

    def test_touching_a_record_marks_the_index_stale(self) -> None:
        self.seed()
        search.search("pool")
        self.assertFalse(search.index_is_stale())
        target = next(self.records.iterdir())
        stamp = core.SQLITE_PATH.stat().st_mtime + 5
        os.utime(target, (stamp, stamp))
        self.assertTrue(search.index_is_stale())

    def test_rebuild_replaces_the_database_atomically(self) -> None:
        self.seed()
        search.search("pool")
        self.assertEqual([path.name for path in self.root.glob(".braingent.db*")], [".braingent.db"])

    def test_cli_and_mcp(self) -> None:
        self.seed()
        code, out, _ = self.run_cli("search", "identity", "adapter", "kind=decision", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual({hit["kind"] for hit in payload}, {"decision"})
        self.assertEqual(set(payload[0]), {"path", "title", "kind", "status", "date", "class", "reason", "score", "snippet", "corpus"})
        code, out, _ = self.run_cli("search", "identity adapter", "--paths", "--limit", "1")
        self.assertEqual(out.strip().splitlines(), ["orgs/org--acme/records/2026-09-16--decision--identity-moves-to-vendor-b.md"])
        code, out, _ = self.run_cli("search", "nothingmatchesthis")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(mcp_tools.search("identity adapter", {"status": "accepted"}, limit=5)[0]["status"], "accepted")
        with self.assertRaises(ValueError):
            mcp_tools.search("   ")


class KeywordAndRewordingTests(SearchTestCase):
    def seed(self) -> None:
        self.write(
            "2026-09-16--decision--identity-moves-to-vendor-b.md", "Identity adapter moves to Vendor B",
            "We replace Vendor A. Residency reasoning was wrong.", kind="decision", status="accepted",
            extra="keywords: [login provider, single sign-on]\n",
        )
        self.write("2026-10-01--learning--pool-timeouts.md", "Connection pool timeouts under burst", "The pool was exhausted by a login storm.")
        self.write("2026-10-02--task--unrelated.md", "Rotate the widget", "Nothing relevant here.", kind="task", status="completed")

    def test_keywords_field_is_valid_and_must_be_a_list(self) -> None:
        self.seed()
        self.assertEqual([issue.message for issue in core.validate() if "keywords" in issue.message], [])
        self.write("2026-10-03--learning--bad.md", "Bad", "Body.", extra="keywords: one string\n")
        self.assertTrue(any("keywords" in issue.message and "list" in issue.message for issue in core.validate()))

    def test_a_keyword_finds_a_record_whose_text_never_uses_the_word(self) -> None:
        self.seed()
        names = [Path(hit["path"]).name for hit in search.search("single sign-on")]
        self.assertEqual(names, ["2026-09-16--decision--identity-moves-to-vendor-b.md"])

    def test_a_keyword_outranks_a_body_mention(self) -> None:
        self.seed()
        names = [Path(hit["path"]).name for hit in search.search("login")]
        self.assertEqual(names[0], "2026-09-16--decision--identity-moves-to-vendor-b.md")
        self.assertIn("2026-10-01--learning--pool-timeouts.md", names)

    def test_rewordings_merge_into_one_ranked_list(self) -> None:
        self.seed()
        self.assertEqual(search.search("who do users authenticate with"), [])
        merged = search.search_fused(["who do users authenticate with", "identity adapter", "widget rotation"], limit=5)
        names = [Path(hit["path"]).name for hit in merged]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {"2026-09-16--decision--identity-moves-to-vendor-b.md", "2026-10-02--task--unrelated.md"})
        self.assertEqual(search.search_fused(["identity adapter"]), search.search("identity adapter"))

    def test_decisions_and_learnings_outrank_work_logs_of_similar_relevance(self) -> None:
        body = "The retention window for audit exports is ninety days."
        self.write("2026-10-01--task--retention-job.md", "Retention window job", body, kind="task", status="completed")
        self.write("2026-10-01--review--retention-pr.md", "Retention window review", body, kind="review", status="completed")
        self.write("2026-09-01--decision--retention.md", "Retention window ruling", body, kind="decision", status="accepted")
        names = [Path(hit["path"]).name for hit in search.search("retention window")]
        self.assertEqual(names[0], "2026-09-01--decision--retention.md")
        self.assertEqual(len(names), 3)

    def test_a_record_far_down_the_raw_ranking_can_still_be_returned(self) -> None:
        for index in range(60):
            self.write(f"2026-10-01--task--noise-{index:02d}.md", f"Deploy window note {index}", "deploy window deploy window", kind="task", status="completed")
        self.write("2026-09-01--decision--freeze.md", "Change freeze ruling", "No deploy during the quarter-end window.", kind="decision", status="accepted")
        names = [Path(hit["path"]).name for hit in search.search("quarter-end deploy window", limit=3)]
        self.assertIn("2026-09-01--decision--freeze.md", names)

    def test_also_reaches_the_cli_and_mcp(self) -> None:
        self.seed()
        code, out, _ = self.run_cli("search", "who do users authenticate with", "--also", "identity adapter", "--paths")
        self.assertEqual((code, out.strip()), (0, "orgs/org--acme/records/2026-09-16--decision--identity-moves-to-vendor-b.md"))
        hits = mcp_tools.search("who do users authenticate with", also=["identity adapter"])
        self.assertEqual(len(hits), 1)

    def test_an_index_built_before_the_keywords_column_is_rebuilt(self) -> None:
        self.seed()
        search.search("pool")
        import sqlite3

        conn = sqlite3.connect(core.SQLITE_PATH)
        conn.execute("UPDATE index_meta SET value = 'old-schema' WHERE key = 'paths_digest'")
        conn.commit()
        conn.close()
        self.assertTrue(search.index_is_stale())
        self.assertTrue(search.search("single sign-on"))


if __name__ == "__main__":
    unittest.main()

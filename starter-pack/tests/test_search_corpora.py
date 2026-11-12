from __future__ import annotations

import contextlib
import hashlib
import io
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from braingent import config, core, mcp_tools, search

PACK_ROOT = Path(__file__).resolve().parents[1]
CORPUS_CONFIG = """
[[search.corpus]]
name = "plans"
path = "../plans"
exclude = ["**/archive/**"]
max_bytes = 2000
"""


def record_text(title: str, body: str) -> str:
    return (
        f"---\ntitle: {title}\nrecord_kind: learning\nstatus: active\ndate: 2026-10-07\ntimezone: UTC\n"
        f"organization: org--acme\nproject: null\n---\n\n# {title}\n\n{body}\n"
    )


class CorpusTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "memory"
        self.plans = base / "plans"
        shutil.copytree(PACK_ROOT / "preferences", self.root / "preferences")
        (self.root / "templates").mkdir()
        (self.root / "workflows").mkdir()
        self.records = self.root / "orgs" / "org--acme" / "records"
        self.records.mkdir(parents=True)
        (self.root / ".braingent").mkdir()
        (self.root / ".braingent" / "config.toml").write_text(CORPUS_CONFIG, encoding="utf-8")
        self.addCleanup(core.set_repo_root, PACK_ROOT)
        self.addCleanup(self._tmp.cleanup)

    def doc(self, relative: str, text: str) -> Path:
        path = self.plans / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def record(self, name: str, title: str, body: str) -> Path:
        path = self.records / name
        path.write_text(record_text(title, body), encoding="utf-8")
        return path

    def seed(self) -> None:
        self.doc(
            "acme/2026-11-11--handover--retirement-recovery-ex-6931.md",
            "---\ntype: handover\nstatus: active\n---\n\n# Retirement recovery handover\n\nHow the walrus queue was drained.\n",
        )
        self.doc("acme/plan/2026-11-01--walrus-rollout.md", "# Walrus rollout plan\n\nShip the walrus queue in two waves.\n")
        self.doc("acme/raw/2026-11-02--walrus-dump.md", "# Raw walrus dump\n\nwalrus walrus walrus\n")
        self.doc("acme/archive/2026-01-01--old-walrus.md", "# Old walrus\n\nwalrus\n")
        self.doc("acme/2026-11-03--walrus.md.bak-1", "# Backup walrus\n\nwalrus\n")
        self.doc("acme/2026-11-04--walrus.bak-copy.md", "# Backup copy\n\nwalrus\n")
        self.doc("acme/2026-11-05--huge-walrus.md", "# Huge\n\n" + "walrus " * 500)
        self.doc(".hidden/2026-11-06--walrus.md", "# Hidden\n\nwalrus\n")
        self.doc("acme/review/1490-source/docs/walrus-checkout.md", "# Checkout\n\nwalrus\n")
        self.doc("acme/review/1490-source/pyproject.toml", "[project]\nname = 'x'\n")
        self.doc("acme/env/lib/site-packages/pkg/walrus-vendored.md", "# Vendored\n\nwalrus\n")
        (self.plans / ".git").mkdir(parents=True, exist_ok=True)
        self.record("2026-10-01--learning--walrus-queue.md", "Walrus queue learning", "The walrus queue backs up under load.")
        core.set_repo_root(self.root)


class CorpusConfigTests(CorpusTestCase):
    def test_corpus_entries_are_parsed_and_resolved_against_the_root(self) -> None:
        loaded = config.load_config(self.root, home=self.root)
        self.assertEqual(len(loaded.search_corpora), 1)
        corpus = loaded.search_corpora[0]
        self.assertEqual((corpus.name, corpus.path, corpus.exclude, corpus.max_bytes), ("plans", "../plans", ("**/archive/**",), 2000))
        self.assertEqual(loaded.issues, ())

    def test_invalid_entries_become_issues_not_crashes(self) -> None:
        (self.root / ".braingent" / "config.toml").write_text(
            '[[search.corpus]]\nname = "Bad Name"\npath = "x"\n\n[[search.corpus]]\nname = "ok"\n\n'
            '[[search.corpus]]\nname = "dup"\npath = "a"\n\n[[search.corpus]]\nname = "dup"\npath = "b"\n',
            encoding="utf-8",
        )
        loaded = config.load_config(self.root, home=self.root)
        self.assertEqual([corpus.name for corpus in loaded.search_corpora], ["dup"])
        self.assertEqual(len(loaded.issues), 3)


class CorpusSearchTests(CorpusTestCase):
    def test_rewordings_keep_distinct_corpora_with_matching_display_paths(self) -> None:
        self.seed()
        config_path = self.root / ".braingent" / "config.toml"
        config_path.write_text(CORPUS_CONFIG.replace('name = "plans"', 'name = "orgs"'), encoding="utf-8")
        name = "2026-10-01--learning--collision.md"
        self.record(name, "Memory document", "collisionwalrus collisionotter")
        self.doc(f"org--acme/records/{name}", "# External document\n\ncollisionwalrus collisionotter\n")
        core.set_repo_root(self.root)
        hits = search.search_fused(["collisionwalrus", "collisionotter"])
        self.assertEqual(len(hits), 2)
        self.assertEqual({hit["corpus"] for hit in hits}, {"records", "orgs"})
        self.assertEqual(len({hit["path"] for hit in hits}), 1)

    def test_identifier_in_a_corpus_filename_finds_the_document_first(self) -> None:
        self.seed()
        hits = search.search("EX-6931")
        self.assertEqual(hits[0]["path"], "plans/acme/2026-11-11--handover--retirement-recovery-ex-6931.md")
        self.assertEqual((hits[0]["corpus"], hits[0]["class"], hits[0]["kind"], hits[0]["status"]), ("plans", "reference", "handover", "active"))
        self.assertEqual(Path(hits[0]["file"]), self.plans / "acme/2026-11-11--handover--retirement-recovery-ex-6931.md")

    def test_records_and_documents_share_one_ranked_list(self) -> None:
        self.seed()
        hits = search.search("walrus queue")
        corpora = {hit["path"]: hit["corpus"] for hit in hits}
        self.assertEqual(corpora["orgs/org--acme/records/2026-10-01--learning--walrus-queue.md"], "records")
        self.assertIn("plans/acme/plan/2026-11-01--walrus-rollout.md", corpora)

    def test_raw_hidden_backup_oversized_and_excluded_files_are_not_indexed(self) -> None:
        self.seed()
        paths = {hit["path"] for hit in search.search("walrus", limit=50)}
        self.assertIn("plans/acme/plan/2026-11-01--walrus-rollout.md", paths)
        for name in ("raw/", "archive/", ".bak", "backup", "huge", ".hidden", "1490-source", "site-packages"):
            with self.subTest(name=name):
                self.assertFalse([path for path in paths if name in path], paths)

    def test_a_deleted_document_is_never_a_live_hit(self) -> None:
        self.seed()
        target = self.plans / "acme/plan/2026-11-01--walrus-rollout.md"
        self.assertIn("plans/acme/plan/2026-11-01--walrus-rollout.md", {hit["path"] for hit in search.search("rollout")})
        target.unlink()
        self.assertEqual(search.search("rollout"), [])

    def test_a_renamed_document_is_found_under_its_new_name(self) -> None:
        self.seed()
        search.search("rollout")
        old = self.plans / "acme/plan/2026-11-01--walrus-rollout.md"
        old.rename(old.with_name("2026-11-01--walrus-rollout-v2.md"))
        self.assertEqual([hit["path"] for hit in search.search("rollout")], ["plans/acme/plan/2026-11-01--walrus-rollout-v2.md"])

    def test_structured_filters_keep_search_to_records(self) -> None:
        self.seed()
        hits = search.search("walrus", {"record_kind": ["learning"]})
        self.assertEqual({hit["corpus"] for hit in hits}, {"records"})

    def test_documents_never_enter_find_or_mcp_get(self) -> None:
        self.seed()
        search.search("walrus")
        self.assertEqual(
            [item["path"] for item in mcp_tools.find({"q": "walrus"})],
            ["orgs/org--acme/records/2026-10-01--learning--walrus-queue.md"],
        )
        with self.assertRaises(ValueError):
            mcp_tools.get("plans/acme/plan/2026-11-01--walrus-rollout.md")

    def test_a_missing_corpus_directory_is_skipped(self) -> None:
        self.seed()
        shutil.rmtree(self.plans)
        self.assertEqual({hit["corpus"] for hit in search.search("walrus")}, {"records"})

    def test_symlinked_files_and_directories_are_not_indexed(self) -> None:
        self.seed()
        outside = self.root.parent / "outside.md"
        outside.write_text("# Private\n\nuniqueprivatewalrus\n", encoding="utf-8")
        (self.plans / "linked.md").symlink_to(outside)
        (self.plans / "linked-directory").symlink_to(self.records, target_is_directory=True)
        self.assertEqual(search.search("uniqueprivatewalrus"), [])
        self.assertFalse(any("linked" in item.relpath for item in search.corpus_files()))

    def test_changing_corpus_root_invalidates_cached_content(self) -> None:
        self.seed()
        other = self.root.parent / "otherplans"
        shutil.copytree(self.plans, other)
        document = other / "acme/plan/2026-11-01--walrus-rollout.md"
        document.write_text("# Replacement\n\nnewcorpuscontent\n", encoding="utf-8")
        os.utime(document, (1, 1))
        search.search("rollout")
        config_path = self.root / ".braingent" / "config.toml"
        config_path.write_text(CORPUS_CONFIG.replace("../plans", "../otherplans"), encoding="utf-8")
        core.set_repo_root(self.root)
        self.assertEqual(search.search("rollout")[0]["title"], "Replacement")
        hits = search.search("newcorpuscontent")
        self.assertEqual(len(hits), 1)
        self.assertEqual(Path(hits[0]["file"]), document)

    def test_version_1_6_index_is_rebuilt_for_an_empty_corpus(self) -> None:
        self.seed()
        shutil.rmtree(self.plans)
        search.search("walrus")
        legacy_names = sorted(path.relative_to(self.root).as_posix() for path in search.record_paths())
        legacy_digest = hashlib.sha256("\n".join(legacy_names).encode("utf-8")).hexdigest()
        with contextlib.closing(sqlite3.connect(core.SQLITE_PATH)) as conn, conn:
            conn.execute("DROP TABLE corpus_fts")
            conn.execute("DROP TABLE corpus_docs")
            conn.execute("UPDATE index_meta SET value = ? WHERE key = 'paths_digest'", (legacy_digest,))
        self.assertEqual({hit["corpus"] for hit in search.search("walrus")}, {"records"})

    def test_unreadable_corpus_file_raises_a_search_error(self) -> None:
        self.seed()
        out, err = io.StringIO(), io.StringIO()
        with (
            patch.object(Path, "read_bytes", side_effect=PermissionError("corpus file is unreadable")),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = core.main(["--root", str(self.root), "search", "walrus"])
        self.assertEqual((code, out.getvalue()), (2, ""))
        self.assertEqual(err.getvalue().strip(), "error: could not refresh search index: corpus file is unreadable")

    def test_documents_about_backups_are_searchable(self) -> None:
        self.seed()
        self.doc("acme/2026-11-12--database-backup-plan.md", "# Database backup plan\n\nnightlysnapshotrecovery\n")
        self.assertEqual(len(search.search("nightlysnapshotrecovery")), 1)

    def test_document_hashes_are_stored(self) -> None:
        self.seed()
        search.search("walrus")
        import sqlite3

        conn = sqlite3.connect(core.SQLITE_PATH)
        try:
            rows = dict(conn.execute("SELECT path, sha256 FROM corpus_docs WHERE corpus = 'plans'").fetchall())
        finally:
            conn.close()
        self.assertEqual(len(rows["acme/plan/2026-11-01--walrus-rollout.md"]), 64)
        self.assertNotIn("acme/raw/2026-11-02--walrus-dump.md", rows)


if __name__ == "__main__":
    unittest.main()

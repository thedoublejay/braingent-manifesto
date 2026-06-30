from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from braingent import config as bgconfig
from braingent import core, factcheck
from braingent.core import Record


def _record(body: str, **frontmatter: object) -> Record:
    return Record(path=Path("rec.md"), frontmatter=dict(frontmatter), body=body)


class ScopeTests(unittest.TestCase):
    def test_verification_field_opts_in(self) -> None:
        cfg = bgconfig.DEFAULT_CONFIG
        self.assertTrue(factcheck.in_scope(_record("", verification="unverified"), cfg))

    def test_scope_topic_opts_in(self) -> None:
        cfg = bgconfig.BraingentConfig(factcheck_scope_topics=("company-research",))
        self.assertTrue(factcheck.in_scope(_record("", topics=["company-research"]), cfg))

    def test_unrelated_record_out_of_scope(self) -> None:
        cfg = bgconfig.BraingentConfig(factcheck_scope_topics=("company-research",))
        self.assertFalse(factcheck.in_scope(_record("", topics=["auth"]), cfg))


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = bgconfig.BraingentConfig(
            factcheck_slop_domains=("contentmill.example",),
            factcheck_prwire_domains=bgconfig.DEFAULT_FACTCHECK_PRWIRE_DOMAINS,
            factcheck_tier12_domains=bgconfig.DEFAULT_FACTCHECK_TIER12_DOMAINS,
        )

    def test_tiers_classify_footnote_sources(self) -> None:
        body = (
            "## Findings\n"
            "- Revenue tripled.[^a]\n"
            "- Company launched.[^b]\n"
            "- Rumoured pivot.[^c]\n\n"
            "## Footnotes\n"
            "[^a]: https://reuters.com/x\n"
            "[^b]: https://prnewswire.com/y\n"
            "[^c]: https://contentmill.example/z\n"
        )
        result = factcheck.audit(_record(body, verification="unverified"), self.cfg)
        self.assertEqual(result["tier_counts"]["tier12"], 1)
        self.assertEqual(result["tier_counts"]["prwire"], 1)
        self.assertEqual(result["tier_counts"]["slop"], 1)
        self.assertEqual(len(result["slop_sources"]), 1)
        self.assertEqual(len(result["prwire_sources"]), 1)
        self.assertEqual(result["needs_ai_judgment"], 1)  # only the slop source

    def test_unverified_and_single_source_markers(self) -> None:
        body = "## Findings\n- A claim [UNVERIFIED].\n- Thin claim [SINGLE-SOURCE].[^a]\n\n## Footnotes\n[^a]: https://reuters.com/x\n"
        result = factcheck.audit(_record(body, verification="unverified"), self.cfg)
        self.assertEqual(len(result["unverified_markers"]), 1)
        self.assertEqual(len(result["single_source_markers"]), 1)

    def test_bare_claim_detected_but_sourced_bullet_clean(self) -> None:
        body = "## Findings\n- Unsourced assertion about the market.\n- Sourced assertion.[^a]\n\n## Footnotes\n[^a]: https://reuters.com/x\n"
        result = factcheck.audit(_record(body, verification="unverified"), self.cfg)
        self.assertEqual(len(result["bare_claim_candidates"]), 1)
        self.assertIn("Unsourced assertion", result["bare_claim_candidates"][0]["text"])

    def test_footnotes_section_bullets_not_flagged_as_bare(self) -> None:
        body = "## Footnotes\n- not a claim line\n[^a]: https://reuters.com/x\n"
        result = factcheck.audit(_record(body, verification="unverified"), self.cfg)
        self.assertEqual(result["bare_claim_candidates"], [])

    def test_legacy_inline_source_still_counts(self) -> None:
        body = "## Findings\n- Old-style claim (source: https://reuters.com/x).\n"
        result = factcheck.audit(_record(body, verification="unverified"), self.cfg)
        self.assertEqual(result["tier_counts"]["tier12"], 1)
        self.assertEqual(result["bare_claim_candidates"], [])  # has a legacy source

    def test_fenced_code_block_ignored(self) -> None:
        body = "## Findings\n```\n- this is sample code, not a claim\n```\n- real unsourced claim\n"
        result = factcheck.audit(_record(body, verification="unverified"), self.cfg)
        self.assertEqual(len(result["bare_claim_candidates"]), 1)


class NextUnverifiedTests(unittest.TestCase):
    def test_oldest_unverified_chosen(self) -> None:
        records = [
            _record("", verification="verified", date="2026-01-01"),
            _record("", verification="unverified", date="2026-03-01"),
            _record("", verification="stale", date="2026-02-01"),
        ]
        chosen = factcheck.next_unverified(records)
        assert chosen is not None
        self.assertEqual(chosen.frontmatter["date"], "2026-02-01")  # oldest needing work

    def test_none_when_all_verified(self) -> None:
        records = [_record("", verification="verified", date="2026-01-01")]
        self.assertIsNone(factcheck.next_unverified(records))


class RunFactcheckTests(unittest.TestCase):
    def test_audit_single_record_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record = root / "report.md"
            record.write_text(
                "---\nrecord_kind: learning\nstatus: active\nverification: unverified\n---\n"
                "## Findings\n- Big claim.[^a]\n\n## Footnotes\n[^a]: https://prnewswire.com/x\n",
                encoding="utf-8",
            )
            saved_root, saved_cfg = core.REPO_ROOT, core.CONFIG
            try:
                core.REPO_ROOT = root
                core.CONFIG = bgconfig.DEFAULT_CONFIG
                exit_code = factcheck.run_factcheck(record=str(record), output_json=True)
            finally:
                core.REPO_ROOT, core.CONFIG = saved_root, saved_cfg
            self.assertEqual(exit_code, 0)

    def test_missing_record_returns_2(self) -> None:
        saved_root = core.REPO_ROOT
        try:
            core.REPO_ROOT = Path(tempfile.gettempdir())
            self.assertEqual(factcheck.run_factcheck(record="does-not-exist.md"), 2)
        finally:
            core.REPO_ROOT = saved_root


if __name__ == "__main__":
    unittest.main()

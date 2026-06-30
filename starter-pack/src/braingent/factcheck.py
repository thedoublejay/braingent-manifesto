"""Deterministic pre-pass for a research fact-check loop.

This does the mechanical 90% of fact-checking a research record so a human or AI
fact-checker spends effort only on the irreducible judgment (does this source
actually support this claim?), not on re-scanning the whole document.

Intended flow:

  1. A first pass writes a research record with ``verification: unverified``,
     often citing weak sources.
  2. ``braingent factcheck`` audits the record and emits a precise punch-list:
     which cited sources are low-credibility, which are PR-wire (self-reported),
     which claims carry ``[UNVERIFIED]`` / ``[SINGLE-SOURCE]`` markers, which
     bullets make an assertion with no citation at all, and a source-tier
     breakdown. Citations are GFM footnote definitions (``[^id]: URL``); a
     ``[^id]`` marker on a claim line means that claim is sourced.
  3. The fact-checker works only that punch-list: re-source or downgrade the
     flagged lines, confirm the rest, then stamp ``verification`` + a score.

The command makes NO network calls and NO edits. It is read-only analysis.

Scope: a record is in scope when it carries a ``verification`` frontmatter field
or when its topics intersect the configured ``[factcheck] scope_topics``. The
credibility tiers are driven entirely by config (``[factcheck] slop_domains`` /
``prwire_domains`` / ``tier12_domains``) so the same engine works for any
research domain without code changes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from braingent import core
from braingent.core import Record, as_list, as_scalar, load_records, split_frontmatter

# Citations live in GFM footnote definitions: ``[^id]: <URL or path>`` at line
# start. The footnote MARKER ``[^id]`` on a claim line means "this is sourced".
# Legacy inline forms ``(source: URL)`` / ``[Source: URL]`` are still matched so
# an unconverted record does not silently read as unsourced.
FN_DEF_RE = re.compile(r"^\s*\[\^([^\]]+)\]:\s*(.+)$")
FN_REF_RE = re.compile(r"\[\^[^\]]+\]")
LEGACY_SOURCE_RE = re.compile(r"\(sources?:\s*([^)]+)\)|\[Source:\s*([^\]]+)\]", re.I)
URL_RE = re.compile(r"https?://([a-z0-9.-]+)", re.I)
UNVERIFIED_RE = re.compile(r"\[UNVERIFIED")
SINGLE_RE = re.compile(r"\[SINGLE-SOURCE\]")
ANALYSIS_RE = re.compile(r"\[ANALYSIS\]")

VERIFICATION_STATES = ("unverified", "verified", "stale")
NEEDS_VERIFICATION = ("", "unverified", "stale")

# Sections whose bullets are not fact claims, so a missing citation is expected.
NON_CLAIM_HEADINGS = re.compile(r"fact-check|footnotes|related records|sources", re.I)


def _hosts_of(citation: str) -> list[str]:
    """All hosts in a citation string (a footnote def may hold several URLs)."""
    return [match.group(1).lower().removeprefix("www.") for match in URL_RE.finditer(citation)]


def _tier_of(host: str, cfg: core.BraingentConfig) -> str:
    if host in cfg.factcheck_slop_domains:
        return "slop"
    if host in cfg.factcheck_prwire_domains:
        return "prwire"
    if host in cfg.factcheck_tier12_domains:
        return "tier12"
    return "primary_or_other"


def _verification(record: Record) -> str:
    return as_scalar(record.frontmatter.get("verification")).lower()


def in_scope(record: Record, cfg: core.BraingentConfig) -> bool:
    """A record is auditable when it opts in via a ``verification`` field or a
    configured scope topic."""
    if "verification" in record.frontmatter:
        return True
    topics = {as_scalar(item) for item in as_list(record.frontmatter.get("topics")) + as_list(record.frontmatter.get("topic"))}
    return bool(topics & set(cfg.factcheck_scope_topics))


def audit(record: Record, cfg: core.BraingentConfig) -> dict[str, Any]:
    """Mechanical audit of one record. Pure analysis, no edits."""
    body = record.body

    slop_hits: list[dict[str, Any]] = []
    prwire_hits: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []
    single_source: list[dict[str, Any]] = []
    bare_claims: list[dict[str, Any]] = []
    tier_counts = {"slop": 0, "prwire": 0, "tier12": 0, "primary_or_other": 0}
    source_citations = 0

    in_non_claim_section = False
    in_fence = False
    for number, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("## "):
            in_non_claim_section = bool(NON_CLAIM_HEADINGS.search(stripped))

        if UNVERIFIED_RE.search(line):
            unverified.append({"line": number, "text": stripped[:160]})
        if SINGLE_RE.search(line):
            single_source.append({"line": number, "text": stripped[:160]})

        fn_def = FN_DEF_RE.match(line)
        legacy = list(LEGACY_SOURCE_RE.finditer(line))

        citation_strings: list[str] = []
        if fn_def:
            citation_strings.append(fn_def.group(2))
        for match in legacy:
            citation_strings.append(match.group(1) or match.group(2) or "")
        for citation in citation_strings:
            for host in _hosts_of(citation):
                source_citations += 1
                tier = _tier_of(host, cfg)
                tier_counts[tier] += 1
                if tier == "slop":
                    slop_hits.append({"line": number, "host": host, "text": stripped[:160]})
                elif tier == "prwire":
                    prwire_hits.append({"line": number, "host": host, "text": stripped[:140]})

        has_source = bool(legacy) or (bool(FN_REF_RE.search(line)) and not fn_def)

        # Bare-claim heuristic: a list bullet asserting something with no marker
        # of any kind (no citation, no UNVERIFIED, no ANALYSIS), outside
        # non-claim sections and tables. Advisory only.
        if (
            not in_non_claim_section
            and not fn_def
            and re.match(r"^\s*[-*]\s+\S", line)
            and not has_source
            and not UNVERIFIED_RE.search(line)
            and not ANALYSIS_RE.search(line)
            and "|" not in line
            and not stripped.lower().startswith(("- [", "* ["))
            and not re.search(r"\.md\b|^- `|see\s", stripped, re.I)
        ):
            bare_claims.append({"line": number, "text": stripped[:140]})

    todo = len(slop_hits) + len(unverified) + len(single_source)
    return {
        "path": record.relpath,
        "verification": _verification(record) or "MISSING",
        "verification_score": as_scalar(record.frontmatter.get("verification_score")) or "null",
        "source_citations": source_citations,
        "tier_counts": tier_counts,
        "slop_sources": slop_hits,
        "prwire_sources": prwire_hits,
        "unverified_markers": unverified,
        "single_source_markers": single_source,
        "bare_claim_candidates": bare_claims,
        "needs_ai_judgment": todo,
    }


def iter_scoped_records(cfg: core.BraingentConfig) -> tuple[list[Record], list[Any]]:
    records, parse_issues = load_records(include_parse_errors=False)
    scoped = [record for record in records if in_scope(record, cfg)]
    return scoped, parse_issues


def next_unverified(records: list[Record]) -> Record | None:
    """The oldest record still needing verification, by record date ascending."""
    candidates = [record for record in records if _verification(record) in NEEDS_VERIFICATION]
    if not candidates:
        return None
    return sorted(candidates, key=lambda record: (record.date_sort or "9999", record.relpath))[0]


def _print_report(result: dict[str, Any]) -> None:
    print(f"\n=== {result['path']} ===")
    print(f"verification: {result['verification']}  score: {result['verification_score']}")
    tier = result["tier_counts"]
    print(
        f"source citations: {result['source_citations']}  "
        f"(slop {tier['slop']}, prwire {tier['prwire']}, tier1/2 {tier['tier12']}, "
        f"primary/other {tier['primary_or_other']})"
    )

    if result["slop_sources"]:
        print(f"\n  ACTION: {len(result['slop_sources'])} low-credibility source(s). Re-source or mark [UNVERIFIED]:")
        for hit in result["slop_sources"]:
            print(f"    L{hit['line']} [{hit['host']}] {hit['text']}")
    if result["prwire_sources"]:
        print(f"\n  NOTE: {len(result['prwire_sources'])} PR-wire source(s) (self-reported, label as such):")
        for hit in result["prwire_sources"]:
            print(f"    L{hit['line']} [{hit['host']}] {hit['text']}")
    if result["unverified_markers"]:
        print(f"\n  OPEN: {len(result['unverified_markers'])} [UNVERIFIED] marker(s) to resolve:")
        for hit in result["unverified_markers"]:
            print(f"    L{hit['line']} {hit['text']}")
    if result["single_source_markers"]:
        print(f"\n  THIN: {len(result['single_source_markers'])} [SINGLE-SOURCE] marker(s) (find a second source):")
        for hit in result["single_source_markers"]:
            print(f"    L{hit['line']} {hit['text']}")
    if result["bare_claim_candidates"]:
        shown = result["bare_claim_candidates"][:25]
        print(f"\n  REVIEW: {len(result['bare_claim_candidates'])} unsourced bullet(s) (add [^id]/[UNVERIFIED]/[ANALYSIS], or ignore if not a claim):")
        for hit in shown:
            print(f"    L{hit['line']} {hit['text']}")
        if len(result["bare_claim_candidates"]) > len(shown):
            print(f"    ... and {len(result['bare_claim_candidates']) - len(shown)} more")

    verdict = "CLEAN (mechanical pass)" if result["needs_ai_judgment"] == 0 else f"{result['needs_ai_judgment']} item(s) need judgment"
    print(f"\n  -> {verdict}")


def run_factcheck(
    record: str | None = None,
    audit_all: bool = False,
    next_only: bool = False,
    output_json: bool = False,
) -> int:
    cfg = core.CONFIG

    if record:
        # Single-record audit does not need a full repo scan (or its taxonomy).
        path = Path(record)
        if not path.is_absolute():
            candidate = core.REPO_ROOT / record
            path = candidate if candidate.exists() else path
        if not path.exists():
            print(f"not found: {record}")
            return 2
        frontmatter, body, error = split_frontmatter(path)
        if error or frontmatter is None:
            print(f"cannot parse frontmatter: {record}")
            return 2
        targets = [Record(path=path, frontmatter=frontmatter, body=body)]
        results = [audit(record_obj, cfg) for record_obj in targets]
        if output_json:
            print(json.dumps(results, indent=2, default=str))
        else:
            _print_report(results[0])
        return 0

    scoped, parse_issues = iter_scoped_records(cfg)
    if parse_issues:
        core.print_issues(parse_issues)
        return 1

    if next_only:
        chosen = next_unverified(scoped)
        if chosen is None:
            if output_json:
                print(json.dumps({"found": False, "scoped_records": len(scoped)}))
            else:
                print("no unverified in-scope records")
            return 1
        if output_json:
            print(
                json.dumps(
                    {
                        "found": True,
                        "path": chosen.relpath,
                        "title": chosen.title,
                        "date": chosen.date_sort,
                        "remaining_unverified": sum(1 for r in scoped if _verification(r) in NEEDS_VERIFICATION),
                    }
                )
            )
        else:
            print(chosen.relpath)
        return 0
    elif audit_all:
        targets = scoped
        if not targets:
            print("no in-scope records (set [factcheck] scope_topics or add a `verification` field)")
            return 1
    else:
        print("Provide a record path, or use --all or --next.")
        return 2

    results = [audit(record_obj, cfg) for record_obj in targets]
    if output_json:
        print(json.dumps(results, indent=2, default=str))
        return 0
    for result in results:
        _print_report(result)
    if len(results) > 1:
        need = sum(1 for result in results if result["needs_ai_judgment"])
        print(f"\n{'=' * 50}\n{len(results)} records audited; {need} need fact-check work.")
    return 0

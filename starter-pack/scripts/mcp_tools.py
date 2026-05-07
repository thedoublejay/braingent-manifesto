#!/usr/bin/env python3
"""MCP-agnostic Braingent retrieval tools.

These functions are pure Python so tests and non-MCP agents can use the same
retrieval path as the MCP server.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import braingent
from scripts.compressors import apply_pipeline

READ_FIRST_FILES = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "INDEX.md",
    "CURRENT_STATE.md",
    "preferences/naming.md",
    "preferences/agent-workflow.md",
    "preferences/capture-policy.md",
    "preferences/search-recipes.md",
    "preferences/taxonomy.md",
    "preferences/note-taking-and-ai-memory.md",
]

SCALAR_FILTER_COLUMNS = {
    "record_kind": "record_kind",
    "status": "status",
    "organization": "organization",
    "project": "project",
    "ticket": "ticket",
    "date": "date",
}

LINK_FILTER_TABLES = {
    "projects": "record_projects",
    "repositories": "record_repositories",
    "topics": "record_topics",
    "tools": "record_tools",
    "people": "record_people",
    "ai_tools": "record_ai_tools",
    "prs": "record_prs",
    "commits": "record_commits",
}


def _resolve_safe(path: str) -> Path:
    candidate = (REPO_ROOT / path).resolve()
    repo_root = REPO_ROOT.resolve()
    if candidate != repo_root and repo_root not in candidate.parents:
        raise ValueError(f"path escapes repo root: {path}")
    if not candidate.is_file():
        raise ValueError(f"path is not a file: {path}")
    return candidate


def _query_filters(query: dict[str, Any] | None) -> dict[str, list[str]]:
    filters: dict[str, list[str]] = {}
    for key, raw_value in (query or {}).items():
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        for value in values:
            if value in (None, ""):
                continue
            normalized_key, normalized_value = braingent.normalize_filter(key, str(value))
            filters.setdefault(normalized_key, []).append(normalized_value)
    return filters


def _compact_records() -> list[dict[str, Any]]:
    path = braingent.RECORDS_COMPACT_JSON_PATH
    if not path.exists():
        raise ValueError("compact index is missing; run scripts/reindex.sh")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("compact index must contain a JSON list")
    return [item for item in payload if isinstance(item, dict)]


def _limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("limit must be greater than zero")
    return limit


def _record_from_index_row(row: sqlite3.Row) -> braingent.Record:
    frontmatter = json.loads(row["frontmatter_json"])
    return braingent.Record(path=REPO_ROOT / str(row["path"]), frontmatter=frontmatter, body="")


def _find_indexed(filters: dict[str, list[str]], max_results: int) -> list[dict[str, Any]] | None:
    if not filters or "text" in filters or not braingent.SQLITE_PATH.exists():
        return None

    clauses: list[str] = []
    params: list[str] = []
    for key, values in filters.items():
        if key in SCALAR_FILTER_COLUMNS:
            column = SCALAR_FILTER_COLUMNS[key]
            for value in values:
                clauses.append(f"records.{column} = ?")
                params.append(value)
            continue
        if key in LINK_FILTER_TABLES:
            table = LINK_FILTER_TABLES[key]
            for value in values:
                clauses.append(f"EXISTS (SELECT 1 FROM {table} WHERE {table}.path = records.path AND {table}.value = ?)")
                params.append(value)
            continue
        return None

    where = " AND ".join(clauses) if clauses else "1"
    conn = sqlite3.connect(braingent.SQLITE_PATH)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT path, frontmatter_json
            FROM records
            WHERE {where}
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    records = [_record_from_index_row(row) for row in rows]
    records.sort(key=braingent.recall_sort_key)
    return [braingent.compact_record_to_json(record) for record in records[:max_results]]


def _find_loaded(filters: dict[str, list[str]], max_results: int, records: list[braingent.Record]) -> list[dict[str, Any]]:
    matched = [record for record in records if braingent.record_matches(record, filters)]
    matched.sort(key=braingent.recall_sort_key)
    return [braingent.compact_record_to_json(record) for record in matched[:max_results]]


def _load_records_or_raise() -> list[braingent.Record]:
    records, parse_issues = braingent.load_records(include_parse_errors=False)
    if parse_issues:
        raise ValueError("; ".join(issue.format() for issue in parse_issues))
    return records


def find(query: dict[str, Any] | None = None, limit: int = 10) -> list[dict[str, Any]]:
    """Search Braingent records by frontmatter query.

    Empty queries return the compact index prefix. Non-empty queries use the
    same normalization and matching logic as scripts/find.sh, but return only
    the compact 9-field projection to keep first-pass retrieval small.
    """

    max_results = _limit(limit)
    if not query:
        return _compact_records()[:max_results]

    filters = _query_filters(query)
    indexed = _find_indexed(filters, max_results)
    if indexed is not None:
        return indexed

    return _find_loaded(filters, max_results, _load_records_or_raise())


def find_many(queries: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Run multiple compact searches while sharing the expensive scan fallback."""

    max_results = _limit(limit)
    records: list[braingent.Record] | None = None
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in queries:
        filters = _query_filters(query)
        indexed = _find_indexed(filters, max_results)
        if indexed is None:
            if records is None:
                records = _load_records_or_raise()
            indexed = _find_loaded(filters, max_results, records)
        for result in indexed:
            path = str(result.get("path") or "")
            if not path or path in seen:
                continue
            seen.add(path)
            output.append(result)
            if len(output) >= max_results:
                return output
    return output


def get(path: str, depth: str = "summary") -> dict[str, Any]:
    """Read one Braingent file with a compactness depth.

    depth values are "summary", "full", and "frontmatter". Summary is the
    default because it strips predictable low-signal sections before returning
    the hydrated record.
    """

    full_path = _resolve_safe(path)
    text = full_path.read_text(encoding="utf-8")
    frontmatter, _, error = braingent.parse_frontmatter_text(full_path, text)
    if error:
        raise ValueError(error)
    frontmatter = frontmatter or {}
    record_kind = str(frontmatter.get("record_kind") or "unknown")
    content = apply_pipeline(text, record_kind=record_kind, depth=depth)
    return {
        "path": full_path.relative_to(REPO_ROOT).as_posix(),
        "frontmatter": frontmatter,
        "body": content,
        "depth": depth,
    }


def guide() -> dict[str, Any]:
    """Return the static read-first chain in a cache-stable envelope."""

    parts: list[str] = []
    files: list[str] = []
    for relpath in READ_FIRST_FILES:
        path = REPO_ROOT / relpath
        if not path.exists():
            continue
        files.append(relpath)
        parts.append(f"<!-- {relpath} -->\n{path.read_text(encoding='utf-8')}")
    return {
        "content": "\n\n".join(parts),
        "files": files,
        "cache_control": {"type": "ephemeral"},
    }

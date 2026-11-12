"""Ranked full-text search over records, backed by the rebuildable SQLite index."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from braingent import core

FTS_TABLE = "records_fts"
FTS_SCHEMA = (
    f"CREATE VIRTUAL TABLE {FTS_TABLE} USING fts5("
    "path UNINDEXED, title, ids, meta, body, tokenize='porter unicode61')"
)
COLUMN_WEIGHTS = (0.0, 10.0, 8.0, 4.0, 1.0)
CANDIDATE_POOL = 200
DEFAULT_LIMIT = 10
SUPERSEDED_PENALTY = 0.5
TERM_PATTERN = re.compile(r"\w[\w#./-]*\w|\w")
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*-\d+|[\w.-]+#\d+")
ID_FIELDS = ("ticket", "prs", "related_prs", "commits", "branches")
META_FIELDS = ("summary", "organization", "project", "projects", "repositories", "repo", "topics", "topic", "tools", "epic", "people")
STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "did", "do", "does", "for", "from", "had", "has",
    "have", "how", "i", "in", "is", "it", "its", "of", "on", "or", "our", "so", "than", "that", "the", "their",
    "then", "there", "these", "this", "those", "to", "was", "we", "were", "what", "when", "where", "which",
    "who", "why", "will", "with",
})


class SearchUnavailableError(RuntimeError):
    pass


def fts_row(record: core.Record) -> tuple[str, str, str, str, str]:
    fm = record.frontmatter
    ids = [core.as_scalar(item) for name in ID_FIELDS for item in core.as_list(fm.get(name))]
    meta = [core.as_scalar(item) for name in META_FIELDS for item in core.as_list(fm.get(name))]
    return (record.relpath, record.title, " ".join([*ids, record.path.stem]), " ".join(meta), record.body)


def write_fts(conn: sqlite3.Connection, records: list[core.Record]) -> bool:
    try:
        conn.execute(FTS_SCHEMA)
    except sqlite3.OperationalError:
        return False
    conn.executemany(f"INSERT INTO {FTS_TABLE} VALUES (?, ?, ?, ?, ?)", [fts_row(record) for record in records])
    conn.execute("CREATE TABLE index_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO index_meta VALUES ('scanned_paths', ?)", (str(len(record_paths())),))
    return True


def record_paths() -> list[Path]:
    roots = core.load_taxonomy().get("record_scan_roots", [])
    return [path for path in core.iter_markdown_files(roots) if path.suffix == ".md"]


def index_is_stale() -> bool:
    db_path = core.SQLITE_PATH
    if not db_path.exists():
        return True
    built = db_path.stat().st_mtime
    paths = record_paths()
    if max((path.stat().st_mtime for path in paths), default=0.0) > built:
        return True
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT value FROM index_meta WHERE key = 'scanned_paths'").fetchone()
    except sqlite3.DatabaseError:
        return True
    finally:
        conn.close()
    return row is None or row[0] != str(len(paths))


def ensure_index() -> None:
    if not index_is_stale():
        return
    records, _ = core.load_records(include_parse_errors=False)
    core.write_sqlite_index(records, core.SQLITE_PATH)


def query_terms(query: str) -> list[str]:
    terms = [term for term in TERM_PATTERN.findall(query) if re.search(r"\w", term)]
    kept = [term for term in terms if term.lower() not in STOPWORDS]
    return list(dict.fromkeys(kept or terms))


def match_expression(terms: list[str]) -> str:
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)


def search(
    query: str,
    filters: dict[str, list[str]] | None = None,
    limit: int = DEFAULT_LIMIT,
    stale_days: int | None = None,
) -> list[dict[str, Any]]:
    terms = query_terms(query)
    if not terms:
        raise ValueError("search needs at least one word")
    if limit < 1:
        raise ValueError("limit must be greater than zero")
    stale_days = core.CONFIG.recall_stale_days if stale_days is None else stale_days
    structured = {key: values for key, values in (filters or {}).items() if key != "text"}
    identifiers = [found.lower() for found in IDENTIFIER_PATTERN.findall(query)]

    ensure_index()
    conn = sqlite3.connect(core.SQLITE_PATH)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT records.path, records.frontmatter_json, {FTS_TABLE}.ids AS ids,
                   bm25({FTS_TABLE}, {", ".join(str(weight) for weight in COLUMN_WEIGHTS)}) AS score,
                   snippet({FTS_TABLE}, 4, '', '', ' … ', 24) AS snippet
            FROM {FTS_TABLE} JOIN records ON records.path = {FTS_TABLE}.path
            WHERE {FTS_TABLE} MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (match_expression(terms), CANDIDATE_POOL if structured or identifiers else max(limit * 4, 40)),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise SearchUnavailableError(f"full-text search is unavailable: {exc}") from exc
    finally:
        conn.close()

    ranked: list[tuple[int, float, str, dict[str, Any]]] = []
    for row in rows:
        record = core.Record(path=core.REPO_ROOT / str(row["path"]), frontmatter=json.loads(row["frontmatter_json"]), body="")
        if structured and not core.record_matches(record, structured):
            continue
        label, reason = core.recall_classification(record, stale_days)
        score = float(row["score"]) * (SUPERSEDED_PENALTY if label == "do_not_use" else 1.0)
        ids = f" {str(row['ids']).lower()} "
        exact = any(f" {identifier} " in ids for identifier in identifiers)
        hit = {
            "path": record.relpath,
            "title": record.title,
            "kind": record.kind,
            "status": record.status,
            "date": record.date_sort,
            "class": label,
            "reason": reason,
            "score": round(-score, 3),
            "snippet": " ".join(str(row["snippet"]).split()),
        }
        ranked.append((0 if exact else 1, score, record.relpath, hit))
    ranked.sort(key=lambda item: item[:3])
    return [hit for *_, hit in ranked[:limit]]


def split_arguments(arguments: list[str]) -> tuple[str, list[str]]:
    words = [argument for argument in arguments if not re.match(r"^[a-z_]+=", argument)]
    return " ".join(words), [argument for argument in arguments if argument not in words]


def run_search(arguments: list[str], output_json: bool = False, paths_only: bool = False, limit: int = DEFAULT_LIMIT) -> int:
    query, raw_filters = split_arguments(arguments)
    hits = search(query, core.parse_find_filters(raw_filters), limit=limit)
    if output_json:
        print(json.dumps(hits, indent=2))
        return 0 if hits else 1
    if not hits:
        return 1
    if paths_only:
        for hit in hits:
            print(hit["path"])
        return 0
    print("| Path | Kind | Status | Date | Class | Title |")
    print("| --- | --- | --- | --- | --- | --- |")
    for hit in hits:
        print(f"| `{hit['path']}` | {hit['kind']} | {hit['status']} | {hit['date']} | {hit['class']} | {hit['title']} |")
    return 0

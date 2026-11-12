"""Ranked full-text search over records and configured read-only corpora, backed by the rebuildable SQLite index."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from braingent import core

FTS_TABLE = "records_fts"
FTS_SCHEMA = (
    f"CREATE VIRTUAL TABLE {FTS_TABLE} USING fts5("
    "path UNINDEXED, title, ids, keywords, meta, body, tokenize='porter unicode61')"
)
COLUMN_WEIGHTS = (0.0, 10.0, 8.0, 8.0, 4.0, 1.0)
BODY_COLUMN = 5
CORPUS_TABLE = "corpus_fts"
CORPUS_SCHEMA = (
    f"CREATE VIRTUAL TABLE {CORPUS_TABLE} USING fts5("
    "corpus UNINDEXED, path UNINDEXED, title, ids, meta, body, tokenize='porter unicode61')"
)
CORPUS_DOCS_SCHEMA = (
    "CREATE TABLE corpus_docs (corpus TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL, size INTEGER NOT NULL, "
    "title TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, date TEXT NOT NULL, PRIMARY KEY (corpus, path))"
)
CORPUS_WEIGHTS = (0.0, 0.0, 10.0, 8.0, 4.0, 1.0)
DEFAULT_CORPUS_EXCLUDES = ("**/raw/**", "**/*.bak*")
PRUNED_DIR_NAMES = frozenset({"node_modules", "site-packages", "__pycache__"})
CODE_TREE_MARKERS = frozenset({".git", "pyproject.toml", "package.json", "Cargo.toml", "go.mod"})
RECORDS_CORPUS = "records"
DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")
HEADING = re.compile(r"^#\s+(.+?)\s*$", re.M)
CANDIDATE_POOL = 200
DEFAULT_LIMIT = 10
SUPERSEDED_PENALTY = 0.5
KIND_WEIGHTS = {"decision": 1.5, "learning": 1.5}
FUSION_K = 60
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


@dataclass(frozen=True)
class CorpusFile:
    corpus: str
    root: Path
    path: Path

    @property
    def relpath(self) -> str:
        return self.path.relative_to(self.root).as_posix()

    @property
    def key(self) -> str:
        return f"{self.corpus}:{self.relpath}"


def fts_row(record: core.Record) -> tuple[str, str, str, str, str, str]:
    fm = record.frontmatter
    ids = [core.as_scalar(item) for name in ID_FIELDS for item in core.as_list(fm.get(name))]
    meta = [core.as_scalar(item) for name in META_FIELDS for item in core.as_list(fm.get(name))]
    keywords = [core.as_scalar(item) for item in core.as_list(fm.get("keywords"))]
    return (record.relpath, record.title, " ".join([*ids, record.path.stem]), " ".join(keywords), " ".join(meta), record.body)


def corpus_roots() -> dict[str, Path]:
    return {corpus.name: (core.REPO_ROOT / Path(corpus.path).expanduser()).resolve() for corpus in core.CONFIG.search_corpora}


def is_excluded(relpath: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(relpath, pattern) or fnmatch.fnmatch(f"/{relpath}", pattern) for pattern in patterns)


def corpus_files() -> list[CorpusFile]:
    """Markdown files of each configured corpus, minus hidden folders, excludes and oversized files."""

    roots = corpus_roots()
    found: list[CorpusFile] = []
    for corpus in core.CONFIG.search_corpora:
        root = roots[corpus.name]
        if not root.is_dir():
            continue
        patterns = DEFAULT_CORPUS_EXCLUDES + corpus.exclude
        for directory, dirnames, filenames in os.walk(root):
            base = Path(directory)
            if base != root and CODE_TREE_MARKERS.intersection([*dirnames, *filenames]):
                dirnames[:] = []
                continue
            prefix = base.relative_to(root).as_posix()
            prefix = "" if prefix == "." else f"{prefix}/"
            dirnames[:] = sorted(
                name
                for name in dirnames
                if not name.startswith(".") and name not in PRUNED_DIR_NAMES
                and not (base / name).is_symlink() and not is_excluded(f"{prefix}{name}/_", patterns)
            )
            for name in sorted(filenames):
                if not name.endswith(".md") or name.startswith(".") or is_excluded(f"{prefix}{name}", patterns):
                    continue
                path = base / name
                if not path.is_symlink() and path.is_file() and path.stat().st_size <= corpus.max_bytes:
                    found.append(CorpusFile(corpus.name, root, path))
    return found


def corpus_row(item: CorpusFile) -> tuple[tuple[str, ...], tuple[object, ...]]:
    raw = item.path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    frontmatter, body, error = core.parse_frontmatter_text(item.path, text)
    fm = frontmatter if isinstance(frontmatter, dict) and not error else {}
    body = body if fm else text
    heading = HEADING.search(body)
    title = str(fm.get("title") or (heading.group(1) if heading else item.path.stem))
    found_ids = [match.lower() for match in IDENTIFIER_PATTERN.findall(f"{item.path.stem} {title}")]
    kind = str(fm.get("type") or "document")
    status = str(fm.get("status") or "-")
    date_match = DATE_PREFIX.match(item.path.name)
    date = str(fm.get("date") or (date_match.group(1) if date_match else "-"))
    meta = " ".join([item.corpus, kind, status, *(str(fm[key]) for key in ("scope",) if fm.get(key))])
    fts = (item.corpus, item.relpath, title, " ".join([*found_ids, item.path.stem]), meta, body)
    doc = (item.corpus, item.relpath, hashlib.sha256(raw).hexdigest(), len(raw), title, kind, status, date)
    return fts, doc


def write_fts(conn: sqlite3.Connection, records: list[core.Record]) -> bool:
    try:
        conn.execute(FTS_SCHEMA)
        conn.execute(CORPUS_SCHEMA)
    except sqlite3.OperationalError:
        return False
    conn.executemany(f"INSERT INTO {FTS_TABLE} VALUES (?, ?, ?, ?, ?, ?)", [fts_row(record) for record in records])
    files = corpus_files()
    rows = [corpus_row(item) for item in files]
    conn.execute(CORPUS_DOCS_SCHEMA)
    conn.executemany(f"INSERT INTO {CORPUS_TABLE} VALUES (?, ?, ?, ?, ?, ?)", [fts for fts, _ in rows])
    conn.executemany("INSERT INTO corpus_docs VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [doc for _, doc in rows])
    conn.execute("CREATE TABLE index_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("INSERT INTO index_meta VALUES ('paths_digest', ?)", (paths_digest(record_paths(), files),))
    return True


def paths_digest(paths: list[Path], files: list[CorpusFile]) -> str:
    """Fingerprint of the search schema, corpus configuration and indexed file set."""

    names = sorted([path.relative_to(core.REPO_ROOT).as_posix() for path in paths] + [item.key for item in files])
    roots = corpus_roots()
    corpora = [
        (corpus.name, str(roots[corpus.name]), corpus.exclude, corpus.max_bytes)
        for corpus in core.CONFIG.search_corpora
    ]
    fingerprint = json.dumps({"schema": 3, "corpora": corpora, "paths": names}, sort_keys=True)
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def record_paths() -> list[Path]:
    roots = core.load_taxonomy().get("record_scan_roots", [])
    return [path for path in core.iter_markdown_files(roots) if path.suffix == ".md"]


def index_is_stale() -> bool:
    db_path = core.SQLITE_PATH
    if not db_path.exists():
        return True
    built = db_path.stat().st_mtime
    paths = record_paths()
    files = corpus_files()
    if max((path.stat().st_mtime for path in [*paths, *(item.path for item in files)]), default=0.0) > built:
        return True
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT value FROM index_meta WHERE key = 'paths_digest'").fetchone()
    except sqlite3.DatabaseError:
        return True
    finally:
        conn.close()
    return row is None or row[0] != paths_digest(paths, files)


def ensure_index() -> None:
    try:
        if not index_is_stale():
            return
        records, _ = core.load_records(include_parse_errors=False)
        core.write_sqlite_index(records, core.SQLITE_PATH)
    except OSError as exc:
        raise SearchUnavailableError(f"could not refresh search index: {exc}") from exc


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
    expression = match_expression(terms)
    weights = ", ".join(str(weight) for weight in COLUMN_WEIGHTS)
    conn = sqlite3.connect(core.SQLITE_PATH)
    try:
        conn.row_factory = sqlite3.Row
        matched = conn.execute(
            f"""
            SELECT records.path, records.record_kind AS kind, records.frontmatter_json, {FTS_TABLE}.ids AS ids,
                   bm25({FTS_TABLE}, {weights}) AS score
            FROM {FTS_TABLE} JOIN records ON records.path = {FTS_TABLE}.path
            WHERE {FTS_TABLE} MATCH ?
            """,
            (expression,),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        conn.close()
        raise SearchUnavailableError(f"full-text search is unavailable: {exc}") from exc

    ranked: list[tuple[int, float, str, dict[str, Any]]] = []
    for row in matched:
        record = core.Record(path=core.REPO_ROOT / str(row["path"]), frontmatter=json.loads(row["frontmatter_json"]), body="")
        if structured and not core.record_matches(record, structured):
            continue
        label, reason = core.recall_classification(record, stale_days)
        score = float(row["score"]) * KIND_WEIGHTS.get(str(row["kind"]), 1.0) * (SUPERSEDED_PENALTY if label == "do_not_use" else 1.0)
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
            "snippet": "",
            "corpus": RECORDS_CORPUS,
        }
        ranked.append((0 if exact else 1, score, record.relpath, hit))
    ranked.sort(key=lambda item: item[:3])
    del ranked[limit:]
    try:
        for *_, hit in ranked:
            row = conn.execute(
                f"SELECT snippet({FTS_TABLE}, {BODY_COLUMN}, '', '', ' … ', 24) FROM {FTS_TABLE} WHERE {FTS_TABLE} MATCH ? AND path = ?",
                (expression, hit["path"]),
            ).fetchone()
            hit["snippet"] = " ".join(str(row[0]).split()) if row else ""
    finally:
        conn.close()
    if not structured:
        ranked.extend(corpus_hits(terms, identifiers, limit))
    ranked.sort(key=lambda item: item[:3])
    return [hit for *_, hit in ranked[:limit]]


def corpus_hits(terms: list[str], identifiers: list[str], limit: int) -> list[tuple[int, float, str, dict[str, Any]]]:
    roots = corpus_roots()
    if not roots:
        return []
    conn = sqlite3.connect(core.SQLITE_PATH)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT {CORPUS_TABLE}.corpus AS corpus, {CORPUS_TABLE}.path AS path, {CORPUS_TABLE}.ids AS ids,
                   corpus_docs.title AS title, corpus_docs.kind AS kind, corpus_docs.status AS status, corpus_docs.date AS date,
                   bm25({CORPUS_TABLE}, {", ".join(str(weight) for weight in CORPUS_WEIGHTS)}) AS score,
                   snippet({CORPUS_TABLE}, 5, '', '', ' … ', 24) AS snippet
            FROM {CORPUS_TABLE} JOIN corpus_docs
              ON corpus_docs.corpus = {CORPUS_TABLE}.corpus AND corpus_docs.path = {CORPUS_TABLE}.path
            WHERE {CORPUS_TABLE} MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (match_expression(terms), CANDIDATE_POOL if identifiers else max(limit * 4, 40)),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise SearchUnavailableError(f"full-text search is unavailable: {exc}") from exc
    finally:
        conn.close()
    hits: list[tuple[int, float, str, dict[str, Any]]] = []
    for row in rows:
        root = roots.get(str(row["corpus"]))
        file = root / str(row["path"]) if root else None
        if file is None or file.is_symlink() or not file.is_file():
            continue
        ids = f" {str(row['ids']).lower()} "
        exact = any(f" {identifier} " in ids for identifier in identifiers)
        path = f"{row['corpus']}/{row['path']}"
        hit = {
            "path": path,
            "title": str(row["title"]),
            "kind": str(row["kind"]),
            "status": str(row["status"]),
            "date": str(row["date"]),
            "class": "reference",
            "reason": f"read-only `{row['corpus']}` corpus, not a braingent record",
            "score": round(-float(row["score"]), 3),
            "snippet": " ".join(str(row["snippet"]).split()),
            "corpus": str(row["corpus"]),
            "file": str(file),
        }
        hits.append((0 if exact else 1, float(row["score"]), path, hit))
    return hits


def split_arguments(arguments: list[str]) -> tuple[str, list[str]]:
    words = [argument for argument in arguments if not re.match(r"^[a-z_]+=", argument)]
    return " ".join(words), [argument for argument in arguments if argument not in words]


def search_fused(
    queries: list[str],
    filters: dict[str, list[str]] | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """Merge several wordings of one question by reciprocal rank, so a record any wording finds can surface."""

    queries = list(dict.fromkeys(query for query in queries if query.strip()))
    if len(queries) < 2:
        return search(queries[0] if queries else "", filters, limit=limit)
    fused: dict[str, tuple[float, dict[str, Any]]] = {}
    for query in queries:
        for rank, hit in enumerate(search(query, filters, limit=max(limit * 2, DEFAULT_LIMIT))):
            score, kept = fused.get(hit["path"], (0.0, hit))
            fused[hit["path"]] = (score + 1.0 / (FUSION_K + rank), kept)
    ordered = sorted(fused.items(), key=lambda item: (-item[1][0], item[0]))
    return [hit for _, (_, hit) in ordered[:limit]]


def run_search(
    arguments: list[str],
    output_json: bool = False,
    paths_only: bool = False,
    limit: int = DEFAULT_LIMIT,
    also: list[str] | None = None,
) -> int:
    query, raw_filters = split_arguments(arguments)
    hits = search_fused([query, *(also or [])], core.parse_find_filters(raw_filters), limit=limit)
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

"""Capture a record without duplicating one, and without silently contradicting a decision.

`capture` wraps `scripts/new-record.sh`. Before writing it checks three things:

- the same source at the same revision is already recorded: report that record and write nothing;
- similar records exist: list them, as a prompt to update one instead;
- for a decision, live decisions on the same subject exist: stop until the caller says the new
  decision supersedes one, coexists with one, or is unrelated.

It never edits another record on a guess. Only `--supersedes <path>` changes an existing record.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date
from typing import Any

from braingent import core, search

EXIT_CONFLICT = 3
SIMILAR_LIMIT = 3
CONFLICT_LIMIT = 5
SHARED_WORDS = 2
FRONTMATTER_END = re.compile(r"^---[ \t]*$", re.MULTILINE)


def same_source(records: list[core.Record], source: str, revision: str | None) -> list[core.Record]:
    wanted = revision or ""
    return [
        record
        for record in records
        if core.as_scalar(record.frontmatter.get("source")) == source
        and (core.as_scalar(record.frontmatter.get("source_revision")) if not core.is_nullish(record.frontmatter.get("source_revision")) else "") == wanted
    ]


def subject_tokens(title: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{4,}", title.lower()))


def similar_records(title: str, kind: str, exclude: set[str]) -> list[dict[str, Any]]:
    try:
        hits = search.search(title, {"record_kind": [kind]}, limit=SIMILAR_LIMIT + len(exclude))
    except (ValueError, search.SearchUnavailableError):
        return []
    return [hit for hit in hits if hit["path"] not in exclude][:SIMILAR_LIMIT]


def live_decisions(title: str) -> list[dict[str, Any]]:
    try:
        hits = search.search(title, {"record_kind": ["decision"]}, limit=CONFLICT_LIMIT * 2)
    except (ValueError, search.SearchUnavailableError):
        return []
    wanted = subject_tokens(title)
    return [
        hit for hit in hits if hit["class"] != "do_not_use" and len(wanted & subject_tokens(hit["title"])) >= SHARED_WORDS
    ][:CONFLICT_LIMIT]


def set_frontmatter(text: str, values: dict[str, Any]) -> str:
    """Set top-level frontmatter keys by line, leaving every other line as written."""

    if not text.startswith("---\n"):
        raise ValueError("record has no frontmatter")
    end = FRONTMATTER_END.search(text, 4)
    if end is None:
        raise ValueError("record frontmatter is not closed")
    head, tail = text[4:end.start()], text[end.start():]
    for key, value in values.items():
        line = f"{key}: {json.dumps(value)}"
        existing = re.search(rf"^{re.escape(key)}:.*$", head, re.MULTILINE)
        head = f"{head[:existing.start()]}{line}{head[existing.end():]}" if existing else f"{head}{line}\n"
    return f"---\n{head}{tail}"


def resolve_decision(path_text: str) -> core.Record:
    path = (core.REPO_ROOT / path_text).resolve()
    frontmatter, body, error = core.split_frontmatter(path) if path.is_file() else (None, "", "file not found")
    if error or not frontmatter:
        raise SystemExit(f"{path_text}: {error or 'not a record'}")
    record = core.Record(path=path, frontmatter=frontmatter, body=body)
    if record.kind != "decision":
        raise SystemExit(f"{path_text} is a {record.kind or 'non-record'}, not a decision")
    return record


def run_capture(
    kind: str,
    entity: str,
    title: str,
    output_dir: str,
    *,
    source: str | None = None,
    revision: str | None = None,
    supersedes: str | None = None,
    coexists_with: list[str] | None = None,
    unrelated: bool = False,
    check: bool = False,
    output_json: bool = False,
) -> int:
    coexists_with = coexists_with or []
    records, _ = core.load_records(include_parse_errors=False)
    result: dict[str, Any] = {"status": "clear", "path": None, "exists": [], "similar": [], "conflicts": []}

    def finish(code: int) -> int:
        if output_json:
            print(json.dumps(result, indent=2))
        elif result["path"]:
            print(result["path"])
        return code

    if source:
        existing = same_source(records, source, revision)
        if existing:
            result.update(status="exists", path=existing[0].relpath, exists=[record.relpath for record in existing])
            print(f"already captured: {existing[0].relpath}", file=sys.stderr)
            return finish(0)

    decided = {resolve_decision(path).relpath for path in [*([supersedes] if supersedes else []), *coexists_with]}
    result["similar"] = similar_records(title, kind, exclude=set())
    if result["similar"]:
        print("similar records (update one of these if it is the same thing):", file=sys.stderr)
        for hit in result["similar"]:
            print(f"- {hit['path']} [{hit['status']}] {hit['title']}", file=sys.stderr)

    if kind == "decision" and not unrelated:
        result["conflicts"] = [hit for hit in live_decisions(title) if hit["path"] not in decided]
        if result["conflicts"] and not decided:
            result["status"] = "conflict"
            print("live decisions on a similar subject. Say how the new one relates before capturing:", file=sys.stderr)
            for hit in result["conflicts"]:
                print(f"- {hit['path']} [{hit['status']}] {hit['title']}", file=sys.stderr)
            print("rerun with --supersedes <path>, --coexists-with <path>, or --unrelated", file=sys.stderr)
            return finish(EXIT_CONFLICT)

    if check:
        return finish(0)

    script = core.REPO_ROOT / "scripts" / "new-record.sh"
    if not script.is_file():
        raise SystemExit(f"capture needs {script.relative_to(core.REPO_ROOT)}; run `braingent update` to restore it")
    created = subprocess.run([str(script), kind, entity, title, output_dir], capture_output=True, text=True, check=False, cwd=core.REPO_ROOT)
    if created.returncode != 0:
        sys.stderr.write(created.stderr)
        return created.returncode
    path = (core.REPO_ROOT / created.stdout.strip().splitlines()[-1]).resolve()
    relpath = path.relative_to(core.REPO_ROOT).as_posix()

    values: dict[str, Any] = {}
    if source:
        values.update(source=source, source_revision=revision, captured_at=date.today().isoformat())
    if supersedes:
        values["supersedes"] = resolve_decision(supersedes).relpath
    if coexists_with:
        values["coexists_with"] = [resolve_decision(item).relpath for item in coexists_with]
    if values:
        path.write_text(set_frontmatter(path.read_text(encoding="utf-8"), values), encoding="utf-8")
    if supersedes:
        old = resolve_decision(supersedes)
        old.path.write_text(
            set_frontmatter(old.path.read_text(encoding="utf-8"), {"status": "superseded", "superseded_by": relpath}), encoding="utf-8"
        )
        print(f"marked superseded: {old.relpath}", file=sys.stderr)

    result.update(status="created", path=relpath)
    return finish(0)

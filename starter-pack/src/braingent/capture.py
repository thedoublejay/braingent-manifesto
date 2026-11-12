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
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

from braingent import core, daily, search

EXIT_CONFLICT = 3
SIMILAR_LIMIT = 3
SHARED_WORDS = 2
FRONTMATTER_END = re.compile(r"^---[ \t]*$", re.MULTILINE)


def inside_root(value: str | Path) -> Path:
    path = (core.REPO_ROOT / value).resolve()
    if not path.is_relative_to(core.REPO_ROOT.resolve()):
        raise SystemExit(f"path escapes the memory root: {value}")
    return path


def record_lock() -> Any:
    return daily.locked(inside_root(".braingent/records.lock"))


def backup_file(path: Path) -> Path:
    path = inside_root(path)
    content = path.read_bytes()
    mode = path.stat().st_mode & 0o777
    index = 1
    while True:
        backup = path.with_name(f"{path.name}.bak" + (f"-{index}" if index > 1 else ""))
        try:
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
        except FileExistsError:
            index += 1
            continue
        print(f"backup: {backup.relative_to(core.REPO_ROOT)}", file=sys.stderr)
        return backup


def replace_bytes(path: Path, content: bytes) -> None:
    path = inside_root(path)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        if path.exists():
            shutil.copymode(path, temporary_path)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


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


def live_decisions(title: str, records: list[core.Record]) -> list[dict[str, Any]]:
    wanted = subject_tokens(title)
    hits: list[dict[str, Any]] = []
    for record in records:
        if (
            record.kind != "decision"
            or record.status not in {"accepted", "active", "proposed"}
            or not core.is_nullish(record.frontmatter.get("superseded_by"))
            or len(wanted & subject_tokens(record.title)) < SHARED_WORDS
        ):
            continue
        label, reason = core.recall_classification(record, core.CONFIG.recall_stale_days)
        hits.append({
            "path": record.relpath, "title": record.title, "kind": record.kind, "status": record.status,
            "date": record.date_sort, "class": label, "reason": reason, "score": 0.0, "snippet": "", "corpus": "records",
        })
    return hits


def set_frontmatter(text: str, values: dict[str, Any]) -> str:
    """Set top-level frontmatter keys by line, leaving every other line as written."""

    if not text.startswith("---\n"):
        raise ValueError("record has no frontmatter")
    end = FRONTMATTER_END.search(text, 4)
    if end is None:
        raise ValueError("record frontmatter is not closed")
    head, tail = text[4:end.start()], text[end.start():]
    for key, value in values.items():
        line = f"{key}: {json.dumps(value)}\n"
        parsed = yaml.compose(head)
        if not isinstance(parsed, yaml.MappingNode):
            raise ValueError("record frontmatter is not a mapping")
        existing = next(((name, node) for name, node in parsed.value if name.value == key), None)
        if existing:
            name, node = existing
            stop = max(node.end_mark.index, head.find("\n", name.start_mark.index) + 1)
            if stop and head[stop - 1] != "\n":
                newline = head.find("\n", stop)
                stop = newline + 1 if newline >= 0 else len(head)
            head = f"{head[:name.start_mark.index]}{line}{head[stop:]}"
        else:
            head = f"{head}{line}"
    yaml.safe_load(head)
    return f"---\n{head}{tail}"


def resolve_decision(path_text: str) -> core.Record:
    path = inside_root(path_text)
    frontmatter, body, error = core.split_frontmatter(path) if path.is_file() else (None, "", "file not found")
    if error or not frontmatter:
        raise SystemExit(f"{path_text}: {error or 'not a record'}")
    record = core.Record(path=path, frontmatter=frontmatter, body=body)
    if record.kind != "decision":
        raise SystemExit(f"{path_text} is a {record.kind or 'non-record'}, not a decision")
    return record


def _run_capture(
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
    destination = inside_root(output_dir)
    if destination.exists() and not destination.is_dir():
        raise SystemExit(f"output directory is not a directory: {output_dir}")
    scan_roots = [inside_root(name) for name in core.load_taxonomy().get("record_scan_roots", [])]
    if not any(destination.is_relative_to(root) for root in scan_roots):
        raise SystemExit("output directory must be inside a taxonomy record_scan_roots directory")
    if kind != "decision" and (supersedes or coexists_with or unrelated):
        raise SystemExit("decision relations require kind=decision")
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
        result["conflicts"] = [hit for hit in live_decisions(title, records) if hit["path"] not in decided]
        if result["conflicts"]:
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
    old = resolve_decision(supersedes) if supersedes else None
    if old:
        backup_file(old.path)
    created = subprocess.run(
        [str(script), kind, entity, title, str(destination)], capture_output=True, text=True, check=False, cwd=core.REPO_ROOT,
        env={**os.environ, "BRAINGENT_TIMEZONE": core.CONFIG.daily_timezone or "UTC"},
    )
    if created.returncode != 0:
        sys.stderr.write(created.stderr)
        return created.returncode
    path = inside_root(created.stdout.strip().splitlines()[-1])
    relpath = path.relative_to(core.REPO_ROOT).as_posix()

    values: dict[str, Any] = {}
    if source:
        values.update(source=source, source_revision=revision, captured_at=core.today_iso())
    if supersedes:
        values["supersedes"] = resolve_decision(supersedes).relpath
    if coexists_with:
        values["coexists_with"] = [resolve_decision(item).relpath for item in coexists_with]
    try:
        if values:
            replace_bytes(path, set_frontmatter(path.read_text(encoding="utf-8"), values).encode("utf-8"))
        if old:
            replace_bytes(
                old.path, set_frontmatter(old.path.read_text(encoding="utf-8"), {"status": "superseded", "superseded_by": relpath}).encode("utf-8")
            )
            print(f"marked superseded: {old.relpath}", file=sys.stderr)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        path.unlink(missing_ok=True)
        raise SystemExit(f"capture failed; new record removed and previous records unchanged: {exc}") from exc

    result.update(status="created", path=relpath)
    return finish(0)


def run_capture(
    kind: str, entity: str, title: str, output_dir: str, *, source: str | None = None, revision: str | None = None,
    supersedes: str | None = None, coexists_with: list[str] | None = None, unrelated: bool = False,
    check: bool = False, output_json: bool = False,
) -> int:
    def run() -> int:
        return _run_capture(
            kind, entity, title, output_dir, source=source, revision=revision, supersedes=supersedes,
            coexists_with=coexists_with, unrelated=unrelated, check=check, output_json=output_json,
        )

    try:
        if check:
            return run()
        with record_lock():
            return run()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise SystemExit(f"capture failed: {exc}") from exc

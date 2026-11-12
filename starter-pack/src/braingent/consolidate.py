"""Consolidation proposals: mechanical tidy-ups a person or agent reviews before anything changes.

`braingent dream` only reads. Each proposal names a record, the evidence, and the exact frontmatter
change if there is one. `--apply <id>` makes that change after regenerating the proposal, so a record
edited since the proposal was listed is never overwritten. `--reject <id>` hides one for good.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from braingent import capture, core

REJECTED_PATH = Path(".braingent") / "proposals-rejected.json"
DEFAULT_LIMIT = 20
LINK_FIELDS = ("supersedes", "superseded_by", "coexists_with", "related_records")


@dataclass(frozen=True)
class Proposal:
    id: str
    kind: str
    path: str
    why: str
    change: dict[str, Any] | None
    date: str


def proposal(kind: str, record: core.Record, why: str, change: dict[str, Any] | None = None) -> Proposal:
    digest = hashlib.sha256(json.dumps([kind, record.relpath, why, change], sort_keys=True).encode("utf-8")).hexdigest()[:10]
    return Proposal(digest, kind, record.relpath, why, change, record.date_sort)


def allows_superseded(record: core.Record, taxonomy: dict[str, Any]) -> bool:
    return "superseded" in (taxonomy.get("statuses", {}).get(record.kind) or [])


def build(records: list[core.Record], taxonomy: dict[str, Any]) -> list[Proposal]:
    by_path = {record.path.resolve(): record for record in records}
    found: list[Proposal] = []

    def target(record: core.Record, value: Any) -> core.Record | None:
        resolved = core.resolve_record_ref(value, source=record.path)
        return by_path.get(resolved.resolve()) if resolved else None

    for record in records:
        fm = record.frontmatter
        for field in LINK_FIELDS:
            for value in core.as_list(fm.get(field)):
                if not core.is_nullish(value) and target(record, value) is None:
                    found.append(proposal("broken-link", record, f"`{field}` points at `{core.as_scalar(value)}`, which is not a record"))

        newer = target(record, fm.get("superseded_by")) if not core.is_nullish(fm.get("superseded_by")) else None
        if newer and record.status != "superseded" and allows_superseded(record, taxonomy):
            found.append(
                proposal(
                    "mark-superseded", record,
                    f"`superseded_by` names `{newer.relpath}` but status is still `{record.status}`", {"status": "superseded"},
                )
            )

        older = target(record, fm.get("supersedes")) if not core.is_nullish(fm.get("supersedes")) else None
        if older and core.is_nullish(older.frontmatter.get("superseded_by")):
            change: dict[str, Any] = {"superseded_by": record.relpath}
            if allows_superseded(older, taxonomy):
                change["status"] = "superseded"
            found.append(proposal("link-superseded-by", older, f"`{record.relpath}` says it supersedes this record, which does not point back", change))

    by_source: dict[tuple[str, str], list[core.Record]] = {}
    for record in records:
        source = core.as_scalar(record.frontmatter.get("source")) if not core.is_nullish(record.frontmatter.get("source")) else ""
        if source and record.kind != "summary":
            revision = record.frontmatter.get("source_revision")
            by_source.setdefault((source, "" if core.is_nullish(revision) else core.as_scalar(revision)), []).append(record)
    for (source, revision), group in by_source.items():
        for extra in sorted(group, key=lambda item: item.relpath)[1:]:
            first = min(group, key=lambda item: item.relpath)
            label = f"`{source}` at `{revision}`" if revision else f"`{source}`"
            found.append(proposal("duplicate-source", extra, f"records the same source as `{first.relpath}`: {label}"))

    already_linked = {item.path for item in found if item.kind == "link-superseded-by"}
    for issue in core.validate_decision_conflicts(records):
        record = by_path.get(issue.path.resolve())
        if record and record.relpath not in already_linked:
            found.append(proposal("state-relation", record, f"{issue.message.split(';')[0]}; set `superseded_by` or `coexists_with`"))

    return sorted(found, key=lambda item: (item.date, item.path, item.kind), reverse=True)


def load_rejected() -> set[str]:
    path = core.REPO_ROOT / REJECTED_PATH
    if not path.is_file():
        return set()
    try:
        return {str(item) for item in json.loads(path.read_text(encoding="utf-8"))}
    except ValueError as exc:
        raise SystemExit(f"{REJECTED_PATH} is not valid JSON: {exc}") from exc


def proposals() -> list[Proposal]:
    records, _ = core.load_records(include_parse_errors=False)
    rejected = load_rejected()
    return [item for item in build(records, core.load_taxonomy()) if item.id not in rejected]


def apply(ids: list[str]) -> int:
    current = {item.id: item for item in proposals()}
    failed = 0
    for wanted in ids:
        item = current.get(wanted)
        if item is None:
            print(f"{wanted}: no longer applies; run `braingent dream` again", flush=True)
            failed += 1
        elif item.change is None:
            print(f"{wanted}: needs a person or agent to decide; nothing to apply automatically")
            failed += 1
        else:
            path = core.REPO_ROOT / item.path
            path.write_text(capture.set_frontmatter(path.read_text(encoding="utf-8"), item.change), encoding="utf-8")
            print(f"{wanted}: applied to {item.path}")
    return 1 if failed else 0


def reject(ids: list[str]) -> int:
    path = core.REPO_ROOT / REJECTED_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(load_rejected() | set(ids)), indent=2) + "\n", encoding="utf-8")
    print(f"rejected {len(ids)}; they will not be proposed again")
    return 0


def run(limit: int = DEFAULT_LIMIT, output_json: bool = False, apply_ids: list[str] | None = None, reject_ids: list[str] | None = None) -> int:
    if reject_ids:
        return reject(reject_ids)
    if apply_ids:
        return apply(apply_ids)
    found = proposals()
    shown = found[:limit]
    if output_json:
        print(json.dumps({"total": len(found), "proposals": [asdict(item) for item in shown]}, indent=2))
        return 0
    print(f"{len(found)} proposals, showing {len(shown)}. Nothing has been changed.")
    for item in shown:
        change = "; change: " + ", ".join(f"{key}: {value}" for key, value in item.change.items()) if item.change else "; needs a decision"
        print(f"- {item.id} {item.kind} `{item.path}`: {item.why}{change}")
    return 0

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

Confidence = Literal["high", "medium", "low", "unresolved"]
Surface = Literal["frontend", "backend"]
CitationKind = Literal["file_span", "ac", "graph_edge", "command"]

FRONTEND_SOURCE_KINDS = {
    "route",
    "page",
    "component",
    "static_link",
    "dynamic_link",
    "feature_flag",
    "permission_gate",
    "nearby_test",
}

BACKEND_SOURCE_KINDS = {
    "endpoint",
    "graphql_op",
    "webhook",
    "service",
    "use_case",
    "table",
    "migration",
    "projection",
    "dto",
    "queue",
    "event",
    "consumer",
    "job",
    "auth",
    "permission",
    "validation",
    "audit",
    "notification",
    "log",
    "metric",
    "contract",
}

ALL_SOURCE_KINDS = FRONTEND_SOURCE_KINDS | BACKEND_SOURCE_KINDS | {"unknown"}


class EvidenceCitation(TypedDict, total=False):
    kind: CitationKind
    repo: str
    path: str
    line_start: int
    line_end: int
    ac_id: str
    edge_id: str
    command: str


class EvidenceRow(TypedDict):
    row_id: str
    surface: Surface
    source_kind: str
    symbol: str
    citations: list[EvidenceCitation]
    callers: list[str]
    consumers: list[str]
    confidence: Confidence
    truncated: bool
    unsupported: bool
    token_estimate: int
    notes: list[str]


class ManifestSummary(TypedDict):
    evidence_pack_version: str
    generated_at: str
    base_ref: str
    head_ref: str
    total_rows: int
    truncated_rows: int
    dropped_kinds: list[str]
    budget_tokens: int
    used_tokens: int
    confidence_histogram: dict[str, int]
    unsupported_surfaces: list[str]


class QAAcRow(TypedDict):
    ac_id: str
    text: str


class QAEvidencePack(TypedDict):
    manifest_summary: ManifestSummary
    rows: list[EvidenceRow]
    acs: NotRequired[list[QAAcRow]]


def load_pack(path: Path) -> QAEvidencePack:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("qa-evidence pack must be a JSON object")
    pack = normalize_pack(raw)
    warnings = validate_pack(pack)
    if warnings:
        raise ValueError("; ".join(warnings))
    return pack


def normalize_pack(raw: dict[str, Any]) -> QAEvidencePack:
    if raw.get("schema_version") != "qa-evidence.v1":
        return raw  # type: ignore[return-value]

    canonical_rows = raw.get("rows")
    if not isinstance(canonical_rows, list):
        return raw  # type: ignore[return-value]

    rows = [
        canonical_row_to_legacy(row)
        for row in canonical_rows
        if isinstance(row, dict)
    ]
    summary = canonical_manifest_to_legacy(raw, rows)
    pack: QAEvidencePack = {
        "manifest_summary": summary,
        "rows": rows,
    }
    acs = raw.get("acs")
    if isinstance(acs, list):
        pack["acs"] = acs  # type: ignore[typeddict-item]
    return pack


def canonical_manifest_to_legacy(raw: dict[str, Any], rows: list[EvidenceRow]) -> ManifestSummary:
    summary = raw.get("manifest_summary") if isinstance(raw.get("manifest_summary"), dict) else {}
    truncated = bool(summary.get("truncated"))
    omitted_rows = summary.get("omitted_rows")
    dropped_kinds = summary.get("dropped_kinds") if isinstance(summary.get("dropped_kinds"), list) else []
    gaps = raw.get("gaps") if isinstance(raw.get("gaps"), list) else []
    unsupported_surfaces = [
        str(gap.get("kind"))
        for gap in gaps
        if isinstance(gap, dict) and gap.get("blocks_complete_coverage") and gap.get("kind")
    ]
    histogram = {"high": 0, "medium": 0, "low": 0, "unresolved": 0}
    for row in rows:
        histogram[row["confidence"]] += 1
        if row["unsupported"] and row["source_kind"] not in unsupported_surfaces:
            unsupported_surfaces.append(row["source_kind"])

    truncated_rows = len([row for row in rows if row["truncated"]])
    if truncated:
        if isinstance(omitted_rows, int) and omitted_rows > 0:
            truncated_rows = max(truncated_rows, omitted_rows)
        else:
            truncated_rows = max(truncated_rows, 1)

    return {
        "evidence_pack_version": str(raw.get("schema_version") or "qa-evidence.v1"),
        "generated_at": "generated-by-gather-step",
        "base_ref": str(raw.get("base_ref") or ""),
        "head_ref": str(raw.get("head_ref") or ""),
        "total_rows": len(rows),
        "truncated_rows": truncated_rows,
        "dropped_kinds": [str(kind) for kind in dropped_kinds],
        "budget_tokens": 0,
        "used_tokens": sum(row["token_estimate"] for row in rows),
        "confidence_histogram": histogram,
        "unsupported_surfaces": unsupported_surfaces,
    }


def canonical_row_to_legacy(row: dict[str, Any]) -> EvidenceRow:
    kind = str(row.get("kind") or "unknown")
    source = str(row.get("source") or "unknown")
    citation = row.get("citation") if isinstance(row.get("citation"), dict) else {}
    subject = row.get("subject") if isinstance(row.get("subject"), dict) else {}
    support = row.get("support") if isinstance(row.get("support"), dict) else {}
    source_kind = canonical_source_kind(kind, citation, subject)
    confidence = confidence_from_support(support)
    symbol = canonical_symbol(kind, citation, subject)
    notes = canonical_notes(source, kind, subject, support)
    return {
        "row_id": str(row.get("id") or ""),
        "surface": canonical_surface(source_kind, citation, subject),
        "source_kind": source_kind,
        "symbol": symbol,
        "citations": [canonical_citation_to_legacy(citation)],
        "callers": [],
        "consumers": [],
        "confidence": confidence,
        "truncated": kind == "truncated_repos",
        "unsupported": confidence == "unresolved" or kind in {"unresolved_possible_repo", "truncated_repos"},
        "token_estimate": max(1, len(" ".join([symbol, *notes]).split())),
        "notes": notes,
    }


def canonical_source_kind(kind: str, citation: dict[str, Any], subject: dict[str, Any]) -> str:
    mapping = {
        "route_definition": "route",
        "route_handler": "route",
        "route_caller": "route",
        "event_definition": "event",
        "event_producer": "event",
        "event_consumer": "consumer",
        "payload_contract": "contract",
        "existing_test_signal": "nearby_test",
        "feature_flag": "feature_flag",
        "cross_repo_caller": "consumer",
        "confirmed_downstream_repo": "consumer",
        "probable_downstream_repo": "consumer",
        "unresolved_possible_repo": "consumer",
        "truncated_repos": "consumer",
        "decorator": "auth",
        "contract_alignment": "contract",
        "deployment_touchpoint": "job",
    }
    if kind in mapping:
        return mapping[kind]
    surface = str(subject.get("surface") or subject.get("category") or "").lower()
    return infer_source_kind(" ".join([kind, str(citation.get("path") or "")]), surface)


def canonical_surface(source_kind: str, citation: dict[str, Any], subject: dict[str, Any]) -> Surface:
    if source_kind in FRONTEND_SOURCE_KINDS:
        return "frontend"
    if source_kind in BACKEND_SOURCE_KINDS:
        return "backend"
    path = str(citation.get("path") or "").lower()
    surface = str(subject.get("surface") or "").lower()
    if any(part in path for part in (".tsx", ".jsx", "/frontend", "frontend/")) or surface in {
        "frontend",
        "page",
        "component",
        "feature_flag",
        "test",
    }:
        return "frontend"
    return "backend"


def canonical_symbol(kind: str, citation: dict[str, Any], subject: dict[str, Any]) -> str:
    for key in ("name", "reason"):
        value = str(subject.get(key) or "").strip()
        if value:
            return value[:120]
    symbol_name = str(citation.get("symbol_name") or "").strip()
    if symbol_name:
        return symbol_name
    route_path = str(citation.get("route_path") or "").strip()
    if route_path:
        method = str(citation.get("route_method") or "").strip()
        return f"{method} {route_path}".strip()
    event_target = str(citation.get("event_target") or "").strip()
    if event_target:
        return event_target
    path = str(citation.get("path") or "").strip()
    if path:
        line = citation.get("line")
        return f"{path}:{line}" if line else path
    repo = str(citation.get("repo") or "").strip()
    return repo or kind


def canonical_notes(
    source: str,
    kind: str,
    subject: dict[str, Any],
    support: dict[str, Any],
) -> list[str]:
    notes = [f"source={source}", f"kind={kind}"]
    category = str(subject.get("category") or "").strip()
    if category:
        notes.append(f"category={category}")
    reason = str(subject.get("reason") or "").strip()
    if reason:
        notes.append(reason)
    method = str(support.get("method") or "").strip()
    if method:
        notes.append(f"support={method}")
    return notes


def canonical_citation_to_legacy(citation: dict[str, Any]) -> EvidenceCitation:
    kind = str(citation.get("kind") or "")
    if kind in {"file_line", "symbol"}:
        line = citation.get("line")
        legacy: EvidenceCitation = {
            "kind": "file_span",
            "repo": str(citation.get("repo") or ""),
            "path": str(citation.get("path") or ""),
        }
        if isinstance(line, int):
            legacy["line_start"] = line
            legacy["line_end"] = line
        return legacy
    if kind == "route":
        method = str(citation.get("route_method") or "").strip()
        path = str(citation.get("route_path") or "").strip()
        return {"kind": "command", "command": f"route {method} {path}".strip()}
    if kind == "event":
        return {"kind": "command", "command": f"event {citation.get('event_target') or ''}".strip()}
    if kind == "repo":
        return {"kind": "command", "command": f"repo {citation.get('repo') or ''}".strip()}
    return {"kind": "command", "command": json.dumps(citation, sort_keys=True)}


def confidence_from_support(support: dict[str, Any]) -> Confidence:
    score = support.get("score")
    if isinstance(score, int):
        if score >= 800:
            return "high"
        if score >= 500:
            return "medium"
        if score > 0:
            return "low"
        return "unresolved"
    if support.get("method"):
        return "low"
    return "medium"


def validate_pack(raw: object) -> list[str]:
    warnings: list[str] = []
    if not isinstance(raw, dict):
        return ["qa-evidence pack must be a JSON object"]
    summary = raw.get("manifest_summary")
    rows = raw.get("rows")
    if not isinstance(summary, dict):
        warnings.append("manifest_summary is required")
    if not isinstance(rows, list):
        warnings.append("rows must be a list")
        return warnings
    if isinstance(summary, dict):
        for key in (
            "evidence_pack_version",
            "generated_at",
            "base_ref",
            "head_ref",
            "total_rows",
            "truncated_rows",
            "dropped_kinds",
            "budget_tokens",
            "used_tokens",
            "confidence_histogram",
            "unsupported_surfaces",
        ):
            if key not in summary:
                warnings.append(f"manifest_summary.{key} is required")
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            warnings.append(f"rows[{index}] must be an object")
            continue
        row_id = str(row.get("row_id") or "")
        if not row_id:
            warnings.append(f"rows[{index}].row_id is required")
        elif row_id in seen:
            warnings.append(f"rows[{index}].row_id duplicates {row_id}")
        seen.add(row_id)
        if row.get("surface") not in {"frontend", "backend"}:
            warnings.append(f"rows[{index}].surface must be frontend or backend")
        if str(row.get("source_kind") or "") not in ALL_SOURCE_KINDS:
            warnings.append(f"rows[{index}].source_kind is unknown: {row.get('source_kind')}")
        if row.get("confidence") not in {"high", "medium", "low", "unresolved"}:
            warnings.append(f"rows[{index}].confidence must be high, medium, low, or unresolved")
        citations = row.get("citations")
        if not isinstance(citations, list) or not citations:
            warnings.append(f"rows[{index}].citations must contain at least one citation")
    if isinstance(summary, dict):
        total_rows = summary.get("total_rows")
        if isinstance(total_rows, int) and total_rows != len(rows):
            warnings.append("manifest_summary.total_rows must match rows length")
    return warnings


def row_to_text(row: EvidenceRow) -> str:
    notes = "; ".join(row.get("notes") or [])
    callers = ", ".join(row.get("callers") or [])
    consumers = ", ".join(row.get("consumers") or [])
    details = [
        f"{row['surface']} {row['source_kind']}: {row['symbol']}",
        f"confidence={row['confidence']}",
    ]
    if callers:
        details.append(f"callers={callers}")
    if consumers:
        details.append(f"consumers={consumers}")
    if row.get("unsupported"):
        details.append("unsupported=true")
    if row.get("truncated"):
        details.append("truncated=true")
    if notes:
        details.append(f"notes={notes}")
    return " | ".join(details)


def command_to_row(
    row_id: str,
    command: str,
    text: str,
    *,
    ok: bool,
    base_ref: str,
    head_ref: str,
) -> EvidenceRow:
    source_kind = infer_source_kind(command, text)
    surface: Surface = "frontend" if source_kind in FRONTEND_SOURCE_KINDS else "backend"
    unsupported = not ok
    truncated = "[truncated]" in text
    confidence: Confidence = "low" if ok else "unresolved"
    return {
        "row_id": row_id,
        "surface": surface,
        "source_kind": source_kind,
        "symbol": infer_symbol(command, text),
        "citations": [{"kind": "command", "command": command}],
        "callers": [],
        "consumers": [],
        "confidence": confidence,
        "truncated": truncated,
        "unsupported": unsupported,
        "token_estimate": max(1, len(text.split())),
        "notes": [text.strip()] if text.strip() else [],
    }


def infer_source_kind(command: str, text: str) -> str:
    combined = f"{command}\n{text}".lower()
    if "projection-impact" in combined or "projection" in combined:
        return "projection"
    if "route" in combined or "page" in combined:
        return "route"
    if "component" in combined:
        return "component"
    if "graphql" in combined:
        return "graphql_op"
    if "endpoint" in combined or "api" in combined:
        return "endpoint"
    if "event" in combined or "subscriber" in combined:
        return "event"
    if "consumer" in combined or "downstream" in combined:
        return "consumer"
    if "contract" in combined or "dto" in combined:
        return "contract"
    if "test" in combined or "spec" in combined:
        return "nearby_test"
    return "unknown"


def infer_symbol(command: str, text: str) -> str:
    for token in command.split():
        if token and not token.startswith("-") and token not in {"gather-step", "search", "pack", "impact"}:
            if "/" not in token or token.startswith(("/", "./", "../")):
                continue
            return token
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    return first_line[:80] or command


def build_manifest(
    rows: list[EvidenceRow],
    *,
    base_ref: str,
    head_ref: str,
    budget_tokens: int,
) -> ManifestSummary:
    histogram = {"high": 0, "medium": 0, "low": 0, "unresolved": 0}
    unsupported_surfaces: list[str] = []
    for row in rows:
        histogram[row["confidence"]] += 1
        if row["unsupported"] and row["source_kind"] not in unsupported_surfaces:
            unsupported_surfaces.append(row["source_kind"])
    return {
        "evidence_pack_version": "0.1-draft",
        "generated_at": "generated-by-adapter",
        "base_ref": base_ref,
        "head_ref": head_ref,
        "total_rows": len(rows),
        "truncated_rows": len([row for row in rows if row["truncated"]]),
        "dropped_kinds": [],
        "budget_tokens": budget_tokens,
        "used_tokens": sum(row["token_estimate"] for row in rows),
        "confidence_histogram": histogram,
        "unsupported_surfaces": unsupported_surfaces,
    }

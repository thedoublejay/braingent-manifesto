from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / ".test-plans"
DEFAULT_GATHER_BINARY = "gather-step"
# QA plans are intentionally verbose; default high and make truncation explicit.
DEFAULT_BUDGET_TOKENS = 160_000
DEFAULT_EVIDENCE_BUDGET = DEFAULT_BUDGET_TOKENS * 4
EMIT_EXTENSIONS = {
    "markdown": ".md",
    "xray-json": ".xray.json",
    "testrail-csv": ".testrail.csv",
    "gherkin": ".feature",
}

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from qa_evidence import QAEvidencePack, build_manifest, command_to_row, load_pack, normalize_pack, row_to_text


@dataclass(frozen=True)
class SourceDoc:
    label: str
    path: str
    text: str


@dataclass(frozen=True)
class AcceptanceCriterion:
    ident: str
    text: str
    source: str


@dataclass
class EvidenceItem:
    label: str
    command: str
    text: str
    ok: bool
    evidence_row_id: str | None = None


@dataclass
class Scenario:
    ident: str
    title: str
    classification: str
    case_type: str
    priority: str
    sources: list[str]
    preconditions: list[str]
    steps: list[str]
    expected_result: str
    data_variations: list[str]
    automation_candidate: str
    gaps: list[str] = field(default_factory=list)


@dataclass
class GenerationInput:
    ticket_key: str
    ticket: SourceDoc
    sources: list[SourceDoc]
    acceptance_criteria: list[AcceptanceCriterion]
    implementation_state: str
    no_diff: bool
    base: str | None
    head: str | None
    memory_records: list[dict[str, Any]]
    gather_evidence: list[EvidenceItem]
    evidence_pack: QAEvidencePack | None
    assumptions: list[str]
    gaps: list[str]


@dataclass(frozen=True)
class MemoryLookupResult:
    records: list[dict[str, Any]]
    warnings: list[str]


class InputError(ValueError):
    pass


def looks_like_missing_path(value: str) -> bool:
    stripped = value.strip()
    if not stripped or "\n" in value:
        return False
    if stripped.startswith(("./", "../", "~/", ".\\", "..\\", "~\\", "\\\\")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", stripped):
        return True
    suffix = Path(stripped).suffix
    return bool(suffix and suffix[1:].isalpha())


def read_source(value: str, label: str) -> SourceDoc:
    path = Path(value).expanduser()
    if path.exists() and path.is_file():
        return SourceDoc(label=label, path=str(path), text=path.read_text(encoding="utf-8"))
    if looks_like_missing_path(value):
        raise InputError(f"{label} path does not exist: {value}")
    return SourceDoc(label=label, path="inline", text=value)


def evidence_budget_bytes(args: argparse.Namespace) -> int:
    if args.evidence_budget_bytes is not None:
        return max(1, int(args.evidence_budget_bytes))
    return max(1, int(args.budget_tokens)) * 4


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "test-plan"


def short_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        stripped = re.sub(r"^(title|summary)\s*:\s*", "", stripped, flags=re.I)
        return stripped[:120]
    return fallback


def strip_marker(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^\s*[-*]\s+\[[ xX]\]\s+", "", line)
    line = re.sub(r"^\s*[-*]\s+", "", line)
    line = re.sub(r"^\s*\d+[.)]\s+", "", line)
    line = re.sub(r"^\s*AC[-_\s]*(\d+)[:.)-]\s*", "", line, flags=re.I)
    return line.strip()


def markdown_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or "|" not in stripped[1:]:
        return []
    cells = [cell.strip() for cell in stripped.strip("|").split("|")]
    if not cells:
        return []
    if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
        return []
    return cells


def acceptance_candidate_from_table(cells: list[str]) -> str:
    normalized_cells = [strip_marker(cell) for cell in cells]
    lower_cells = [cell.lower() for cell in normalized_cells]
    if any(cell in {"#", "scenario", "expected behavior", "expected result"} for cell in lower_cells):
        return ""
    if {"given", "when", "then"}.issubset(set(lower_cells[:3])):
        return ""
    if len(normalized_cells) >= 3 and normalized_cells[0].isdigit():
        scenario = normalized_cells[1]
        expected = normalized_cells[2]
        if scenario and expected:
            return f"{scenario} -> {expected}"
    if len(normalized_cells) >= 3:
        given = normalized_cells[0]
        when = normalized_cells[1]
        then = normalized_cells[2]
        if given and when and then:
            return f"Given {given}; when {when}; then {then}"
    return ""


def extract_acceptance_criteria(sources: list[SourceDoc]) -> list[AcceptanceCriterion]:
    criteria: list[AcceptanceCriterion] = []
    seen: set[str] = set()

    for source in sources:
        lines = source.text.splitlines()
        section: str | None = None
        acceptance_candidates: list[str] = []
        requirement_candidates: list[str] = []
        for line in lines:
            stripped = line.strip()
            if re.match(r"^#{1,6}\s+", stripped):
                if re.search(r"acceptance\s+criteria|success\s+criteria", stripped, re.I):
                    section = "acceptance"
                elif re.search(r"requirements?", stripped, re.I):
                    section = "requirements"
                else:
                    section = None
                continue

            explicit = re.match(r"^\s*(?:[-*]\s+)?AC[-_\s]*(\d+)[:.)-]\s*(.+)", line, re.I)
            bullet = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.+)", line)
            table_cells = markdown_table_cells(line) if section in {"acceptance", "requirements"} else []
            candidate = ""
            if explicit:
                candidate = explicit.group(2)
            elif table_cells:
                candidate = acceptance_candidate_from_table(table_cells)
            elif section in {"acceptance", "requirements"} and bullet:
                candidate = bullet.group(1)
            elif section in {"acceptance", "requirements"} and re.match(
                r"^\s*(given|when|then|must|should|verify|ensure)\b", stripped, re.I
            ):
                candidate = stripped

            if candidate:
                target = acceptance_candidates if explicit or section == "acceptance" else requirement_candidates
                target.append(candidate)

        source_candidates = acceptance_candidates or requirement_candidates
        for candidate in source_candidates:
            normalized = strip_marker(candidate)
            if len(normalized) < 8:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            criteria.append(
                AcceptanceCriterion(
                    ident=f"AC-{len(criteria) + 1}",
                    text=normalized,
                    source=source.label,
                )
            )

    return criteria


def line_has_product_intent(text: str) -> bool:
    if len(text.strip()) < 14:
        return False
    return bool(
        re.search(
            r"\b(user|admin|customer|reviewer|lead|system|page|api|workflow|feature|should|must|can|when|display|save|create|update|delete|filter|search|sort|preserve|show|hide|allow|prevent)\b",
            text,
            re.I,
        )
    )


def extract_product_requirements(
    sources: list[SourceDoc],
    existing: list[AcceptanceCriterion],
    include_ticket: bool,
) -> list[AcceptanceCriterion]:
    requirements: list[AcceptanceCriterion] = []
    seen = {criterion.text.lower() for criterion in existing}
    counter = 1

    for source in sources:
        if source.label == "Ticket" and not include_ticket:
            continue
        in_ac_section = False
        for line in source.text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^#{1,6}\s+", stripped):
                in_ac_section = bool(
                    re.search(r"acceptance\s+criteria|success\s+criteria|requirements?", stripped, re.I)
                )
                continue
            if in_ac_section:
                continue
            if re.match(r"^\s*(?:[-*]\s+)?AC[-_\s]*\d+[:.)-]\s*", line, re.I):
                continue
            candidate = strip_marker(stripped)
            if not line_has_product_intent(candidate):
                continue
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            requirements.append(
                AcceptanceCriterion(
                    ident=f"REQ-{counter}",
                    text=candidate,
                    source=source.label,
                )
            )
            counter += 1

    return requirements


def has_clear_product_intent(text: str) -> bool:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) < 80:
        return False
    return bool(
        re.search(
            r"\b(user|admin|customer|system|page|api|workflow|feature|should|must|can|when|display|save|create|update|delete|filter|search)\b",
            compact,
            re.I,
        )
    )


def parse_memory_query(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        return "q", raw
    key, value = raw.split("=", 1)
    return key.strip(), value.strip()


def format_memory_query(query: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in query.items())


def compact_memory_search(args: argparse.Namespace, title: str) -> MemoryLookupResult:
    queries: list[dict[str, Any]] = []
    for query_field in ("repo", "project", "topic", "tool"):
        for value in getattr(args, query_field) or []:
            queries.append({query_field: value})
    for raw in args.memory_query or []:
        key, value = parse_memory_query(raw)
        if value:
            queries.append({key: value})
    if args.ticket_key:
        queries.append({"q": args.ticket_key})
    if title:
        queries.append({"q": title})

    try:
        from scripts import mcp_tools
    except (Exception, SystemExit) as exc:
        return MemoryLookupResult(records=[], warnings=[f"Braingent memory unavailable: {exc}."])

    try:
        records = mcp_tools.find_many(queries, limit=args.max_memory)
    except Exception as exc:  # pragma: no cover - defensive path for local index drift
        query_label = "; ".join(format_memory_query(query) for query in queries) or "no query"
        return MemoryLookupResult(
            records=[],
            warnings=[f"Braingent memory lookup degraded for `{query_label}`: {exc}."],
        )
    return MemoryLookupResult(records=records, warnings=[])


def split_diff(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    if ".." not in value:
        return value, "HEAD"
    base, head = value.split("..", 1)
    return base or None, head or None


def truncate_evidence(text: str, budget: int) -> str:
    cleaned = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(cleaned) <= budget:
        return cleaned
    return cleaned[:budget].rstrip() + "\n...[truncated]"


def run_command(command: list[str], budget: int) -> EvidenceItem:
    display = " ".join(command)
    try:
        proc = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
    except FileNotFoundError:
        return EvidenceItem(
            label=command_label(command),
            command=display,
            text=f"Command not found: {command[0]}",
            ok=False,
        )
    except subprocess.TimeoutExpired:
        return EvidenceItem(
            label=command_label(command),
            command=display,
            text="Command timed out after 90 seconds.",
            ok=False,
        )
    output = proc.stdout or ""
    if proc.returncode != 0 and proc.stderr:
        output = (output + "\n" + proc.stderr).strip()
    return EvidenceItem(
        label=command_label(command),
        command=display,
        text=truncate_evidence(output, budget),
        ok=proc.returncode == 0,
    )


def command_label(command: list[str]) -> str:
    known = {"status", "doctor", "qa-evidence", "pr-review", "search", "pack", "impact", "projection-impact"}
    for part in command:
        if part in known:
            return part
    return Path(command[0]).name


def gather_step_legacy_evidence(
    args: argparse.Namespace,
    *,
    binary: str,
    workspace: str,
    base: str | None,
    head: str | None,
    budget: int,
) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    common = [binary, "--workspace", workspace, "--no-banner", "--no-interactive"]

    if base and head and not args.no_diff:
        evidence.append(
            run_command(
                [
                    binary,
                    "pr-review",
                    "--workspace",
                    workspace,
                    "--base",
                    base,
                    "--head",
                    head,
                    "--keep-cache",
                    "--format",
                    "json",
                    "--no-banner",
                    "--no-interactive",
                ],
                budget,
            )
        )

    for target in args.gather_target or []:
        evidence.append(run_command([*common, "search", target, "--limit", "8", "--json"], budget))
        evidence.append(
            run_command(
                [*common, "pack", target, "--mode", "review", "--limit", "4", "--budget-bytes", str(budget), "--json"],
                budget,
            )
        )
        evidence.append(run_command([*common, "impact", target, "--limit", "12", "--json"], budget))

    for target in args.projection_target or []:
        evidence.append(
            run_command(
                [*common, "projection-impact", "--target", target, "--evidence-verbosity", "summary", "--json"],
                budget,
            )
        )

    return evidence


def gather_step_evidence(args: argparse.Namespace, base: str | None, head: str | None) -> list[EvidenceItem]:
    if args.no_diff and not args.gather_target:
        return []
    if not args.gather_workspace:
        return []

    binary = args.gather_binary or DEFAULT_GATHER_BINARY
    if shutil.which(binary) is None and not Path(binary).exists():
        return [
            EvidenceItem(
                label="gather-step",
                command=binary,
                text=f"Gather Step binary not found: {binary}",
                ok=False,
            )
        ]

    workspace = str(Path(args.gather_workspace).expanduser())
    budget = evidence_budget_bytes(args)
    common = [binary, "--workspace", workspace, "--no-banner", "--no-interactive"]
    evidence: list[EvidenceItem] = [
        run_command([*common, "status", "--json"], budget),
        run_command([*common, "doctor", "--json"], budget),
    ]

    native_targets = args.gather_target or ([None] if base and head and not args.no_diff else [])
    native_evidence: list[EvidenceItem] = []
    for target in native_targets:
        command = [*common, "qa-evidence"]
        if target:
            command.append(target)
        if base:
            command.extend(["--base", base])
        if head:
            command.extend(["--head", head])
        command.extend(["--budget-bytes", str(budget), "--json"])
        native_evidence.append(run_command(command, max(budget * 10, 120_000)))

    evidence.extend(native_evidence)
    if any(item.ok and item.label == "qa-evidence" and "qa-evidence.v1" in item.text for item in native_evidence):
        return evidence

    evidence.extend(
        gather_step_legacy_evidence(args, binary=binary, workspace=workspace, base=base, head=head, budget=budget)
    )
    return evidence


def qa_evidence_json_objects(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    stripped = text.strip()
    if not stripped:
        return objects
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return [parsed]
    candidates = stripped.splitlines()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
    return objects


def qa_evidence_packs_from_commands(evidence: list[EvidenceItem]) -> list[QAEvidencePack]:
    packs: list[QAEvidencePack] = []
    for item in evidence:
        if item.label != "qa-evidence" or not item.ok:
            continue
        for raw in qa_evidence_json_objects(item.text):
            if raw.get("schema_version") != "qa-evidence.v1":
                continue
            pack = normalize_pack(raw)
            if isinstance(pack.get("rows"), list):
                packs.append(pack)
    return packs


def merge_qa_evidence_packs(
    packs: list[QAEvidencePack],
    *,
    base: str | None,
    head: str | None,
    budget_tokens: int,
) -> QAEvidencePack | None:
    if not packs:
        return None

    rows = []
    seen_rows: set[str] = set()
    acs = []
    seen_acs: set[str] = set()
    dropped_kinds: set[str] = set()
    unsupported_surfaces: set[str] = set()
    truncated_rows = 0

    for pack in packs:
        summary = pack["manifest_summary"]
        truncated_rows += int(summary.get("truncated_rows") or 0)
        dropped_kinds.update(str(kind) for kind in summary.get("dropped_kinds", []))
        unsupported_surfaces.update(str(surface) for surface in summary.get("unsupported_surfaces", []))
        for row in pack["rows"]:
            row_id = row["row_id"]
            if row_id in seen_rows:
                continue
            rows.append(row)
            seen_rows.add(row_id)
        for ac in pack.get("acs", []):
            ac_id = ac["ac_id"]
            if ac_id in seen_acs:
                continue
            acs.append(ac)
            seen_acs.add(ac_id)

    summary = build_manifest(
        rows,
        base_ref=base or "",
        head_ref=head or "",
        budget_tokens=budget_tokens,
    )
    summary["evidence_pack_version"] = "qa-evidence.v1"
    summary["generated_at"] = "generated-by-gather-step"
    summary["truncated_rows"] = max(summary["truncated_rows"], truncated_rows)
    summary["dropped_kinds"] = sorted(dropped_kinds)
    summary["unsupported_surfaces"] = sorted(set(summary["unsupported_surfaces"]) | unsupported_surfaces)
    merged: QAEvidencePack = {"manifest_summary": summary, "rows": rows}
    if acs:
        merged["acs"] = acs
    return merged


def evidence_pack_from_commands(
    evidence: list[EvidenceItem],
    *,
    base: str | None,
    head: str | None,
    budget_tokens: int,
) -> QAEvidencePack | None:
    if not evidence:
        return None
    native_pack = merge_qa_evidence_packs(
        qa_evidence_packs_from_commands(evidence),
        base=base,
        head=head,
        budget_tokens=budget_tokens,
    )
    if native_pack:
        return native_pack

    rows = [
        command_to_row(
            f"QE-{index:03}",
            item.command,
            item.text,
            ok=item.ok,
            base_ref=base or "",
            head_ref=head or "",
        )
        for index, item in enumerate(evidence, start=1)
        if item.label not in {"status", "doctor"}
    ]
    for item, row in zip([item for item in evidence if item.label not in {"status", "doctor"}], rows, strict=False):
        item.evidence_row_id = row["row_id"]
    return {
        "manifest_summary": build_manifest(
            rows,
            base_ref=base or "",
            head_ref=head or "",
            budget_tokens=budget_tokens,
        ),
        "rows": rows,
    }


def evidence_items_from_pack(path: Path, pack: QAEvidencePack) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for row in pack["rows"]:
        items.append(
            EvidenceItem(
                label=row["source_kind"],
                command=f"qa-evidence:{path}#{row['row_id']}",
                text=row_to_text(row),
                ok=not row["unsupported"],
                evidence_row_id=row["row_id"],
            )
        )
    return items


def infer_case_type(text: str) -> str:
    if re.search(r"\b(api|endpoint|graphql|rest|request|response|contract|schema|payload|webhook)\b", text, re.I):
        return "Manual API"
    if re.search(
        r"\b(page|button|modal|screen|form|field|tab|grid|table|filter|sort|pagination|browser|mobile|figma|ui)\b",
        text,
        re.I,
    ):
        return "Manual UI"
    if re.search(r"\b(event|queue|topic|projection|consumer|producer)\b", text, re.I):
        return "Contract Check"
    return "Exploratory Charter"


def infer_priority(text: str) -> str:
    if re.search(r"\b(security|permission|payment|data loss|blocked|cannot|must|compliance|migration|production)\b", text, re.I):
        return "High"
    if re.search(r"\b(edge|negative|optional|copy|tooltip|cosmetic)\b", text, re.I):
        return "Low"
    return "Medium"


def data_variations_for(text: str) -> list[str]:
    variations: list[str] = []
    checks = [
        (r"\b(role|permission|admin|owner|viewer|approver|reviewer|lead)\b", "role/permission matrix"),
        (r"\b(tenant|workspace|organization|account)\b", "single-tenant and cross-tenant data"),
        (r"\b(locale|language|currency|timezone|date)\b", "locale, timezone, and date boundaries"),
        (r"\b(empty|null|missing|required|optional)\b", "empty, null, and missing values"),
        (r"\b(filter|search|sort|pagination|page)\b", "empty, partial, and large result sets"),
        (r"\b(upload|file|image|document)\b", "valid, invalid, and oversized files"),
    ]
    for pattern, label in checks:
        if re.search(pattern, text, re.I):
            variations.append(label)
    return variations or ["happy path, negative path, and boundary data"]


def keyword_set(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]{3,}", text.lower())
    stop = {
        "this",
        "that",
        "with",
        "from",
        "when",
        "then",
        "should",
        "must",
        "user",
        "system",
        "page",
        "data",
        "value",
    }
    return {word for word in words if word not in stop}


def evidence_overlaps(ac: AcceptanceCriterion, evidence: list[EvidenceItem]) -> bool:
    keywords = keyword_set(ac.text)
    if not keywords:
        return False
    haystack = "\n".join(item.text for item in evidence if item.ok).lower()
    return len([word for word in keywords if word in haystack]) >= min(2, len(keywords))


def scenario_from_ac(ac: AcceptanceCriterion, index: int, classification: str) -> Scenario:
    text = ac.text.rstrip(".")
    case_type = infer_case_type(text)
    return Scenario(
        ident=f"TC-{index:03d}",
        title=text[:80],
        classification=classification,
        case_type=case_type,
        priority=infer_priority(text),
        sources=[f"{ac.ident}: {text} ({ac.source})"],
        preconditions=["Relevant feature flag, role, and environment are configured for the source requirement."],
        steps=[
            f"Prepare the product surface or API flow described by {ac.ident}.",
            f"Exercise the behavior: {text}.",
            "Repeat with the listed data variations when the behavior depends on input shape.",
        ],
        expected_result=f"The system satisfies {ac.ident}: {text}.",
        data_variations=data_variations_for(text),
        automation_candidate="Yes" if case_type in {"Manual API", "E2E Candidate", "Contract Check"} else "Maybe",
        gaps=[],
    )


def scenario_from_evidence(evidence: EvidenceItem, index: int) -> Scenario:
    first_line = next((line.strip() for line in evidence.text.splitlines() if line.strip()), evidence.command)
    title = first_line[:80]
    return Scenario(
        ident=f"TC-{index:03d}",
        title=f"Verify implementation evidence: {title}",
        classification="Code-only",
        case_type="Exploratory Charter",
        priority="Medium",
        sources=[f"Gather Step {evidence.label}: `{evidence.command}`"],
        preconditions=["Implementation branch is available and the Gather Step index is current enough for review evidence."],
        steps=[
            "Open the changed implementation surfaces cited by the evidence command.",
            "Trace callers, consumers, contracts, and existing tests named in the evidence.",
            "Exercise one representative happy path and one failure or boundary path for each risky surface.",
        ],
        expected_result="Implementation behavior is either covered by product requirements or recorded as a code-only gap.",
        data_variations=["caller/consumer path", "changed contract shape", "existing test present vs absent"],
        automation_candidate="Maybe",
        gaps=["Needs product-owner confirmation unless it maps to an explicit acceptance criterion."],
    )


def evidence_matches_ac(ac: AcceptanceCriterion, evidence: EvidenceItem) -> bool:
    return evidence.ok and evidence.label not in {"status", "doctor"} and evidence_overlaps(ac, [evidence])


def build_scenarios(model: GenerationInput) -> list[Scenario]:
    scenarios: list[Scenario] = []
    matched_evidence: set[int] = set()
    for ac in model.acceptance_criteria:
        matches = [
            index
            for index, evidence in enumerate(model.gather_evidence)
            if evidence_matches_ac(ac, evidence)
        ]
        classification = "Both" if matches else "AC-only"
        matched_evidence.update(matches)
        scenarios.append(scenario_from_ac(ac, len(scenarios) + 1, classification))

    if not model.no_diff:
        for index, evidence in enumerate(model.gather_evidence):
            if index in matched_evidence:
                continue
            if not evidence.ok or not evidence.text.strip() or evidence.label in {"status", "doctor"}:
                continue
            scenarios.append(scenario_from_evidence(evidence, len(scenarios) + 1))

    if not scenarios:
        raise InputError("No testable scenarios could be generated from the provided inputs.")
    return scenarios


def build_gaps(args: argparse.Namespace, ticket: SourceDoc, criteria: list[AcceptanceCriterion]) -> list[str]:
    gaps: list[str] = []
    text = ticket.text
    if not criteria:
        gaps.append("Acceptance criteria were not found; generated cases are inferred from product intent.")
    for source in getattr(args, "_source_docs", []):
        if not any(criterion.source == source.label for criterion in criteria):
            gaps.append(f"{source.label} did not yield explicit requirement rows; review it manually for hidden product intent.")
    if re.search(r"\b(page|screen|button|ui|figma|design|browser)\b", text, re.I) and not args.design_context:
        gaps.append("UI/design context was not supplied; visual and responsive checks need page, screenshot, or Figma evidence.")
    if not args.no_diff and not (args.diff or (args.base and args.head)):
        gaps.append("Implementation diff was not supplied; white-box classification is limited to explicit Gather Step targets.")
    for ac in criteria:
        if re.search(r"\b(etc\.|and so on|properly|as expected|user-friendly|fast|nice|seamless)\b", ac.text, re.I):
            gaps.append(f"{ac.ident} contains wording that may need a sharper expected result.")
    return gaps


def build_model(args: argparse.Namespace) -> GenerationInput:
    ticket = read_source(args.ticket, "Ticket")
    sources = [read_source(value, f"Source {index}") for index, value in enumerate(args.source or [], start=1)]
    all_sources = [ticket, *sources]
    criteria = extract_acceptance_criteria(all_sources)
    title = short_title(ticket.text, args.ticket_key or "test plan")
    product_requirements = extract_product_requirements(
        all_sources,
        criteria,
        include_ticket=not criteria and args.allow_missing_ac,
    )

    if not criteria and not args.allow_missing_ac:
        raise InputError(
            "Refusing to generate: provide acceptance criteria or pass --allow-missing-ac for clear product intent."
        )
    if not criteria and not product_requirements and not has_clear_product_intent(ticket.text):
        raise InputError(
            "Refusing to generate: provide acceptance criteria or a clearer product-intent source."
        )
    criteria = [*criteria, *product_requirements]

    base, head = args.base, args.head
    diff_base, diff_head = split_diff(args.diff)
    base = base or diff_base
    head = head or diff_head

    if args.no_diff and args.implementation_state == "post-implementation":
        args.implementation_state = "pre-implementation"

    args._source_docs = sources
    memory_lookup = compact_memory_search(args, title)
    evidence_pack: QAEvidencePack | None = None
    if args.evidence_pack:
        evidence_pack_path = Path(args.evidence_pack).expanduser()
        try:
            evidence_pack = load_pack(evidence_pack_path)
        except (OSError, ValueError) as exc:
            raise InputError(f"Invalid qa-evidence pack `{args.evidence_pack}`: {exc}") from exc
        gather_evidence = evidence_items_from_pack(evidence_pack_path, evidence_pack)
    else:
        command_evidence = gather_step_evidence(args, base, head)
        evidence_pack = evidence_pack_from_commands(
            command_evidence,
            base=base,
            head=head,
            budget_tokens=max(1, evidence_budget_bytes(args) // 4),
        )
        if evidence_pack and evidence_pack["manifest_summary"]["evidence_pack_version"] == "qa-evidence.v1":
            gather_evidence = evidence_items_from_pack(Path("gather-step qa-evidence"), evidence_pack)
            gather_evidence.extend(item for item in command_evidence if not item.ok)
        else:
            gather_evidence = command_evidence
    existing_ac_ids = {criterion.ident for criterion in criteria}
    if evidence_pack:
        for ac in evidence_pack.get("acs", []):
            ac_id = str(ac.get("ac_id") or "").strip()
            text = str(ac.get("text") or "").strip()
            if ac_id and text and ac_id not in existing_ac_ids:
                criteria.append(AcceptanceCriterion(ident=ac_id, text=text, source="QA Evidence Pack"))
                existing_ac_ids.add(ac_id)
    gaps = build_gaps(args, ticket, criteria)
    gaps.extend(memory_lookup.warnings)

    if not gather_evidence and not args.no_diff:
        gaps.append("Gather Step evidence was not collected; code-only and Both classifications may be incomplete.")
    for evidence in gather_evidence:
        if not evidence.ok:
            gaps.append(f"Gather Step command failed or was unavailable: `{evidence.command}`.")
    if evidence_pack:
        summary = evidence_pack["manifest_summary"]
        if summary.get("truncated_rows", 0) > 0:
            gaps.append(
                f"QA evidence manifest reports {summary['truncated_rows']} truncated rows; coverage completeness is blocked until reviewed."
            )
        for surface in summary.get("unsupported_surfaces", []):
            gaps.append(f"QA evidence manifest marks `{surface}` discovery as unsupported.")

    assumptions = [
        f"Implementation state: {args.implementation_state}.",
        "Generated output is a manual QA reference, not executable automated test code.",
    ]
    if args.no_diff:
        assumptions.append("No implementation diff was used; white-box pass was skipped.")

    return GenerationInput(
        ticket_key=args.ticket_key or title,
        ticket=ticket,
        sources=sources,
        acceptance_criteria=criteria,
        implementation_state=args.implementation_state,
        no_diff=args.no_diff,
        base=base,
        head=head,
        memory_records=memory_lookup.records,
        gather_evidence=gather_evidence,
        evidence_pack=evidence_pack,
        assumptions=assumptions,
        gaps=gaps,
    )


def markdown_list(items: list[str], empty: str = "None.") -> str:
    if not items:
        return f"- {empty}"
    return "\n".join(f"- {item}" for item in items)


def render_sources(model: GenerationInput) -> str:
    rows = ["| ID | Source | Path | Notes |", "| --- | --- | --- | --- |"]
    rows.append(f"| SRC-1 | Ticket | `{model.ticket.path}` | {model.ticket_key} |")
    for index, source in enumerate(model.sources, start=2):
        rows.append(f"| SRC-{index} | {source.label} | `{source.path}` | Supporting source |")
    for index, record in enumerate(model.memory_records, start=1):
        title = str(record.get("title") or "")
        path = str(record.get("path") or "")
        rows.append(f"| MEM-{index} | Braingent | `{path}` | {title} |")
    for index, evidence in enumerate(model.gather_evidence, start=1):
        status = "ok" if evidence.ok else "gap"
        row_id = f" / {evidence.evidence_row_id}" if evidence.evidence_row_id else ""
        rows.append(f"| GS-{index} | Gather Step | `{evidence.command}` | {status}{row_id} |")
    return "\n".join(rows)


def scenario_source_matches(source: str, ident: str) -> bool:
    return source.split(":", 1)[0].strip() == ident


def scenario_source_id(source: str) -> str:
    return source.split(":", 1)[0].strip()


def unique_ordered(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def spec_id_for_ident(ident: str) -> str:
    match = re.search(r"(\d+)$", ident)
    if not match:
        return f"SPEC-{slugify(ident).upper()}"
    return f"SPEC-{int(match.group(1)):03d}"


def scenario_source_ids(scenario: Scenario) -> list[str]:
    return unique_ordered([scenario_source_id(source) for source in scenario.sources])


def scenario_spec_ids(scenario: Scenario) -> list[str]:
    ids = [source_id for source_id in scenario_source_ids(scenario) if source_id.startswith(("AC-", "REQ-"))]
    return [spec_id_for_ident(source_id) for source_id in ids]


def scenarios_for_requirement(scenarios: list[Scenario], ident: str) -> list[str]:
    return [
        scenario.ident
        for scenario in scenarios
        if any(scenario_source_matches(source, ident) for source in scenario.sources)
    ]


def deterministic_precheck_gaps(model: GenerationInput, scenarios: list[Scenario]) -> list[str]:
    gaps: list[str] = []
    existing_gap_text = "\n".join(model.gaps).lower()
    for criterion in model.acceptance_criteria:
        if scenarios_for_requirement(scenarios, criterion.ident):
            continue
        if criterion.ident.lower() not in existing_gap_text:
            gaps.append(f"Precheck: {criterion.ident} has no covering test case or explicit gap.")

    titles: dict[str, str] = {}
    for scenario in scenarios:
        key = scenario.title.lower()
        if key in titles:
            gaps.append(f"Precheck: {scenario.ident} duplicates scenario title with {titles[key]}.")
        else:
            titles[key] = scenario.ident
        if not scenario.sources:
            gaps.append(f"Precheck: {scenario.ident} has no structured source citation.")
        if not scenario.expected_result or len(scenario.expected_result.strip()) < 12:
            gaps.append(f"Precheck: {scenario.ident} has a weak expected result.")

    if model.evidence_pack:
        summary = model.evidence_pack["manifest_summary"]
        if summary["truncated_rows"] > 0 and "truncated" not in existing_gap_text:
            gaps.append("Precheck: QA evidence pack truncation is not surfaced in gaps.")
        for surface in summary.get("unsupported_surfaces", []):
            if surface.lower() not in existing_gap_text:
                gaps.append(f"Precheck: unsupported QA evidence surface `{surface}` is not surfaced in gaps.")

    return unique_ordered(gaps)


def all_gaps(model: GenerationInput, scenarios: list[Scenario]) -> list[str]:
    return unique_ordered([*model.gaps, *deterministic_precheck_gaps(model, scenarios)])


def render_ac_matrix(model: GenerationInput, scenarios: list[Scenario]) -> str:
    if not model.acceptance_criteria:
        return "- No explicit acceptance criteria found."
    rows = ["| AC | Requirement | Cases | Status |", "| --- | --- | --- | --- |"]
    for ac in model.acceptance_criteria:
        linked = scenarios_for_requirement(scenarios, ac.ident)
        status = "covered" if linked else "gap"
        rows.append(f"| {ac.ident} | {ac.text} | {', '.join(linked) or '-'} | {status} |")
    return "\n".join(rows)


def render_spec_matrix(model: GenerationInput, scenarios: list[Scenario]) -> str:
    if not model.acceptance_criteria:
        return "- No spec rows generated."
    rows = ["| Spec | Source | Requirement | Cases | Status |", "| --- | --- | --- | --- | --- |"]
    for criterion in model.acceptance_criteria:
        linked = scenarios_for_requirement(scenarios, criterion.ident)
        rows.append(
            f"| {spec_id_for_ident(criterion.ident)} | {criterion.ident} | {criterion.text} | "
            f"{', '.join(linked) or '-'} | {'covered' if linked else 'gap'} |"
        )
    return "\n".join(rows)


def render_uncovered_requirements(model: GenerationInput, scenarios: list[Scenario]) -> str:
    uncovered = [
        f"{criterion.ident}: {criterion.text}"
        for criterion in model.acceptance_criteria
        if not scenarios_for_requirement(scenarios, criterion.ident)
    ]
    return markdown_list(uncovered)


def render_reverse_traceability(model: GenerationInput, scenarios: list[Scenario]) -> str:
    if not model.acceptance_criteria:
        return "- No explicit acceptance criteria found."
    rows = ["| Requirement | Spec | Test Cases |", "| --- | --- | --- |"]
    for criterion in model.acceptance_criteria:
        linked = scenarios_for_requirement(scenarios, criterion.ident)
        rows.append(f"| {criterion.ident} | {spec_id_for_ident(criterion.ident)} | {', '.join(linked) or '-'} |")
    return "\n".join(rows)


def render_ac_heatmap(model: GenerationInput, scenarios: list[Scenario]) -> str:
    if not model.acceptance_criteria:
        return "- No explicit acceptance criteria found."
    rows = ["| Requirement | Coverage |", "| --- | --- |"]
    for criterion in model.acceptance_criteria:
        linked = scenarios_for_requirement(scenarios, criterion.ident)
        marker = "covered" if linked else "uncovered"
        rows.append(f"| {criterion.ident} | {marker} |")
    return "\n".join(rows)


def render_impact_map(model: GenerationInput) -> str:
    lines: list[str] = []
    if model.base or model.head:
        lines.append(f"- Diff: `{model.base or '?'}` -> `{model.head or '?'}`")
    if model.evidence_pack:
        summary = model.evidence_pack["manifest_summary"]
        lines.append(
            "- QA Evidence Pack: "
            f"{summary['total_rows']} rows, {summary['truncated_rows']} truncated, "
            f"unsupported surfaces: {', '.join(summary['unsupported_surfaces']) or 'none'}."
        )
    if model.gather_evidence:
        for evidence in model.gather_evidence:
            status = "ok" if evidence.ok else "gap"
            row_id = f" ({evidence.evidence_row_id})" if evidence.evidence_row_id else ""
            lines.append(f"- {status}{row_id}: `{evidence.command}`")
    else:
        lines.append("- No Gather Step evidence collected.")
    return "\n".join(lines)


def render_scenario(scenario: Scenario) -> str:
    return "\n".join(
        [
            f"### {scenario.ident}: {scenario.title}",
            "",
            f"- Classification: {scenario.classification}",
            f"- Type: {scenario.case_type}",
            f"- Priority: {scenario.priority}",
            "- Sources:",
            *[f"  - {source}" for source in scenario.sources],
            "- Preconditions:",
            *[f"  - {item}" for item in scenario.preconditions],
            "- Steps:",
            *[f"  {index}. {step}" for index, step in enumerate(scenario.steps, start=1)],
            f"- Expected Result: {scenario.expected_result}",
            "- Data Variations:",
            *[f"  - {item}" for item in scenario.data_variations],
            f"- Automation Candidate: {scenario.automation_candidate}",
            "- Gaps / Notes:",
            *[f"  - {item}" for item in (scenario.gaps or ['None.'])],
        ]
    )


def render_plan(model: GenerationInput, scenarios: list[Scenario]) -> str:
    title = short_title(model.ticket.text, model.ticket_key)
    gaps = all_gaps(model, scenarios)
    coverage = {
        "both": len([scenario for scenario in scenarios if scenario.classification == "Both"]),
        "ac_only": len([scenario for scenario in scenarios if scenario.classification == "AC-only"]),
        "code_only": len([scenario for scenario in scenarios if scenario.classification == "Code-only"]),
    }
    scenario_blocks = "\n\n".join(render_scenario(scenario) for scenario in scenarios)
    followups = gaps or ["None."]
    return f"""# Test Plan: {model.ticket_key}

> Generated by Braingent `tools/tool--test-plan`. Human review required before QA execution.

## Intake Summary

- Title: {title}
- Implementation State: {model.implementation_state}
- Diff Mode: {"no-diff / product-only evidence" if model.no_diff else "implementation evidence requested"}
- Scenario Count: {len(scenarios)}

## Assumptions

{markdown_list(model.assumptions)}

## Coverage Summary

- Both: {coverage["both"]}
- AC-only: {coverage["ac_only"]}
- Code-only: {coverage["code_only"]}
- Gaps: {len(gaps)}

## Source Registry

{render_sources(model)}

## Spec Matrix

{render_spec_matrix(model, scenarios)}

## AC Coverage Matrix

{render_ac_matrix(model, scenarios)}

## AC Coverage Heatmap

{render_ac_heatmap(model, scenarios)}

## Uncovered ACs

{render_uncovered_requirements(model, scenarios)}

## Code Paths And Impact Map

{render_impact_map(model)}

## Test Cases

{scenario_blocks}

## Data Matrix

{markdown_list(sorted({variation for scenario in scenarios for variation in scenario.data_variations}))}

## Gaps

{markdown_list(gaps)}

## Follow-Up Questions

{markdown_list(followups)}

## Reverse Traceability Index

{render_reverse_traceability(model, scenarios)}

## Traceability

- Ticket source: `{model.ticket.path}`
- Braingent memory records: {len(model.memory_records)}
- Gather Step evidence commands: {len(model.gather_evidence)}
- QA evidence rows: {model.evidence_pack['manifest_summary']['total_rows'] if model.evidence_pack else 0}
"""


def scenario_to_export_dict(scenario: Scenario) -> dict[str, Any]:
    return {
        "id": scenario.ident,
        "title": scenario.title,
        "classification": scenario.classification,
        "type": scenario.case_type,
        "priority": scenario.priority,
        "sources": scenario.sources,
        "source_ids": scenario_source_ids(scenario),
        "spec_ids": scenario_spec_ids(scenario),
        "preconditions": scenario.preconditions,
        "steps": scenario.steps,
        "expected_result": scenario.expected_result,
        "data_variations": scenario.data_variations,
        "automation_candidate": scenario.automation_candidate,
        "gaps": scenario.gaps,
    }


def render_xray_json(model: GenerationInput, scenarios: list[Scenario]) -> str:
    tests = []
    for scenario in scenarios:
        tests.append(
            {
                "testInfo": {
                    "summary": f"{scenario.ident}: {scenario.title}",
                    "type": "Manual",
                    "labels": ["braingent", scenario.classification.lower().replace(" ", "-")],
                    "requirements": scenario_source_ids(scenario),
                    "specIds": scenario_spec_ids(scenario),
                    "steps": [
                        {"action": step, "data": "", "result": scenario.expected_result}
                        for step in scenario.steps
                    ],
                    "preconditions": "\n".join(scenario.preconditions),
                    "description": "\n".join(scenario.sources),
                }
            }
        )
    payload = {
        "schema": "braingent-xray-json.v1",
        "ticketKey": model.ticket_key,
        "summary": {
            "scenarioCount": len(scenarios),
            "gaps": all_gaps(model, scenarios),
            "qaEvidenceRows": model.evidence_pack["manifest_summary"]["total_rows"] if model.evidence_pack else 0,
        },
        "tests": tests,
    }
    return json.dumps(payload, indent=2)


def render_testrail_csv(model: GenerationInput, scenarios: list[Scenario]) -> str:
    output = io.StringIO()
    fieldnames = [
        "Section",
        "Title",
        "Preconditions",
        "Steps",
        "Expected Result",
        "Priority",
        "Type",
        "Automation Candidate",
        "References",
        "Spec IDs",
        "Labels",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for scenario in scenarios:
        writer.writerow(
            {
                "Section": model.ticket_key,
                "Title": f"{scenario.ident}: {scenario.title}",
                "Preconditions": "\n".join(scenario.preconditions),
                "Steps": "\n".join(f"{index}. {step}" for index, step in enumerate(scenario.steps, start=1)),
                "Expected Result": scenario.expected_result,
                "Priority": scenario.priority,
                "Type": scenario.case_type,
                "Automation Candidate": scenario.automation_candidate,
                "References": ", ".join(scenario_source_ids(scenario)),
                "Spec IDs": ", ".join(scenario_spec_ids(scenario)),
                "Labels": f"braingent,{scenario.classification.lower().replace(' ', '-')}",
            }
        )
    return output.getvalue()


def gherkin_safe(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().replace(":", " -")


def render_gherkin(model: GenerationInput, scenarios: list[Scenario]) -> str:
    lines = [
        f"Feature: {gherkin_safe(model.ticket_key)} QA test plan",
        "  Generated by Braingent tools/tool--test-plan.",
        "",
    ]
    for scenario in scenarios:
        tags = [
            f"@{scenario.ident}",
            f"@{scenario.classification.lower().replace('-', '_').replace(' ', '_')}",
            *[f"@{spec_id.replace('-', '_')}" for spec_id in scenario_spec_ids(scenario)],
        ]
        lines.extend(
            [
                "  " + " ".join(tags),
                f"  Scenario: {gherkin_safe(scenario.title)}",
            ]
        )
        for precondition in scenario.preconditions:
            lines.append(f"    Given {gherkin_safe(precondition)}")
        for index, step in enumerate(scenario.steps):
            keyword = "When" if index == 0 else "And"
            lines.append(f"    {keyword} {gherkin_safe(step)}")
        lines.append(f"    Then {gherkin_safe(scenario.expected_result)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_output(model: GenerationInput, scenarios: list[Scenario], emit_format: str) -> str:
    if emit_format == "markdown":
        return render_plan(model, scenarios)
    if emit_format == "xray-json":
        return render_xray_json(model, scenarios)
    if emit_format == "testrail-csv":
        return render_testrail_csv(model, scenarios)
    if emit_format == "gherkin":
        return render_gherkin(model, scenarios)
    raise InputError(f"Unsupported emit format: {emit_format}")


def output_path_for(args: argparse.Namespace, model: GenerationInput) -> Path:
    if args.output:
        return Path(args.output).expanduser()
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else DEFAULT_OUTPUT_DIR
    extension = EMIT_EXTENSIONS[args.emit_format]
    return output_dir / f"{slugify(model.ticket_key)}--test-plan{extension}"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Braingent manual QA test plan from ticket text, memory, and optional Gather Step evidence."
    )
    parser.add_argument("ticket", help="Ticket text or path to a Markdown/text ticket export.")
    parser.add_argument("--ticket-key", default="", help="Ticket key or short identifier for the output title.")
    parser.add_argument("--source", action="append", default=[], help="Supporting spec, PRD, note, or design source path/text.")
    parser.add_argument(
        "--implementation-state",
        choices=("pre-implementation", "in-progress", "post-implementation"),
        default="post-implementation",
    )
    parser.add_argument("--allow-missing-ac", action="store_true", help="Allow generation when no explicit AC is found.")
    parser.add_argument("--design-context", action="store_true", help="Mark design/page context as supplied.")
    parser.add_argument("--no-diff", action="store_true", help="Skip white-box implementation evidence.")
    parser.add_argument("--diff", help="Base/head range, e.g. main..HEAD.")
    parser.add_argument("--base", help="Base ref for implementation evidence.")
    parser.add_argument("--head", help="Head ref for implementation evidence.")
    parser.add_argument("--gather-workspace", help="Workspace path for Gather Step evidence commands.")
    parser.add_argument("--gather-binary", default=DEFAULT_GATHER_BINARY, help="Gather Step binary path/name.")
    parser.add_argument("--gather-target", action="append", default=[], help="Symbol/route/event target to inspect with Gather Step.")
    parser.add_argument("--projection-target", action="append", default=[], help="Field target to inspect with Gather Step projection-impact.")
    parser.add_argument("--evidence-pack", help="Already-normalized qa-evidence.json path.")
    parser.add_argument(
        "--emit-format",
        choices=tuple(EMIT_EXTENSIONS),
        default="markdown",
        help="Output format: markdown, xray-json, testrail-csv, or gherkin.",
    )
    parser.add_argument(
        "--budget-tokens",
        type=int,
        default=DEFAULT_BUDGET_TOKENS,
        help="Evidence token budget before explicit truncation gaps are emitted.",
    )
    parser.add_argument(
        "--evidence-budget-bytes",
        type=int,
        help="Low-level Gather Step byte budget override. Defaults to --budget-tokens * 4.",
    )
    parser.add_argument("--repo", action="append", default=[], help="Braingent repository filter.")
    parser.add_argument("--project", action="append", default=[], help="Braingent project filter.")
    parser.add_argument("--topic", action="append", default=[], help="Braingent topic filter.")
    parser.add_argument("--tool", action="append", default=[], help="Braingent tool filter.")
    parser.add_argument("--memory-query", action="append", default=[], help="Extra Braingent memory query, e.g. q=QA miss.")
    parser.add_argument("--max-memory", type=int, default=8)
    parser.add_argument("--output", help="Output path.")
    parser.add_argument("--output-dir", help="Output directory. Defaults to .test-plans/.")
    parser.add_argument("--print", action="store_true", dest="print_output", help="Print generated output.")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        model = build_model(args)
        scenarios = build_scenarios(model)
        rendered = render_output(model, scenarios, args.emit_format)
        path = output_path_for(args, model)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    except InputError as exc:
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: {exc}", file=sys.stderr)
        return 2

    if args.print_output:
        print(rendered)
    else:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

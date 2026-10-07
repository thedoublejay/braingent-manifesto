"""Generic drift check between per-service environment contracts and a deployed mirror.

A contract is one JSON file per service:

    {"service": "<name>", "fields": {"<field>": ["<ENV_VAR>", ...]}, "required_fields": [...],
     "source_config_sha256": "<hex>", "version": 1}

Both directories hold files of this shape. Paths are arguments, never defaults.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when a contract file cannot be read or has an unexpected shape."""


@dataclass(frozen=True)
class Contract:
    service: str
    env_vars: frozenset[str]
    required_fields: frozenset[str]
    source_sha256: str | None


@dataclass(frozen=True)
class ServiceDrift:
    service: str
    missing_in_deployed: tuple[str, ...] = ()
    missing_in_contract: tuple[str, ...] = ()
    required_only_in_contract: tuple[str, ...] = ()
    required_only_in_deployed: tuple[str, ...] = ()
    sha_mismatch: tuple[str, str] | None = None

    @property
    def has_drift(self) -> bool:
        return bool(
            self.missing_in_deployed
            or self.missing_in_contract
            or self.required_only_in_contract
            or self.required_only_in_deployed
            or self.sha_mismatch
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "missing_in_deployed": list(self.missing_in_deployed),
            "missing_in_contract": list(self.missing_in_contract),
            "required_only_in_contract": list(self.required_only_in_contract),
            "required_only_in_deployed": list(self.required_only_in_deployed),
            "sha_mismatch": list(self.sha_mismatch) if self.sha_mismatch else None,
        }


@dataclass(frozen=True)
class DriftReport:
    services_only_in_contracts: tuple[str, ...] = ()
    services_only_in_deployed: tuple[str, ...] = ()
    drifted: tuple[ServiceDrift, ...] = field(default_factory=tuple)
    compared: int = 0

    @property
    def has_drift(self) -> bool:
        return bool(self.services_only_in_contracts or self.services_only_in_deployed or self.drifted)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compared": self.compared,
            "has_drift": self.has_drift,
            "services_only_in_contracts": list(self.services_only_in_contracts),
            "services_only_in_deployed": list(self.services_only_in_deployed),
            "drifted": [item.to_dict() for item in self.drifted],
        }


def _string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContractError(f"{label}: expected a list of strings")
    return value


def load_contract(path: Path) -> Contract:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{path.as_posix()}: could not read contract ({exc})") from exc
    if not isinstance(raw, dict):
        raise ContractError(f"{path.as_posix()}: contract root must be an object")
    fields = raw.get("fields")
    if not isinstance(fields, dict):
        raise ContractError(f"{path.as_posix()}: `fields` must be an object")
    env_vars: set[str] = set()
    for name, variables in fields.items():
        env_vars.update(_string_list(variables, f"{path.as_posix()}: fields.{name}"))
    sha = raw.get("source_config_sha256")
    return Contract(
        service=str(raw.get("service") or path.stem),
        env_vars=frozenset(env_vars),
        required_fields=frozenset(_string_list(raw.get("required_fields"), f"{path.as_posix()}: required_fields")),
        source_sha256=sha if isinstance(sha, str) else None,
    )


def load_directory(directory: Path) -> dict[str, Contract]:
    if not directory.is_dir():
        raise ContractError(f"{directory.as_posix()}: not a directory")
    contracts: dict[str, Contract] = {}
    for path in sorted(directory.glob("*.json")):
        contract = load_contract(path)
        contracts[contract.service] = contract
    return contracts


def compare(contracts: dict[str, Contract], deployed: dict[str, Contract]) -> DriftReport:
    shared = sorted(set(contracts) & set(deployed))
    drifted: list[ServiceDrift] = []
    for service in shared:
        source, mirror = contracts[service], deployed[service]
        sha_mismatch = None
        if source.source_sha256 and mirror.source_sha256 and source.source_sha256 != mirror.source_sha256:
            sha_mismatch = (source.source_sha256, mirror.source_sha256)
        drift = ServiceDrift(
            service=service,
            missing_in_deployed=tuple(sorted(source.env_vars - mirror.env_vars)),
            missing_in_contract=tuple(sorted(mirror.env_vars - source.env_vars)),
            required_only_in_contract=tuple(sorted(source.required_fields - mirror.required_fields)),
            required_only_in_deployed=tuple(sorted(mirror.required_fields - source.required_fields)),
            sha_mismatch=sha_mismatch,
        )
        if drift.has_drift:
            drifted.append(drift)
    return DriftReport(
        services_only_in_contracts=tuple(sorted(set(contracts) - set(deployed))),
        services_only_in_deployed=tuple(sorted(set(deployed) - set(contracts))),
        drifted=tuple(drifted),
        compared=len(shared),
    )


def render_report(report: DriftReport) -> str:
    if not report.has_drift:
        return f"No config drift across {report.compared} service(s)."
    lines = [f"Config drift found ({report.compared} service(s) compared)."]
    lines.extend(f"- {service}: contract has no deployed mirror" for service in report.services_only_in_contracts)
    lines.extend(f"- {service}: deployed mirror has no contract" for service in report.services_only_in_deployed)
    for item in report.drifted:
        lines.append(f"- {item.service}")
        if item.missing_in_deployed:
            lines.append(f"  - in contract, missing from deployed: {', '.join(item.missing_in_deployed)}")
        if item.missing_in_contract:
            lines.append(f"  - in deployed, missing from contract: {', '.join(item.missing_in_contract)}")
        if item.required_only_in_contract:
            lines.append(f"  - required only in contract: {', '.join(item.required_only_in_contract)}")
        if item.required_only_in_deployed:
            lines.append(f"  - required only in deployed: {', '.join(item.required_only_in_deployed)}")
        if item.sha_mismatch:
            lines.append("  - source_config_sha256 differs between contract and deployed mirror")
    return "\n".join(lines)


def run_config_drift(contracts_dir: Path, deployed_dir: Path) -> DriftReport:
    return compare(load_directory(contracts_dir), load_directory(deployed_dir))

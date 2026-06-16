"""Optional configuration for the Braingent CLI.

Reads `.braingent/config.toml` (repo-local) and `~/.braingent/config.toml`
(user-level). Repo-local values win over user-level; both override built-in
defaults. The CLI works with no config file at all — the safety patterns below
are always active.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# Secret / forbidden-content patterns enforced by `braingent doctor`, always on.
# Config `[safety] forbid_patterns` is added to these, never replaces them.
BUILTIN_FORBID_PATTERNS: tuple[str, ...] = (
    r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}",
    r"BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY",
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b",
    r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    r"\bAIza[0-9A-Za-z_-]{35}\b",
    r"\bsk-[A-Za-z0-9]{20,}\b",
)

DEFAULT_STALE_DAYS = 180
DEFAULT_RECALL_LIMIT = 8
DEFAULT_TASK_ID_PREFIX = "BGT"
DEFAULT_TASK_ID_PAD = 4

CONFIG_RELATIVE_PATH = Path(".braingent") / "config.toml"


@dataclass(frozen=True)
class BraingentConfig:
    forbid_patterns: tuple[str, ...] = BUILTIN_FORBID_PATTERNS
    forbid_paths: tuple[str, ...] = ()
    doctor_stale_days: int = DEFAULT_STALE_DAYS
    recall_limit: int = DEFAULT_RECALL_LIMIT
    recall_stale_days: int = DEFAULT_STALE_DAYS
    task_id_prefix: str = DEFAULT_TASK_ID_PREFIX
    task_id_pad: int = DEFAULT_TASK_ID_PAD
    issues: tuple[str, ...] = field(default_factory=tuple)


DEFAULT_CONFIG = BraingentConfig()


def _read_toml(path: Path, issues: list[str]) -> dict:
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        issues.append(f"{path.as_posix()}: could not parse config ({exc})")
        return {}
    if not isinstance(data, dict):
        issues.append(f"{path.as_posix()}: config root must be a table")
        return {}
    return data


def load_config(repo_root: Path, home: Path | None = None) -> BraingentConfig:
    """Build a config from defaults plus user- and repo-level TOML files."""

    issues: list[str] = []
    home = home or Path.home()
    user = _read_toml(home / CONFIG_RELATIVE_PATH, issues)
    repo = _read_toml(repo_root / CONFIG_RELATIVE_PATH, issues)

    def positive_int(section: str, key: str, default: int) -> int:
        for source in (repo, user):  # repo wins
            table = source.get(section)
            if isinstance(table, dict) and key in table:
                value = table[key]
                if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                    return value
                issues.append(f"[{section}] {key} must be a positive integer")
                return default
        return default

    def nonempty_str(section: str, key: str, default: str) -> str:
        for source in (repo, user):  # repo wins
            table = source.get(section)
            if isinstance(table, dict) and key in table:
                value = table[key]
                if isinstance(value, str) and value.strip():
                    return value.strip()
                issues.append(f"[{section}] {key} must be a non-empty string")
                return default
        return default

    def string_list(section: str, key: str) -> list[str]:
        collected: list[str] = []
        for source in (user, repo):  # additive, user then repo
            table = source.get(section)
            if isinstance(table, dict) and key in table:
                value = table[key]
                if isinstance(value, list) and all(isinstance(item, str) for item in value):
                    collected.extend(value)
                else:
                    issues.append(f"[{section}] {key} must be a list of strings")
        return collected

    extra_patterns: list[str] = []
    for pattern in string_list("safety", "forbid_patterns"):
        try:
            re.compile(pattern)
        except re.error as exc:
            issues.append(f"[safety] invalid forbid_patterns regex {pattern!r}: {exc}")
            continue
        extra_patterns.append(pattern)

    return BraingentConfig(
        forbid_patterns=BUILTIN_FORBID_PATTERNS + tuple(extra_patterns),
        forbid_paths=tuple(string_list("safety", "forbid_paths")),
        doctor_stale_days=positive_int("doctor", "stale_days", DEFAULT_STALE_DAYS),
        recall_limit=positive_int("recall", "limit", DEFAULT_RECALL_LIMIT),
        recall_stale_days=positive_int("recall", "stale_days", DEFAULT_STALE_DAYS),
        task_id_prefix=nonempty_str("task_ids", "prefix", DEFAULT_TASK_ID_PREFIX),
        task_id_pad=positive_int("task_ids", "pad", DEFAULT_TASK_ID_PAD),
        issues=tuple(issues),
    )

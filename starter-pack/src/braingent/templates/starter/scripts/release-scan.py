#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - local environment issue.
    raise SystemExit("Missing PyYAML. Install package dev dependencies before running release-scan.") from exc


TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

FORBIDDEN_PARTS = {
    ".git",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    ".test-plans",
    "dashboard",
}


@dataclass(frozen=True)
class DenyPattern:
    ident: str
    regex: re.Pattern[str]
    description: str


def load_denylist(path: Path) -> list[DenyPattern]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    patterns = raw.get("patterns") if isinstance(raw, dict) else None
    if not isinstance(patterns, list):
        raise SystemExit(f"{path} must contain a patterns list")
    result: list[DenyPattern] = []
    for item in patterns:
        if not isinstance(item, dict):
            raise SystemExit(f"{path} contains a non-object pattern entry")
        result.append(
            DenyPattern(
                ident=str(item["id"]),
                regex=re.compile(str(item["regex"])),
                description=str(item.get("description") or item["id"]),
            )
        )
    return result


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def build_artifacts(package_root: Path, out_dir: Path) -> None:
    run([sys.executable, "-m", "build", str(package_root), "--outdir", str(out_dir)], package_root)


def extract_artifacts(dist_dir: Path, extract_dir: Path) -> list[Path]:
    roots: list[Path] = []
    for artifact in sorted(dist_dir.iterdir()):
        target = extract_dir / artifact.name
        target.mkdir(parents=True, exist_ok=True)
        if artifact.suffix == ".whl":
            with zipfile.ZipFile(artifact) as wheel:
                wheel.extractall(target)
        elif artifact.name.endswith(".tar.gz"):
            with tarfile.open(artifact, "r:gz") as sdist:
                sdist.extractall(target, filter="data")
        else:
            raise SystemExit(f"Unexpected artifact: {artifact.name}")
        roots.append(target)
    return roots


def normalized_artifact_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    parts = rel.split("/", 1)
    if len(parts) == 2 and parts[0].startswith("braingent-") and (root / parts[0] / "pyproject.toml").exists():
        return parts[1]
    return rel


def is_allowed_artifact_path(path: str) -> bool:
    parts = set(path.split("/"))
    if parts & FORBIDDEN_PARTS:
        return False
    if path.endswith(".pyc") or "/indexes/records" in path:
        return False
    if path in {"LICENSE", "PKG-INFO", "README.md", "pyproject.toml", "release/denylist.yml", "scripts/release-scan.py"}:
        return True
    return (path.startswith(("src/", "braingent/", "braingent-")) and ".dist-info/" in path) or path.startswith(
        ("src/braingent/", "braingent/")
    )


def iter_files(roots: list[Path]) -> list[tuple[Path, Path, str]]:
    files: list[tuple[Path, Path, str]] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file():
                files.append((root, path, normalized_artifact_path(path, root)))
    return files


def scan_allowed_files(files: list[tuple[Path, Path, str]]) -> list[str]:
    issues: list[str] = []
    for _, _, rel in files:
        if not is_allowed_artifact_path(rel):
            issues.append(f"unexpected artifact file: {rel}")
    return issues


def scan_denylist(files: list[tuple[Path, Path, str]], patterns: list[DenyPattern]) -> list[str]:
    issues: list[str] = []
    for _, path, rel in files:
        if path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in patterns:
            match = pattern.regex.search(text)
            if match:
                issues.append(f"{rel}: {pattern.ident}: {pattern.description}: {match.group(0)!r}")
    return issues


def run_gitleaks(source: Path, require: bool) -> list[str]:
    binary = shutil.which("gitleaks")
    if not binary:
        if require:
            return ["gitleaks is required but was not found on PATH"]
        print("release-scan: gitleaks not found; skipped external secret scan", file=sys.stderr)
        return []
    completed = subprocess.run([binary, "detect", "--source", str(source), "--no-git", "--redact"], check=False)
    if completed.returncode == 0:
        return []
    return [f"gitleaks detected potential secrets under {source}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and scan Braingent release artifacts.")
    parser.add_argument("--package-root", default=".", help="package root containing pyproject.toml")
    parser.add_argument("--denylist", default="release/denylist.yml", help="denylist YAML path")
    parser.add_argument("--require-gitleaks", action="store_true", help="fail if gitleaks is unavailable")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args(argv)

    package_root = Path(args.package_root).expanduser().resolve()
    denylist = Path(args.denylist)
    if not denylist.is_absolute():
        denylist = package_root / denylist
    patterns = load_denylist(denylist)

    with tempfile.TemporaryDirectory(prefix="braingent-release-scan-") as tmp:
        tmp_path = Path(tmp)
        dist_dir = tmp_path / "dist"
        extract_dir = tmp_path / "extract"
        dist_dir.mkdir()
        extract_dir.mkdir()
        build_artifacts(package_root, dist_dir)
        roots = extract_artifacts(dist_dir, extract_dir)
        files = iter_files(roots)
        issues = [
            *scan_allowed_files(files),
            *scan_denylist(files, patterns),
            *run_gitleaks(extract_dir, args.require_gitleaks),
        ]
        summary: dict[str, Any] = {
            "artifacts": sorted(path.name for path in dist_dir.iterdir()),
            "file_count": len(files),
            "issues": issues,
        }
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        elif issues:
            print("release-scan failed:", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
        else:
            print(f"release-scan passed for {', '.join(summary['artifacts'])}")
        return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

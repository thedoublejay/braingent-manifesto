#!/usr/bin/env sh
set -eu

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
script="$repo_root/scripts/braingent.py"

if command -v python3 >/dev/null 2>&1 && python3 -c 'import yaml' >/dev/null 2>&1; then
  exec python3 "$script" doctor "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run --script "$script" doctor "$@"
fi

printf '%s\n' 'Missing runtime: install PyYAML for python3 or install uv.' >&2
exit 127

#!/usr/bin/env sh
set -eu

if command -v braingent >/dev/null 2>&1; then
  exec braingent qa generate "$@"
fi

repo_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec python3 "$repo_root/tools/tool--test-plan/test_plan.py" "$@"

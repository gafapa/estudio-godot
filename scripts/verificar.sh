#!/usr/bin/env bash
# Verify installed project readiness; --quick never certifies engine execution.
set -eu
[ "$#" -ge 1 ] && [ "$#" -le 2 ] || { echo 'Usage: verificar.sh <project> [--quick]' >&2; exit 2; }
PROJECT="$1"; shift
PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
[ -d "$PROJECT" ] || { echo 'Project directory not found' >&2; exit 2; }
exec "$PY" "$PROJECT/tools/verify_project.py" "$PROJECT" "$@"

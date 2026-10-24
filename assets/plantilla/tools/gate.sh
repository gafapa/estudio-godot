#!/usr/bin/env bash
# Ticket gate: validate committed changes in a unique detached worktree.
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[ "$#" -ge 2 ] && [ "$#" -le 3 ] || { echo 'Usage: gate.sh <commit-or-branch> <ticket> [base]' >&2; exit 2; }
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
exec "$PY" tools/validate_commit.py --commit "$1" --ticket "$2" --base "${3:-main}" --quick

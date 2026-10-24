#!/usr/bin/env bash
# Local CI. Isolated modes validate a committed snapshot, never dirty editor files.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
QUICK=0; ISOLATED=0; SNAPSHOT=0; FRESH=0; COMMIT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --quick) QUICK=1; shift ;;
    --isolated|--aislado) ISOLATED=1; shift ;;
    --snapshot) SNAPSHOT=1; shift ;;
    --fresh) FRESH=1; shift ;;
    --commit) [ "$#" -ge 2 ] && [ -n "$2" ] || { echo '--commit requires a value' >&2; exit 2; }; COMMIT="$2"; ISOLATED=1; shift 2 ;;
    *) echo 'Usage: ci.sh [--quick] [--isolated] [--commit SHA] [--fresh]' >&2; exit 2 ;;
  esac
done
if [ "$ISOLATED" = 1 ]; then
  [ "$SNAPSHOT" = 0 ] || { echo 'Conflicting snapshot options' >&2; exit 2; }
  PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
  ARGS=(--commit "${COMMIT:-HEAD}")
  [ "$QUICK" = 0 ] || ARGS+=(--quick)
  [ "$FRESH" = 0 ] || ARGS+=(--fresh)
  exec "$PY" tools/validate_commit.py "${ARGS[@]}"
fi
if [ "$SNAPSHOT" = 1 ]; then
  [ -z "$(git status --porcelain --untracked-files=normal)" ] || { echo 'Snapshot must be clean' >&2; exit 2; }
fi
FAILED=()
run() { local name="$1"; shift; echo "CHECK $name"; if "$@"; then :; else FAILED+=("$name"); fi; }
run lint bash tools/lint.sh
run data bash tools/validate_data.sh
run tests bash tools/test.sh
if [ "$QUICK" = 0 ]; then
  run windows-export bash tools/export.sh windows release
  run pc-smoke bash tools/pc_smoke.sh --no-export
  run linux-export bash tools/export.sh linux release
fi
if [ "${#FAILED[@]}" = 0 ]; then echo 'CI_LOCAL_OK'; exit 0; fi
echo "CI_LOCAL_FAILED: ${FAILED[*]}" >&2
exit 1

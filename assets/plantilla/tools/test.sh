#!/usr/bin/env bash
# Run a nonempty GdUnit4 suite with mandatory bounded execution and strict log checks.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
VERBOSE=0; TARGET=""
for ARG in "$@"; do
  case "$ARG" in
    -v) VERBOSE=1 ;;
    -h|--help) echo 'Usage: test.sh [-v] [test-file-or-directory]'; exit 0 ;;
    -*) echo "Unknown option: $ARG" >&2; exit 2 ;;
    *) [ -z "$TARGET" ] || { echo 'Only one test target is allowed' >&2; exit 2; }; TARGET="$ARG" ;;
  esac
done
TARGET="${TARGET:-tests}"; TARGET="${TARGET#res://}"; TARGET="${TARGET#./}"; TARGET="${TARGET%/}"
[ -e "$TARGET" ] || { echo "Missing test target: $TARGET" >&2; exit 2; }
if [ -d "$TARGET" ]; then
  FOUND="$(find "$TARGET" -type f \( -name 'test_*.gd' -o -name '*_test.gd' \) -print -quit)"
  [ -n "$FOUND" ] || { echo 'TESTS_FAILED: no tests found' >&2; exit 1; }
fi
[ -f addons/gdUnit4/bin/GdUnitCmdTool.gd ] || { echo 'Missing GdUnit4 runner' >&2; exit 2; }
PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
GODOT_REAL="${GODOT:-godot}"; export GODOT_REAL
. tools/lib/godot_guard.sh
godot_guard_acquire || exit 2
trap godot_guard_release EXIT
mkdir -p tools/out; touch tools/out/.gdignore
LOG=tools/out/test.log
# Import every run: removed resources and project settings invalidate timestamp-only caches.
"$PY" tools/run_bounded.py "${TEST_TIMEOUT:-600}" tools/godot_guarded.sh --headless --path . --import > tools/out/import.log 2>&1
RC=$?
if [ "$RC" -ne 0 ] || grep -qE 'SCRIPT ERROR|Parse Error|Failed to load script|^ERROR:' tools/out/import.log; then
  echo 'TESTS_FAILED: project import failed' >&2; tail -20 tools/out/import.log >&2; exit 2
fi
"$PY" tools/run_bounded.py "${TEST_TIMEOUT:-600}" tools/godot_guarded.sh --headless --path . -s -d res://addons/gdUnit4/bin/GdUnitCmdTool.gd -a "res://$TARGET" -c --ignoreHeadlessMode -rd res://tools/out/reports -rc 2 > "$LOG" 2>&1
RC=$?
[ "$VERBOSE" = 0 ] || cat "$LOG"
if "$PY" tools/parse_test_log.py "$LOG" "$RC"; then exit 0; fi
tail -30 "$LOG" >&2
exit 1

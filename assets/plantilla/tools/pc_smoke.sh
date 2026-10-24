#!/usr/bin/env bash
# Smoke-test an exported PC build with a bounded guarded process.
set -u
cd "$(dirname "$0")/.." || exit 2
EXE="build/windows/{{EXE}}.exe"
CONSOLE="build/windows/{{EXE}}.console.exe"
TARGET=windows; NOEXPORT=0
for a in "$@"; do
  case "$a" in
    --no-export) NOEXPORT=1 ;;
    --linux) TARGET=linux; EXE="build/linux/{{EXE}}.x86_64"; CONSOLE="" ;;
    *) echo "Unknown argument: $a" >&2; exit 2 ;;
  esac
done
if [ "$NOEXPORT" = 0 ] || [ ! -f "$EXE" ]; then
  bash tools/export.sh "$TARGET" debug || exit 1
fi
RUN="$EXE"; [ -n "$CONSOLE" ] && [ -f "$CONSOLE" ] && RUN="$CONSOLE"   # console wrapper emits stdout
log="$(mktemp)"
GODOT_REAL="./$RUN" "${PYTHON:-python}" tools/run_bounded.py 60 tools/godot_guarded.sh --headless -- --smoke >"$log" 2>&1
rc=$?
if [ $rc -ne 0 ] || ! grep -q "^SMOKE_OK" "$log" || grep -qE "SCRIPT ERROR|Parse Error|Failed to load script|^ERROR" "$log"; then
  echo "PC_SMOKE_FAILED (rc=$rc; 124 = timeout)" >&2
  tail -20 "$log" >&2
  rm -f "$log"; exit 1
fi
rm -f "$log"
echo "PC_SMOKE_OK ($RUN)"

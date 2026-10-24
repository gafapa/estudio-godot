#!/usr/bin/env bash
# Render and inspect scenes at exact target resolutions. Usage errors fail before locking.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
usage() { echo 'Usage: screenshot.sh res://scene.tscn WxH|all [--fixture file] [--frames N] [--out file.png]' >&2; exit 2; }
[ "$#" -ge 2 ] || usage
SCENE="$1"; RES="$2"; shift 2
FIXTURE=""; FRAMES=10; OUT=""
while [ "$#" -gt 0 ]; do
  [ "$#" -ge 2 ] && [ -n "$2" ] && [[ "$2" != --* ]] || usage
  case "$1" in
    --fixture) FIXTURE="$2" ;;
    --frames) FRAMES="$2" ;;
    --out) OUT="$2" ;;
    *) usage ;;
  esac
  shift 2
done
[[ "$FRAMES" =~ ^[1-9][0-9]*$ ]] && [ "$FRAMES" -le 10000 ] || usage
[[ "$SCENE" == res://*.tscn ]] && [ -f "${SCENE#res://}" ] || usage
[ -z "$FIXTURE" ] || [ -f "${FIXTURE#res://}" ] || usage
[ "$RES" != all ] || [ -z "$OUT" ] || usage
valid_resolution() { [[ "$1" =~ ^([1-9][0-9]*)x([1-9][0-9]*)$ ]] && [ "${BASH_REMATCH[1]}" -le 16384 ] && [ "${BASH_REMATCH[2]}" -le 16384 ]; }
if [ "$RES" != all ]; then valid_resolution "$RES" || usage; fi
ALL_RES=({{SHOT_RES}})
PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
GODOT_REAL="${GODOT:-godot}"; export GODOT_REAL
. tools/lib/godot_guard.sh
godot_guard_acquire || exit 2
trap godot_guard_release EXIT
mkdir -p tools/out; touch tools/out/.gdignore
"$PY" tools/run_bounded.py "${SHOT_TIMEOUT:-120}" tools/godot_guarded.sh --headless --path . --import >tools/out/shot_import.log 2>&1 || { cat tools/out/shot_import.log >&2; exit 1; }
shot() {
  local resolution="$1" output="$2" log rc
  log="$(mktemp)"; rm -f -- "$output"
  GODOT_REQUIRE_RENDERING=1 "$PY" tools/run_bounded.py "${SHOT_TIMEOUT:-120}" tools/godot_guarded.sh --path . --windowed --position "${GODOT_SHOT_POSITION:--32000,-32000}" --resolution 320x240 --audio-driver Dummy --script tools/screenshot_runner.gd -- "$SCENE" "$resolution" "$FRAMES" "$output" "$FIXTURE" >"$log" 2>&1
  rc=$?
  if [ "$rc" = 0 ] && [ -s "$output" ] && grep -q SCREENSHOT_OK "$log" && ! grep -qE 'SCRIPT ERROR|Parse Error|Failed to load script|^ERROR:' "$log"; then
    grep SCREENSHOT_OK "$log"; rm -f "$log"; return 0
  fi
  echo "SCREENSHOT_FAILED $SCENE $resolution rc=$rc" >&2; tail -15 "$log" >&2; rm -f "$log"; return 1
}
NAME="$(basename "${SCENE%.*}")"; FAILED=0
if [ "$RES" = all ]; then
  for ITEM in "${ALL_RES[@]}"; do shot "$ITEM" "tools/out/${NAME}_${ITEM}.png" || FAILED=1; done
else
  shot "$RES" "${OUT:-tools/out/${NAME}_${RES}.png}" || FAILED=1
fi
exit "$FAILED"

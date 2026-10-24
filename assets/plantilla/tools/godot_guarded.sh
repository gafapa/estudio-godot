#!/usr/bin/env bash
# Headless by default; close only owned engines and yield machine time between runs.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib/godot_guard.sh"
REAL="${GODOT_REAL:-godot}"
PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
YIELD_SECONDS="${GODOT_YIELD_SECONDS:-5}"
[[ "$YIELD_SECONDS" =~ ^[1-9][0-9]*$ ]] && [ "$YIELD_SECONDS" -le 60 ] || { echo 'GODOT_YIELD_SECONDS must be from 1 to 60' >&2; exit 2; }
export GODOT_RUN_TIMEOUT="${GODOT_RUN_TIMEOUT:-120}"
CHILD=""; MACHINE_LOCK=""; CONTROL=""
cleanup() {
  local rc=$?
  trap '' INT TERM HUP
  if [ -n "$CHILD" ]; then
    touch "$CONTROL/cancel"
    wait "$CHILD" 2>/dev/null || true
    if [ "$(cat "$CONTROL/receipt" 2>/dev/null)" != verified-empty ]; then
      echo 'godot_guarded: UNVERIFIED closure; machine lock quarantined.' >&2
      mkdir "$MACHINE_LOCK.reap" 2>/dev/null || true
      godot_guard_release
      exit 3
    fi
  fi
  if [ -n "$CONTROL" ]; then
    rm -f -- "$CONTROL/cancel" "$CONTROL/receipt"
    rmdir "$CONTROL" 2>/dev/null || true
  fi
  [ -z "$MACHINE_LOCK" ] || _gg_release_owned "$MACHINE_LOCK"
  godot_guard_release
  # No engine or machine lease is held during this gap; other applications can run.
  if [ -n "$CHILD" ]; then
    echo "GODOT_YIELD: ${YIELD_SECONDS}s with owned engines closed and machine lease released" >&2
    sleep "$YIELD_SECONDS"
  fi
  exit "$rc"
}
trap cleanup EXIT
trap 'echo "godot_guarded: interrupted" >&2; exit 143' INT TERM HUP
godot_guard_acquire || exit 2
_GG_ME="$$ $(_gg_winpid $$)"
MACHINE_LOCK="${GODOT_MACHINE_LOCK:-${TEMP:-${TMPDIR:-/tmp}}/godot-studio-machine-engine.lock}"
MACHINE_LOCK="$(cygpath -u "$MACHINE_LOCK" 2>/dev/null || echo "$MACHINE_LOCK")"
_gg_wait "$MACHINE_LOCK" || exit 2
"$PY" "$HERE/wait_for_godot.py" --timeout "${GODOT_IDLE_WAIT:-30}" || exit $?
if [ -z "${GODOT_SHARED_DATA:-}" ] && [ -n "$_GG_TOP" ]; then
  GH="$_GG_TOP/tools/out/godot-home"
  mkdir -p "$GH/appdata" "$GH/local" "$GH/xdg/data" "$GH/xdg/config" "$GH/xdg/cache"
  APPDATA="$(cygpath -w "$GH/appdata" 2>/dev/null || echo "$GH/appdata")"
  LOCALAPPDATA="$(cygpath -w "$GH/local" 2>/dev/null || echo "$GH/local")"
  export APPDATA LOCALAPPDATA
  export XDG_DATA_HOME="$GH/xdg/data" XDG_CONFIG_HOME="$GH/xdg/config" XDG_CACHE_HOME="$GH/xdg/cache"
fi
ARGS=("$@")
if [ "${GODOT_REQUIRE_RENDERING:-0}" != 1 ]; then
  # Insert engine options before any user argument separator.
  ARGS=(--headless "${ARGS[@]}")
fi
CONTROL="$(mktemp -d "${TMPDIR:-/tmp}/studio-owned.XXXXXXXX")" || exit 3
export STUDIO_OWNED_CANCEL="$(cygpath -w "$CONTROL/cancel" 2>/dev/null || echo "$CONTROL/cancel")"
export STUDIO_OWNED_RECEIPT="$(cygpath -w "$CONTROL/receipt" 2>/dev/null || echo "$CONTROL/receipt")"
INTERRUPTED=0
trap 'INTERRUPTED=1' INT TERM HUP
"$PY" "$HERE/run_owned_godot.py" -- "$REAL" "${ARGS[@]}" &
CHILD=$!
trap 'echo "godot_guarded: interrupted" >&2; exit 143' INT TERM HUP
[ "$INTERRUPTED" = 0 ] || exit 143
wait "$CHILD"
RC=$?
exit "$RC"

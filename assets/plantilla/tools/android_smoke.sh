#!/usr/bin/env bash
# Test an existing Android device without uninstalling apps or stopping emulators.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
# Argument validation and device selection happen before acquiring a shared device lock.
SERIAL="$("$PY" tools/android_smoke.py --select-device "$@")" || exit $?
. tools/lib/godot_guard.sh
godot_guard_device_lock "$SERIAL" || exit 2
trap 'godot_guard_device_unlock "$SERIAL"' EXIT
trap 'exit 143' INT TERM HUP
export ANDROID_SERIAL="$SERIAL"
"$PY" tools/android_smoke.py "$@"
exit $?

#!/usr/bin/env bash
# Report GDScript formatting/lint failures after edits without changing files.
set -u
PY="${PYTHON:-python}"; command -v "$PY" >/dev/null 2>&1 || PY=python3
INPUT="$(cat)"
FILE="$(printf '%s' "$INPUT" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null | tr -d '\r')"
case "$FILE" in *.gd) ;; *) exit 0 ;; esac
case "$FILE" in */addons/*|*/godot-api/*) exit 0 ;; esac
[ -f "$FILE" ] || exit 0
OUTPUT=""
if ! RESULT="$("$PY" -m gdtoolkit.formatter --check "$FILE" 2>&1)"; then OUTPUT+="gdformat: file is not formatted (tools/lint.sh --fix)
"; fi
if ! RESULT="$("$PY" -m gdtoolkit.linter "$FILE" 2>&1)"; then OUTPUT+="$RESULT
"; fi
if [ -n "$OUTPUT" ]; then printf '%s' "$OUTPUT" >&2; exit 2; fi
exit 0

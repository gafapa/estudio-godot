#!/usr/bin/env bash
# Validate local JSON data and duplicate identifiers.
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
exec "$PY" -I tools/validate_data.py "$@"

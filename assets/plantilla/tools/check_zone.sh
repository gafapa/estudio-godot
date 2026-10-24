#!/usr/bin/env bash
# Validate ticket paths against immutable commit changes, including renames.
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
exec "$PY" tools/check_zone.py "$@"

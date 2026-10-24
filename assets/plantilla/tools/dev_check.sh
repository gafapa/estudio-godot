#!/usr/bin/env bash
# Focused development feedback; never replaces immutable delivery/integration CI.
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[ "$#" = 1 ] && [ -n "$1" ] || { echo 'Usage: dev_check.sh <test-file-or-directory>' >&2; exit 2; }
bash tools/lint.sh
bash tools/validate_data.sh
bash tools/test.sh "$1"
echo 'DEV_CHECK_ONLY: focused checks passed; delivery requires gate.sh on the committed SHA'

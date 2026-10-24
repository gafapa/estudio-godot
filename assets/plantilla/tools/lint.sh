#!/usr/bin/env bash
# Check or fix GDScript formatting and lint with pinned local tools.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

FIX=0
case "${1:-}" in
  --fix) FIX=1 ;;
  "") ;;
  *) echo "Usage: tools/lint.sh [--fix]" >&2; exit 2 ;;
esac

PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
find_tool() {
  if command -v "$1" >/dev/null 2>&1; then echo "$1"; return 0; fi
  local d scheme ext
  for scheme in nt_user posix_user; do
    d="$("$PY" -c "import sysconfig;print(sysconfig.get_path('scripts','$scheme'))" 2>/dev/null | tr -d '\r')"
    d="$(cygpath -u "$d" 2>/dev/null || echo "$d")"
    for ext in "" ".exe"; do
      if [ -x "$d/$1$ext" ] && [ -f "$d/$1$ext" ]; then echo "$d/$1$ext"; return 0; fi
    done
  done
  return 1
}
GDLINT="$(find_tool gdlint)" && GDFORMAT="$(find_tool gdformat)" || {
  echo "ERROR: gdtoolkit is missing. Run: python -m pip install -r tools/requirements.txt" >&2
  exit 2
}

FILES=()
while IFS= read -r f; do FILES+=("$f"); done < <(
  find src tests tools -name '*.gd' -not -path '*/addons/*' -not -path 'tools/godot-api/*' -not -path 'tools/out/*' | sort
)
if [ "${#FILES[@]}" -eq 0 ]; then echo "lint: no GDScript files"; exit 0; fi

RC=0
if [ "$FIX" = 1 ]; then
  "$GDFORMAT" "${FILES[@]}" 2>&1 | tail -2
fi
if ! OUT="$("$GDFORMAT" --check "${FILES[@]}" 2>&1)"; then
  echo "$OUT" | head -30
  echo "gdformat: unformatted files (run tools/lint.sh --fix)"
  RC=1
fi
if ! OUT="$("$GDLINT" "${FILES[@]}" 2>&1)"; then
  echo "$OUT" | head -60
  RC=1
fi
if [ "$RC" = 0 ]; then echo "lint OK (${#FILES[@]} files)"; else echo "lint FAILED"; fi
exit "$RC"

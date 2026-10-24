#!/usr/bin/env bash
# Dump the installed Godot API for local signature lookup.
set -eu
GODOT_REAL="${GODOT:-godot}"; export GODOT_REAL
GODOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/godot_guarded.sh"   # Guarded engine execution.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MAIN="$HERE"
if FIRST="$(git -C "$HERE" worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p' | head -1)" \
  && [ -n "$FIRST" ] && [ -d "$FIRST" ]; then
  MAIN="$FIRST"
fi
OUT="$MAIN/tools/godot-api"

FORCE=0
case "${1:-}" in
  --force) FORCE=1 ;;
  "") ;;
  *) echo "Usage: tools/dump_api.sh [--force]" >&2; exit 2 ;;
esac

. "$HERE/tools/lib/godot_guard.sh"
godot_guard_mutex api-dump || exit 2
trap 'godot_guard_unmutex api-dump' EXIT
VERSION="$("$GODOT" --version | tr -d '\r')"
if [ "$FORCE" = 0 ] && [ -f "$OUT/INDEX.txt" ] && [ "$(cat "$OUT/.version" 2>/dev/null)" = "$VERSION" ]; then
  echo "API already available for Godot $VERSION: $OUT (use --force to rebuild)"
  exit 0
fi

PY=""
for c in python python3; do
  if "$c" --version >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "ERROR: Python is required" >&2; exit 2; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"; godot_guard_unmutex api-dump' EXIT
"$GODOT" --headless --path "$HERE" --doctool "$TMP" > "$TMP/doctool.log" 2>&1 || {
  echo "ERROR: --doctool failed:" >&2; tail -15 "$TMP/doctool.log" >&2; exit 2; }
[ -d "$TMP/doc/classes" ] || { echo "ERROR: --doctool did not produce doc/classes" >&2; exit 2; }

mkdir -p "$TMP/xml"
cp "$TMP"/doc/classes/*.xml "$TMP/xml/"
for d in "$TMP"/modules/*/doc_classes "$TMP"/platform/*/doc_classes; do
  if [ -d "$d" ]; then cp "$d"/*.xml "$TMP/xml/"; fi
done

"$PY" -I - "$TMP/xml" "$TMP/INDEX.txt" <<'PYEOF'
import sys, glob, os
import xml.etree.ElementTree as ET

xml_dir, index_path = sys.argv[1], sys.argv[2]
lines = []
for path in sorted(glob.glob(os.path.join(xml_dir, "*.xml"))):
    root = ET.parse(path).getroot()
    cls = root.get("name")
    inh = root.get("inherits")
    lines.append(f"{cls} < {inh}" if inh else cls)

    def sig(m):
        args = []
        for p in m.findall("param"):
            a = f'{p.get("type")} {p.get("name")}'
            if p.get("default") is not None:
                a += f' = {p.get("default")}'
            args.append(a)
        return ", ".join(args)

    for tag in ("constructors", "methods", "operators", "annotations"):
        for m in root.findall(f"{tag}/*"):
            ret = m.find("return")
            r = ret.get("type") if ret is not None else "void"
            q = m.get("qualifiers")
            extra = f" [{q}]" if q else ""
            name = m.get("name")
            if tag == "constructors":
                name = "new"
            lines.append(f"{cls}.{name}({sig(m)}) -> {r}{extra}")
    for m in root.findall("members/member"):
        extra = f' = {m.get("default")}' if m.get("default") not in (None, "") else ""
        lines.append(f'{cls}.{m.get("name")} : {m.get("type")}{extra}')
    for m in root.findall("signals/signal"):
        lines.append(f'{cls}.{m.get("name")}({sig(m)}) [signal]')
    for m in root.findall("constants/constant"):
        enum = f' ({m.get("enum")})' if m.get("enum") else ""
        lines.append(f'{cls}.{m.get("name")} = {m.get("value")} [const]{enum}')

with open(index_path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")
PYEOF

mkdir -p "$OUT"
rm -f "$OUT/.version"          # A missing version marks an incomplete dump
rm -rf "$OUT/xml"
mv "$TMP/xml" "$OUT/xml"
mv "$TMP/INDEX.txt" "$OUT/INDEX.txt"
: > "$OUT/.gdignore"
printf '%s' "$VERSION" > "$OUT/.version"
echo "API dumped for Godot $VERSION"
echo "  classes:  $(ls "$OUT/xml" | wc -l)"
echo "  index:  $OUT/INDEX.txt ($(wc -l < "$OUT/INDEX.txt") lines)"
echo "  example: grep '^SurfaceTool\.' $OUT/INDEX.txt"

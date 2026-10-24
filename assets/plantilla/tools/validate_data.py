#!/usr/bin/env python3
"""Validate data JSON against local schemas and reject duplicate IDs/names."""
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("ERROR: jsonschema is missing. Run: python -m pip install -r tools/requirements.txt",
          file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCHEMAS = DATA / "schemas"
MAX_ERRORS_PER_FILE = 5


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)


def find_duplicates(node, path="$"):
    """Return duplicate identifier/name messages for object lists."""
    out = []
    if isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node):
            for key in ("id", "name"):
                vals = [x[key] for x in node if key in x]
                seen, dup = set(), set()
                for v in vals:
                    if isinstance(v, (str, int)):
                        (dup if v in seen else seen).add(v)
                if dup:
                    shown = ", ".join(sorted(map(str, dup))[:5])
                    out.append(f"{path}: '{key}' duplicated: {shown}")
        for i, x in enumerate(node):
            out += find_duplicates(x, f"{path}[{i}]")
    elif isinstance(node, dict):
        for k, v in node.items():
            out += find_duplicates(v, f"{path}.{k}")
    return out


def validate(path: Path) -> list[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"Unreadable JSON: {e}"]
    if not isinstance(doc, dict) or "$schema" not in doc:
        return ['does not declare "$schema"']
    schema_path = (path.parent / str(doc["$schema"])).resolve()
    if not schema_path.is_file():
        return [f'Schema not found: {doc["$schema"]}']
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except Exception as e:  # noqa: BLE001
        return [f"Invalid schema ({schema_path.name}): {e}"]
    errors = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: tuple(str(part) for part in e.absolute_path))
    msgs = []
    for e in errors[:MAX_ERRORS_PER_FILE]:
        loc = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in e.absolute_path)
        msgs.append(f"{loc}: {e.message[:160]}")
    if len(errors) > MAX_ERRORS_PER_FILE:
        msgs.append(f"... and {len(errors) - MAX_ERRORS_PER_FILE} more errors")
    return msgs + find_duplicates(doc)


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a).resolve() for a in argv]
    else:
        files = sorted(p for p in DATA.rglob("*.json") if SCHEMAS not in p.parents)
    bad = 0
    for f in files:
        msgs = validate(f)
        if msgs:
            bad += 1
            print(f"FAILED {rel(f)}")
            for m in msgs:
                print(f"   {m}")
    if bad:
        print(f"validate_data: {bad} of {len(files)} files with errors")
        return 1
    print(f"validate_data OK ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

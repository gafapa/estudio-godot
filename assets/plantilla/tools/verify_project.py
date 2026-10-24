#!/usr/bin/env python3
"""Verify project readiness. Quick checks are partial; only full engine checks certify VERIFY_OK."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--quick", "--rapido", action="store_true")
    args = parser.parse_args()
    root = Path(args.project).resolve()
    failures = []
    def fail(message):
        failures.append(message)
        print(f"[FAIL] {message}")
    def run(name, command, timeout=90):
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout)
            if result.returncode:
                fail(f"{name}: {result.stdout[-2000:]} {result.stderr[-1000:]}")
                return False
            print(f"[OK] {name}: {result.stdout.strip().splitlines()[-1] if result.stdout.strip() else 'passed'}")
            return True
        except (OSError, subprocess.TimeoutExpired) as error:
            fail(f"{name}: {error}")
            return False
    try:
        import yaml
    except ImportError:
        print("VERIFY_FAILED: install tools/requirements.txt (PyYAML is required)")
        return 2
    import shutil
    bash = shutil.which("bash")
    if not bash and os.name == "nt" and shutil.which("git"):
        bash = str(Path(shutil.which("git")).parent.parent / "bin/bash.exe")
    if not bash or not Path(bash).exists():
        fail("Bash not found (Git Bash on Windows)")
    required = ["CLAUDE.md", "project.godot", "docs/AGENTES.md", "docs/PLAN.md", "docs/DIRECTOR.md", "docs/VISION.md", ".claude/settings.json", ".claude/skills/sprint/SKILL.md", "tools/gate.sh", "tools/test.sh", "tools/hooks/pre-push", "docs/design/gameplay.md", "docs/design/personajes.md", "docs/design/ux/pantallas.md", "docs/referencias/mecanicas.md"]
    for relative in required:
        if not (root / relative).is_file():
            fail(f"Missing {relative}")
    for folder in (root / "docs", root / ".claude"):
        for path in folder.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if re.search(r"\{\{[A-Z_]+\}\}|\b(?:TODO|ADAPTAR)\b", text):
                fail(f"Unfinished personalization: {path.relative_to(root)}")
            if text.startswith("---\n"):
                try:
                    metadata = yaml.safe_load(text.split("---", 2)[1])
                    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str) or not isinstance(metadata.get("description"), str):
                        raise ValueError("name and description strings are required")
                    if not re.fullmatch(r"[a-z0-9-]{1,64}", metadata["name"]):
                        raise ValueError("Invalid name")
                except (yaml.YAMLError, ValueError, IndexError) as error:
                    fail(f"Invalid metadata {path.relative_to(root)}: {error}")
    for relative in ("CLAUDE.md", "project.godot"):
        path = root / relative
        if path.is_file() and re.search(r"\{\{[A-Z_]+\}\}|\b(?:TODO|ADAPTAR)\b", path.read_text(encoding="utf-8")):
            fail(f"Unfinished personalization: {relative}")
    try:
        json.loads((root / ".claude/settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        fail(f"Invalid hook settings: {error}")
    for path in (root / "tools").rglob("*"):
        if not path.is_file() or "out" in path.relative_to(root / "tools").parts:
            continue
        if path.suffix == ".sh" or path.name == "pre-push":
            if b"\r" in path.read_bytes():
                fail(f"CRLF shell script: {path.relative_to(root)}")
    try:
        hook = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=root, capture_output=True, text=True)
        configured = hook.stdout.strip()
        if configured != "tools/hooks":
            hook_path = Path(configured) if configured else root / ".git/hooks"
            if not hook_path.is_absolute():
                hook_path = root / hook_path
            chained = hook_path / "pre-push"
            if not chained.is_file() or "tools/hooks/pre-push" not in chained.read_text(encoding="utf-8", errors="replace"):
                fail("Existing pre-push hook must chain tools/hooks/pre-push; existing configuration was preserved")
    except OSError as error:
        fail(f"Git: {error}")
    run("Python dependencies", [sys.executable, "-c", "import gdtoolkit,jsonschema,yaml"])
    if bash:
        run("lint", [bash, "tools/lint.sh"])
        run("data", [bash, "tools/validate_data.sh"])
    if not args.quick and not failures:
        if not (root / "addons/gdUnit4/bin/GdUnitCmdTool.gd").is_file() or not (root / "addons/gdUnit4/plugin.cfg").is_file():
            fail("Compatible GdUnit4 plugin and command runner are required")
        environment = dict(os.environ)
        environment["GODOT_REAL"] = environment.get("GODOT", "godot")
        try:
            version = subprocess.run([bash, "tools/godot_guarded.sh", "--version"], cwd=root, env=environment, capture_output=True, text=True, timeout=30)
            expected = re.search(r"Godot (4\.\d+(?:\.\d+)?)", (root / "CLAUDE.md").read_text(encoding="utf-8"))
            actual = re.match(r"(4\.\d+(?:\.\d+)?)(?:\.|$)", version.stdout.strip())
            if version.returncode or not expected or not actual or actual.group(1) != expected.group(1):
                fail(f"Godot version mismatch or unavailable: {version.stdout.strip()} {version.stderr.strip()}")
        except (OSError, subprocess.TimeoutExpired) as error:
            fail(f"Godot: {error}")
        if not failures:
            run("engine API", [bash, "tools/dump_api.sh"], timeout=180)
            run("nonempty tests", [bash, "tools/test.sh"], timeout=1300)
    if failures:
        print(f"VERIFY_FAILED ({len(failures)})")
        return 1
    print("VERIFY_PARTIAL_OK: engine execution, exports and devices not certified" if args.quick else "VERIFY_OK: engine tests passed; export/device qualification is separate")
    return 0


if __name__ == "__main__":
    sys.exit(main())

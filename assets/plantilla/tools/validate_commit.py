#!/usr/bin/env python3
"""Run CI on an immutable commit in a unique, disposable detached worktree."""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True

from validation_cache import fingerprint, load_receipt, save_receipt
from workflow_metrics import record


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git failed")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--ticket")
    parser.add_argument("--base", default="main")
    parser.add_argument("--fresh", action="store_true", help="Run checks even if reusable evidence exists")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    worktree = None
    added = False
    started = time.monotonic()
    returncode = 2
    cache_hit = False
    commit = ""
    try:
        commit = git(root, "rev-parse", "--verify", f"{args.commit}^{{commit}}")
        if args.ticket:
            base = git(root, "rev-parse", "--verify", f"{args.base}^{{commit}}")
            result = subprocess.run([sys.executable, str(root / "tools/check_zone.py"), commit, args.ticket, base], cwd=root)
            if result.returncode:
                returncode = result.returncode
                return result.returncode
        git_binary = Path(shutil.which("git") or "git")
        bash = shutil.which("bash")
        if not bash and os.name == "nt":
            candidate = git_binary.resolve().parent.parent / "bin/bash.exe"
            if candidate.is_file():
                bash = str(candidate)
        if not bash:
            raise RuntimeError("Bash is required (Git Bash on Windows)")
        output_root = root / "tools/out/validation"
        output_root.mkdir(parents=True, exist_ok=True)
        output_root = output_root.resolve()
        if not output_root.is_relative_to(root):
            raise RuntimeError("Validation output must stay inside the project")
        environment = dict(os.environ)
        # Lock inheritance applies only within the same checkout, never to this snapshot.
        environment.pop("GODOT_LOCK_HELD", None)
        environment.pop("GODOT_LOCK_CHECKOUT", None)
        quick = bool(args.quick or args.ticket)
        # External submodules and symlink targets are not fully identified by the SHA.
        external = any(line.startswith(("160000 ", "120000 ")) for line in
                       git(root, "ls-tree", "-r", commit).splitlines())
        key = fingerprint(root, commit, bash, environment) if quick and not external else None
        cache_directory = output_root / "cache"
        label = "GATE" if args.ticket else "COMMIT_CI"
        receipt = load_receipt(cache_directory, key) if key and not args.fresh else None
        if receipt:
            cache_hit = True
            returncode = 0
            print(f"{label}_OK commit={commit} cached=true evidence={receipt['log']}", flush=True)
            return 0
        if key:
            # A fresh attempt supersedes older evidence, including when it fails.
            (cache_directory / f"{key}.json").unlink(missing_ok=True)
        run_directory = Path(tempfile.mkdtemp(prefix=f"{commit[:12]}-", dir=output_root))
        worktree = run_directory / "snapshot"
        git(root, "worktree", "add", "--detach", str(worktree), commit)
        added = True
        command = [bash, "tools/ci.sh", "--snapshot"]
        if quick:
            command.append("--quick")
        log = run_directory / "ci.log"
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(command, cwd=worktree, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        print(log.read_text(encoding="utf-8", errors="replace")[-12000:], end="", flush=True)
        returncode = result.returncode
        if returncode != 0 and key:
            (cache_directory / f"{key}.json").unlink(missing_ok=True)
        if returncode == 0 and key:
            # Tool/environment changes during the run invalidate reuse.
            if fingerprint(root, commit, bash, environment) == key:
                try:
                    save_receipt(cache_directory, key, commit, log)
                except (OSError, ValueError) as error:
                    print(f"WARNING: Could not cache validation: {error}", file=sys.stderr)
        print(f"{label}_{'OK' if result.returncode == 0 else 'FAILED'} commit={commit} cached=false evidence={log}", flush=True)
        return result.returncode
    except (OSError, RuntimeError) as error:
        returncode = 2
        print(f"VALIDATION_FAILED: {error}", file=sys.stderr)
        return 2
    finally:
        if added:
            try:
                git(root, "worktree", "remove", "--force", str(worktree))
            except RuntimeError as error:
                print(f"WARNING: Could not remove owned worktree {worktree}: {error}", file=sys.stderr)
        elif worktree and worktree.is_dir():
            worktree.rmdir()
        try:
            record(root, "validation", time.monotonic() - started, args.ticket or "",
                   "passed" if returncode == 0 else "failed", commit=commit, cache_hit=cache_hit,
                   mode="quick" if args.quick or args.ticket else "full")
        except (OSError, ValueError) as error:
            print(f"WARNING: Could not record validation timing: {error}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

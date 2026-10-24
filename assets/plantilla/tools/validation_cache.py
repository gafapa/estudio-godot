#!/usr/bin/env python3
"""Conservative local cache for successful quick CI, never human review or exports."""
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

SCHEMA = 1
MAX_AGE_SECONDS = 24 * 60 * 60


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(root, commit, bash, environment):
    """Return None when required tool identity cannot be established."""
    try:
        if any(environment.get(name) for name in
               ("BASH_ENV", "ENV", "PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "LD_LIBRARY_PATH")):
            return None
        binaries = {}
        for name, command in (("python", sys.executable), ("bash", bash),
                              ("git", "git"), ("godot", environment.get("GODOT", "godot"))):
            resolved = shutil.which(command, path=environment.get("PATH"))
            if not resolved:
                return None
            path = Path(resolved).resolve()
            binaries[name] = {"path": str(path), "sha256": digest_file(path)}
        # Dirty orchestration tools must not reuse results produced by older tools.
        tools = {}
        for directory, children, files in os.walk(root / "tools"):
            children[:] = sorted(name for name in children if name not in ("out", "__pycache__"))
            for name in sorted(files):
                path = Path(directory) / name
                tools[str(path.relative_to(root))] = digest_file(path)
        packages = sorted((item.metadata["Name"], item.version,
                           hashlib.sha256((item.read_text("RECORD") or "").encode()).hexdigest())
                          for item in importlib.metadata.distributions())
        payload = {"schema": SCHEMA, "commit": commit, "mode": "quick", "tools": tools,
                   "binaries": binaries, "packages": packages,
                   "platform": platform.platform(), "python": sys.version,
                   "environment": sorted((name, value) for name, value in environment.items()
                                         if name not in ("_", "SHLVL", "PWD", "OLDPWD"))}
        # Persist only a digest, never raw environment variables or their secrets.
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    except (OSError, ValueError, TypeError, KeyError):
        return None


def load_receipt(directory, key):
    try:
        if not directory.resolve().is_relative_to(directory.parent.resolve()):
            return None
        receipt = json.loads((directory / f"{key}.json").read_text(encoding="utf-8"))
        age = time.time() - receipt["completed_at"]
        log = (directory.parent / receipt["log"]).resolve()
        if (receipt["schema"] != SCHEMA or receipt["key"] != key
                or receipt["returncode"] != 0 or receipt["mode"] != "quick"
                or not 0 <= age <= MAX_AGE_SECONDS
                or not log.is_relative_to(directory.parent.resolve())
                or digest_file(log) != receipt["log_sha256"]):
            return None
        return receipt
    except (OSError, ValueError, TypeError, KeyError):
        return None


def save_receipt(directory, key, commit, log):
    directory.mkdir(parents=True, exist_ok=True)
    if not directory.resolve().is_relative_to(directory.parent.resolve()):
        raise ValueError("Cache directory must stay inside validation output")
    receipt = {"schema": SCHEMA, "key": key, "commit": commit, "mode": "quick",
               "returncode": 0, "completed_at": time.time(),
               "log": log.relative_to(directory.parent).as_posix(),
               "log_sha256": digest_file(log)}
    temporary = directory / f"{key}.{os.getpid()}.tmp"
    try:
        temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, directory / f"{key}.json")
    finally:
        temporary.unlink(missing_ok=True)

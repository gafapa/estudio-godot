#!/usr/bin/env python3
"""Validate both sides of changes against a ticket's relative POSIX path globs."""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def path_pattern(pattern):
    if pattern.startswith("/") or ".." in pattern.split("/") or "\\" in pattern:
        raise ValueError(f"Invalid relative path pattern: {pattern}")
    parts = []
    index = 0
    while index < len(pattern):
        if pattern[index:index+3] == "**/":
            parts.append("(?:.*/)?")
            index += 3
        elif pattern[index:index+2] == "**":
            parts.append(".*")
            index += 2
        elif pattern[index] == "*":
            parts.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            parts.append("[^/]")
            index += 1
        else:
            parts.append(re.escape(pattern[index]))
            index += 1
    return re.compile("^" + "".join(parts) + "$")


def check_zone(commit, ticket, base="main"):
    commit = git("rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    base = git("rev-parse", "--verify", f"{base}^{{commit}}").decode().strip()
    definitions = []
    for source in Path("docs/backlog").glob("*.md"):
        active = False
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.startswith("### "):
                active = bool(re.match(r"^### " + re.escape(ticket) + r"(?:\s|$)", line))
            if active and ("**Allowed paths:**" in line or "**Puede tocar:**" in line):
                definitions.append(line.split(":**", 1)[1].strip())
    if len(definitions) != 1:
        raise ValueError(f"Expected one Allowed paths definition for {ticket}, got {len(definitions)}")
    patterns = re.findall(r"`([^`]+)`", definitions[0])
    if not patterns:
        raise ValueError("Allowed paths must contain backtick-delimited patterns")
    compiled = [path_pattern(pattern) for pattern in patterns]
    # --no-renames exposes the old path as a deletion and the new path as an addition.
    files = git("diff", "--no-renames", "--name-only", "-z", f"{base}...{commit}").decode("utf-8").split("\0")
    outside = [name for name in files if name and not any(pattern.fullmatch(name) for pattern in compiled)]
    if outside:
        for name in outside:
            print(f"OUTSIDE_ZONE: {name}", file=sys.stderr)
        return 1
    print(f"ZONE_OK {ticket} commit={commit} base={base}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit")
    parser.add_argument("ticket")
    parser.add_argument("base", nargs="?", default="main")
    args = parser.parse_args()
    try:
        return check_zone(args.commit, args.ticket, args.base)
    except (OSError, ValueError) as error:
        print(f"ZONE_FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

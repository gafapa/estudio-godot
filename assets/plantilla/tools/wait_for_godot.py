#!/usr/bin/env python3
"""Wait for machine-wide Godot idleness without terminating any process."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

QUERY = r"""$ErrorActionPreference='Stop'; $items=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^Godot.*\.exe$' } | Select-Object ProcessId,Name); ConvertTo-Json -InputObject $items -Compress"""


def inventory():
    if os.name != "nt":
        result = subprocess.run(["ps", "-eo", "pid=,comm="], capture_output=True, text=True, timeout=10, check=True)
        rows = []
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 1)
            if len(fields) == 2 and "godot" in fields[1].lower():
                rows.append({"ProcessId": int(fields[0]), "Name": fields[1]})
        return rows
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if not executable:
        raise RuntimeError("Windows process inventory is unavailable")
    result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", QUERY],
                            capture_output=True, text=True, timeout=30, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    rows = json.loads(result.stdout.lstrip("\ufeff").strip())
    if not isinstance(rows, list):
        raise RuntimeError("Invalid Godot process inventory")
    for row in rows:
        if (not isinstance(row, dict) or type(row.get("ProcessId")) is not int
                or row["ProcessId"] <= 0 or not isinstance(row.get("Name"), str)
                or not row["Name"].lower().startswith("godot")):
            raise RuntimeError("Invalid Godot process identity")
    return rows


def wait_for_idle(timeout, detect=inventory, now=time.monotonic, pause=time.sleep):
    deadline = now() + timeout
    previous = None
    while True:
        rows = detect()
        if not rows:
            return True
        identities = tuple(sorted(row["ProcessId"] for row in rows))
        if identities != previous:
            print("GODOT_WAIT: existing Godot PIDs " + ",".join(map(str, identities)),
                  file=sys.stderr, flush=True)
            previous = identities
        remaining = deadline - now()
        if remaining <= 0:
            print("GODOT_WAIT_TIMEOUT: existing engines left untouched", file=sys.stderr)
            return False
        pause(min(5, remaining))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    if args.timeout < 0:
        parser.error("timeout must be nonnegative")
    try:
        return 0 if wait_for_idle(args.timeout) else 2
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("GODOT_INVENTORY_FAILED: " + str(error), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Run a command with a mandatory timeout; terminate the owned process tree on expiry."""
import os
import signal
import subprocess
import sys


def main():
    seconds = int(sys.argv[1])
    if not 1 <= seconds <= 86400:
        raise ValueError("Timeout must be between 1 and 86400 seconds")
    command = sys.argv[2:]
    if os.name == "nt" and command and command[0].endswith(".sh"):
        # Windows cannot CreateProcess a shell script directly.
        import shutil
        from pathlib import Path
        bash = shutil.which("bash") or str(Path(shutil.which("git")).parent.parent / "bin/bash.exe")
        command = [bash, *command]
    process = subprocess.Popen(command, start_new_session=(os.name != "nt"),
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                               stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=sys.stderr)
    try:
        return process.wait(timeout=seconds)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name != "nt":
                os.killpg(process.pid, signal.SIGKILL)
            process.kill()
            process.wait()
        print(f"TIMEOUT: command exceeded {seconds}s", file=sys.stderr)
        return 124


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, IndexError) as error:
        print(f"RUN_FAILED: {error}", file=sys.stderr)
        sys.exit(2)

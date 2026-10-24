#!/usr/bin/env python3
"""Fail closed on engine failures, missing discovery, malformed summaries or orphan nodes."""
import re
import sys
from pathlib import Path


def evaluate(log, returncode):
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", log).replace("\r", "")
    if returncode not in (0, 101):
        return False, f"Engine/test runner failed with exit code {returncode}"
    if "No test cases found" in text:
        return False, "Test discovery returned no test cases"
    if re.search(r"SCRIPT ERROR|Parse Error|Failed to load script|^ERROR:", text, re.MULTILINE):
        return False, "Engine reported an error"
    summaries = re.findall(r"^Overall Summary:\s*(.*)$", text, re.MULTILINE)
    if not summaries:
        return False, "Missing GdUnit4 summary"
    summary = summaries[-1]
    values = {}
    for key in ("test cases", "errors", "failures", "skipped", "orphans"):
        match = re.search(r"\b(\d+) " + key + r"\b", summary)
        if not match:
            return False, f"Malformed GdUnit4 summary: missing {key}"
        values[key] = int(match.group(1))
    passed = values["test cases"] - values["errors"] - values["failures"] - values["skipped"]
    if passed <= 0 or values["errors"] or values["failures"] or values["orphans"]:
        return False, summary
    return True, summary + (" (runner warnings, rc=101)" if returncode == 101 else "")


if __name__ == "__main__":
    success, message = evaluate(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"), int(sys.argv[2]))
    print(f"TESTS_{'OK' if success else 'FAILED'}: {message}")
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Record local measured workflow times and summarize them without network access."""
import argparse
import collections
import datetime
import json
import math
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASES = ("implementation", "validation", "review", "wait", "integration", "escaped_defect")


def record(root, phase, seconds, ticket="", outcome="passed", **details):
    if phase not in PHASES or not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Phase must be supported and seconds must be finite and nonnegative")
    directory = root / "tools/out/metrics"
    directory.mkdir(parents=True, exist_ok=True)
    if not directory.resolve().is_relative_to(root.resolve()):
        raise ValueError("Metrics output must stay inside the project")
    event = {"phase": phase, "seconds": seconds, "ticket": ticket, "outcome": outcome,
             "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), **details}
    path = directory / f"{uuid.uuid4().hex}.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(event, stream)
        stream.write("\n")
    return path


def summarize(root):
    totals = collections.defaultdict(float)
    counts = collections.Counter()
    cache_hits = failures = defects = 0
    for path in (root / "tools/out/metrics").glob("*.json"):
        event = json.loads(path.read_text(encoding="utf-8"))
        phase, seconds = event["phase"], event["seconds"]
        if phase not in PHASES or not math.isfinite(seconds) or seconds < 0:
            raise ValueError(f"Invalid metric: {path}")
        totals[phase] += seconds
        counts[phase] += 1
        cache_hits += bool(event.get("cache_hit", False))
        failures += event["outcome"] == "failed"
        defects += phase == "escaped_defect"
    return {"seconds_by_phase": dict(totals), "events_by_phase": dict(counts),
            "cache_hits": cache_hits, "failed_events": failures, "escaped_defects": defects}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("record")
    add.add_argument("--phase", choices=PHASES, required=True)
    add.add_argument("--seconds", type=float, required=True)
    add.add_argument("--ticket", default="")
    add.add_argument("--outcome", choices=("passed", "failed", "pending"), default="passed")
    commands.add_parser("report")
    args = parser.parse_args()
    try:
        if args.command == "record":
            print(record(ROOT, args.phase, args.seconds, args.ticket, args.outcome))
        else:
            print(json.dumps(summarize(ROOT), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"METRICS_FAILED: {error}\n")


if __name__ == "__main__":
    main()

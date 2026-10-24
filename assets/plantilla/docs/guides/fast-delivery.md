# Faster delivery with unchanged acceptance criteria

Use this workflow during normal production. Keep Sol/Luna model assignments and medium/low reasoning; optimize duplicated work and handoffs before changing resources.

## Choose the smallest useful delivery unit

Group small, related changes when they share an owner, dependencies, coherent Allowed paths and one observable player or tooling outcome. Do not create a separate design, implementation and documentation ticket for each trivial edit. Keep each delivery reviewable and independently reversible. Split unrelated behavior and keep saves, contracts, migrations, economy, determinism and shared foundations separate from routine changes. Assign the highest applicable risk to a grouped ticket.

For small changes to an approved system, the ticket itself can be the specification: objective, relevant context, paths, exclusions, criteria and verification method. Update existing design documents only when decisions change. New systems still need the appropriate design review; critical architectural decisions still need contracts, fixtures and ADRs. Do not generate documents merely to satisfy a template.

## Development feedback and delivery

During implementation, run `bash tools/dev_check.sh tests/unit/<system>` or the relevant existing test file/directory. It runs lint, data checks and a nonempty targeted suite. Choose tests from affected behavior and dependencies; broaden immediately for shared changes or unexplained failures. This command is development feedback, never ticket approval.

Before delivery, commit and run `bash tools/gate.sh <SHA> <ID> [base]`. The gate always checks ownership and runs or verifies reusable evidence for lint, data and the complete nonempty test suite. The quick label excludes exports, not tests. Run fresh checks for high-risk delivery:

```bash
python tools/validate_commit.py --commit <SHA> --ticket <ID> --base <base> --quick --fresh
```

## Reuse machine evidence, preserve independent judgment

Successful quick CI can be reused for at most 24 hours when the SHA, quick mode, orchestration tools, executable hashes, installed package metadata, OS/Python and environment fingerprint match. Receipts reference a retained log with a checked digest under `tools/out/validation/`. Raw environment values are not stored in receipts. Missing, damaged or expired evidence triggers execution. Failures are never cached. Ownership checks run on every ticket request, including cache hits.

Reuse is disabled when tools cannot be identified, the commit contains symlinks/submodules, or external shell/Python/library overrides prevent conservative identification. Use `--fresh` for external runtime dependencies not represented by the fingerprint, suspected flaky behavior, changed drivers/system state, or a result that needs reproduction. The cache is local optimization evidence, not an attestation against malicious modifications. Do not cache review verdicts, screenshots, listening checks, export artifacts or device qualification. Full CI always runs.

QA and code reviewers may cite reused machine evidence, but must independently examine the assigned SHA, reproduce acceptance scenarios and collect their own behavioral or review evidence. For low/medium-risk tickets, one qualified non-author reviewer may cover QA plus applicable technical, visual and gameplay review. Record each required criterion and verdict explicitly; do not replace missing visual/gameplay competence with a generic approval. High-risk tickets retain separate QA and technical review, adversarial tests and applicable specialist reviews.

When separate reviews are required, start them concurrently after the SHA and machine evidence are ready. Give each reviewer the ticket, spec, base and SHA without author conclusions. Use separate output directories and review worktrees for runtime work. Respect Godot/device locks and available capacity; do not launch overlapping mutations. Integration remains sequential.

Follow [quiet Godot testing](quiet-godot-tests.md): headless where suitable, bounded engine invocations, verified owned-process closure and a five-second machine-lease-free gap between runs. Faster delivery must not monopolize the machine or leave engines running. Use parallelism for inspection and design while engine runs remain cooperative.

## Integration and milestones

Run `bash tools/ci.sh --quick --commit <merge-SHA> --fresh` after integration and inspect affected captures. A different merge SHA needs its own evidence, even if branch checks passed. Full platform CI, human playtests where available and milestone qualification remain required by their existing criteria. Exports are not repeated for every internal change unless the affected platform/build behavior warrants them.

## Measure elapsed work and escaped defects

Immutable validation automatically records elapsed time, SHA, mode, result and cache-hit status in local `tools/out/metrics/` event files. Record other phases from observed elapsed time, not estimates:

```bash
python tools/workflow_metrics.py record --phase implementation --seconds 420 --ticket M1-01
python tools/workflow_metrics.py record --phase review --seconds 120 --ticket M1-01
python tools/workflow_metrics.py record --phase wait --seconds 35 --ticket M1-01 --outcome pending
python tools/workflow_metrics.py record --phase integration --seconds 40 --ticket M1-01
python tools/workflow_metrics.py record --phase escaped_defect --seconds 0 --ticket BUG-01 --outcome failed
python tools/workflow_metrics.py report
```

An escaped defect is a unique issue discovered after integration; record it once with its bug ticket and severity in that ticket. Keep phase intervals disjoint for each worker. Summed worker durations can overlap across agents and are not wall-clock delivery time. The report counts recorded events and failures, not a quality score. In the milestone retrospective compare similar ticket classes, validation reuse, time waiting and escaped defect severity/count. Report missing observations; do not claim a measured speedup or unchanged quality from configuration alone.

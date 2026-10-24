# Quiet, cooperative Godot tests

Prefer headless tests for import, parsing, unit/integration rules, data and smoke checks. `tools/godot_guarded.sh` injects `--headless` by default, which uses headless display and dummy audio. Do not open the editor/project manager for automated tests. A headless pass does not qualify rendered appearance, audible quality or physical interaction.

## Share machine time

Run bounded engine sessions through the guard. It takes a machine lease shared by installed studios, checks for existing Godot processes, and waits up to `GODOT_IDLE_WAIT` (default 30 seconds) without touching them. If another engine remains active, return a pending/blocked test result instead of opening another instance. Noncooperating tools can still race a process inventory; the lease coordinates tools using the same path.

After every engine invocation, including import, close the owned process tree, verify closure, release the machine lease and yield for five seconds before the next invocation. No machine lease or owned engine remains during this gap. `GODOT_YIELD_SECONDS` accepts 1–60 seconds; the default is 5 and zero is rejected. Keep normal suites small enough to return machine time regularly. `GODOT_RUN_TIMEOUT` defaults to 120 seconds and bounds each invocation; change it only for a justified longer test, keeping the gap between invocations. Do not run continuous engine/retry loops.

The default shared lease is `godot-studio-machine-engine.lock` in the host temporary directory, independent of repository/worktree. Other cooperating applications can use the same path through `GODOT_MACHINE_LOCK`. Releasing a lease and yielding gives them an opportunity, not a guarantee of fair scheduling.

## Always close only owned processes

The guard launches through `tools/run_owned_godot.py`. On Windows a private kill-on-close Job Object contains the engine and descendants atomically; console subprocesses are hidden. The helper terminates residual owned descendants on normal exit, failure, cancellation or timeout and verifies the private job is empty before writing its closure receipt. On POSIX, a private process group is terminated and checked; cross-platform qualification must be reported separately.

The guard releases its lease only after a verified closure receipt. An unverified shutdown fails the run and quarantines the lease for inspection. Never remove a quarantine or kill an unrelated editor to force a retry. Preserve the user's existing editors and other applications; do not use global process-name termination.

## Tests requiring rendering

Only explicitly rendered checks set `GODOT_REQUIRE_RENDERING=1`. `tools/screenshot.sh` does this for its actual capture, uses dummy audio and positions the window offscreen; imports remain headless. Use a bounded capture and close it immediately. Do not silently substitute headless images for a real rendering check. Leave manual interaction/listening pending when it would interrupt the user and has not been requested.

Keep stdout/log evidence with engine version, test count and exit status. Confirm `GODOT_OWNED_CLEANUP_OK ... active=0` and `GODOT_YIELD` in engine logs; run a read-only process inventory after the batch to confirm no owned engine remains. Missing engine/addon or an active unrelated engine is a limitation, never a passed test.

Source: [Godot command-line reference](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html).

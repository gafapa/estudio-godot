# {{GAME_NAME}}

{{PITCH}}

TODO: Add concrete pillars and genre constraints from docs/VISION.md.

## Language

All project documentation, code identifiers, comments, docstrings, technical reports and commit messages must be in English. Game-facing text and localization follow the game's selected languages.

## Operating mode

Mode: **{{MODE}}**. Automatic mode makes reversible decisions within scope and records them in docs/DIRECTOR.md; gated mode waits at creative and milestone decisions. Honor existing authorization. Seek missing authorization before spending, publication or destruction of user work, after preparing a reviewable result. Inspect remotes before authorized pushes; do not assume privacy.

The main session is the Producer. Delegate only when supported and authorized; otherwise work sequentially and disclose that review was not independent. The Architect writes contracts and fixtures; the Producer approves and integrates them. docs/AGENTES.md is the canonical ownership and review policy.

Use docs/guides/fast-delivery.md to group coherent small tickets, keep specifications proportional and reuse matching machine evidence. A qualified non-author reviewer may combine low/medium-risk review responsibilities with explicit results for each required criterion; high-risk work keeps separate QA/technical review. Launch separate reviews concurrently only with isolated outputs, adequate capacity and runtime locks.

## Rigor and concurrency

Rigor: **light** for M0-M1; standard for M2-M4; full for critical systems. ESTUDIO_WIP defaults to 6 but must fit available agent capacity. GODOT_SLOTS defaults to CPU cores / 4, clamped to 1-4. Launch disjoint zones and reserve review capacity. All Godot runs use tools wrappers.

Follow docs/guides/quiet-godot-tests.md: headless and silent by default, one machine-guarded engine invocation at a time, bounded execution, verified closure of owned processes and a five-second lease-free gap after each invocation. Existing Godot processes are left untouched. Only genuine rendering checks opt out of headless; screenshots use a bounded offscreen window. Never leave Godot running after a test.

## Architecture

Typed GDScript; rules separated from presentation where practical; seeded RNG per subsystem; injectable clock; validated commands; versioned saves/migrations; schema-validated balance data; translation keys for game text. Local development telemetry is disabled in release. Contract changes need the Architect, ADR, fixtures, consumer updates and Producer approval.

TODO: Specify genre exceptions, performance budgets and known traps.

## Commands

- `bash tools/lint.sh [--fix]`: format and lint GDScript.
- `bash tools/validate_data.sh [files...]`: validate local data and duplicate IDs.
- `bash tools/test.sh [-v] [path]`: nonempty GdUnit4 suite; failed or empty discovery is an error.
- `bash tools/dev_check.sh <test-path>`: focused development feedback; never substitutes for delivery/integration CI.
- `bash tools/gate.sh <commit-or-branch> <ticket> [base]`: resolve immutable SHAs, check zone and validate in a unique detached worktree. Evidence identifies the commit.
- `bash tools/ci.sh [--quick] [--isolated] [--commit SHA] [--fresh]`: local CI; isolated modes validate a clean commit. Quick runs the complete test suite without exports and may reuse matching successful receipts. Use --fresh for integrated SHAs or suspected external/flaky changes. Full CI always executes Windows/Linux exports and PC smoke; presets are created by M0-01.
- `python tools/workflow_metrics.py record --phase review --seconds <measured-seconds> --ticket <ID>` and `report`: local phase times, validation cache hits and recorded escaped defects. Validation times are recorded automatically.
- `tools/hooks/pre-push`: validates each outgoing commit from Git input. Preserve and chain existing hooks.
- `bash tools/screenshot.sh res://scene.tscn WxH|all [--fixture path] [--frames N] [--out path]`: real rendering at {{SHOT_RES}}; inspect PNGs.
- `bash tools/export.sh windows|linux|android [debug|release]`: local build, no publication.
- `bash tools/pc_smoke.sh [--no-export] [--linux]`: exported game with --smoke.
- `bash tools/android_smoke.sh [--no-export] [--scene res://scene.tscn] [--arg key=value] [--perf N] [--shot N] [--wait N]`: update APK without deleting application data. Select an existing device or start a dedicated AVD separately; no automatic emulator startup/shutdown. Requires a debuggable test build. Preserves prior launch files and stay-awake settings.
- `bash tools/user_dir.sh`: current checkout's isolated user directory.
- `bash tools/dump_api.sh [--force]`: installed engine API.
- `bash tools/playtest.sh <persona> [minutes] [seed]`: implemented by M0-04; unavailable until its criteria pass.
- `bash tools/balance.sh`: implement when needed; do not claim it already exists.

## Environment and Git

Godot {{GODOT_VERSION}}. Platforms: {{PLATFORMS}}. Device: {{DEVICE}}.
Python 3.10+ and tools/requirements.txt; compatible GdUnit4 in addons/gdUnit4.
Vendor GdUnit4 in the reviewed commit. Isolated checks do not copy uncommitted addons.

Keep main playable. Commit to feat/<ID>-<slug> or fix/<ID>-<slug>; integrate sequentially after approval. Run tools/ci.sh --quick --commit <merge-SHA> --fresh and inspect affected captures before marking INTEGRATED. High-risk delivery also uses fresh immutable validation. No force push, committed secrets or automatic publication. Record pending engine/export/device checks.

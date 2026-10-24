# Validation record: 2026-10-24

## Local checks

- 49 skill regression checks passed on Windows with Python 3.12. This suite includes simulated engine/device scenarios and seven native process-containment checks using harmless Python helpers.
- In a separate isolated generated project, Godot 4.7.2.stable.official.ed1daf0bf and GdUnit4 6.2.2 passed two actual headless harness tests: `test_main_scene_loads` and `test_smoke_is_inactive_without_flag`.
- Both import and suite invocations reported verified owned-process closure (`active=0`) and a five-second yield with the machine lease released.
- A final read-only inventory found no Godot processes.
- The obsolete debugger connection to port 0 was removed; the final engine logs contained no engine errors. The test-log parser now rejects generic engine errors even when a test summary says zero test failures.

The original local fixture, process inventory and raw logs are retained in the development workspace. The sanitized engine log below removes local absolute fixture paths and ANSI formatting while retaining the reported test result.

## Scope

These results qualify the generated harness's two headless checks and owned-process closure for these Windows runs. They do not establish rendered appearance, audible output, exports, Android hardware, cross-platform engine behavior or correctness of another game. GitHub CI runs the regression suite; it does not repeat the real Godot fixture run.

## Reproduction

Install the skill template into an isolated test project using `scripts/instalar.py`. Supply a compatible local GdUnit4 addon with `--gdunit-from`, point `GODOT` at the installed Godot executable, and run `bash tools/test.sh` from that project. Keep the default five-second yield and retain `tools/out/import.log` and `tools/out/test.log`. Do not test against a user project with unsaved work.

[Sanitized real engine log](headless-test-2026-10-24.log)

"""Native Windows containment tests using Python helpers, never Godot."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import time
import unittest

RUNNER = Path(__file__).resolve().parent.parent / 'assets/plantilla/tools/run_owned_godot.py'


def hidden_popen(*args, **kwargs):
    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(*args, **kwargs)


@unittest.skipUnless(os.name == 'nt', 'Windows process jobs required')
class OwnedProcessTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.api.OpenProcess.restype = wintypes.HANDLE
        self.api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.api.WaitForSingleObject.restype = wintypes.DWORD
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]

    def command(self, source):
        return [sys.executable, str(RUNNER), '--', sys.executable, '-c', source]

    def identity(self, marker):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if marker.exists():
                value = marker.read_text(encoding='utf-8')
                if value:
                    handle = self.api.OpenProcess(0x100000, False, int(value))
                    self.assertTrue(handle, 'Expected live helper identity')
                    self.addCleanup(self.api.CloseHandle, handle)
                    return handle
            time.sleep(0.02)
        self.fail('Helper did not publish its identity')

    def descendant_source(self, marker, root_wait, root_marker=None):
        child = f'import os,time; from pathlib import Path; Path({str(marker)!r}).write_text(str(os.getpid()),encoding="utf-8"); time.sleep(60)'
        prefix = '' if root_marker is None else f'import os; from pathlib import Path; Path({str(root_marker)!r}).write_text(str(os.getpid()),encoding="utf-8"); '
        return prefix + f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}],creationflags=subprocess.CREATE_NO_WINDOW); time.sleep({root_wait})'

    def test_exit_code_and_verified_empty_job(self):
        result = subprocess.run(self.command('raise SystemExit(7)'), capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 7)
        self.assertIn('active=0', result.stderr)

    def test_owned_timeout_closes_process_before_returning(self):
        result = subprocess.run(self.command('import time; time.sleep(60)'),
                                env=dict(os.environ, GODOT_RUN_TIMEOUT='1'), capture_output=True,
                                text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertIn('GODOT_OWNED_TIMEOUT', result.stderr)
        self.assertIn('active=0', result.stderr)

    def test_residual_descendant_closed_and_unrelated_preserved(self):
        marker = self.root / 'child.pid'
        unrelated = hidden_popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        self.addCleanup(self.stop, unrelated)
        runner = hidden_popen(self.command(self.descendant_source(marker, 2)), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop, runner)
        child = self.identity(marker)
        _, error = runner.communicate(timeout=15)
        self.assertEqual(runner.returncode, 0, error)
        self.assertEqual(self.api.WaitForSingleObject(child, 3000), 0)
        self.assertIn('GODOT_OWNED_CLOSING', error)
        self.assertIn('active=0', error)
        self.assertIsNone(unrelated.poll())

    def test_abrupt_runner_death_closes_native_tree(self):
        marker = self.root / 'child.pid'
        root_marker = self.root / 'root.pid'
        runner = hidden_popen(self.command(self.descendant_source(marker, 60, root_marker)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.stop, runner)
        child = self.identity(marker)
        root = self.identity(root_marker)
        runner.kill()
        runner.wait(timeout=5)
        self.assertEqual(self.api.WaitForSingleObject(child, 5000), 0)
        self.assertEqual(self.api.WaitForSingleObject(root, 5000), 0)

    def test_missing_executable_fails_closed(self):
        result = subprocess.run([sys.executable, str(RUNNER), '--', str(self.root / 'missing.exe')], capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 3)
        self.assertNotIn('GODOT_OWNED_STARTED', result.stderr)
        self.assertIn('active=0', result.stderr)

    def test_cooperative_cancel_verifies_both_processes_before_receipt(self):
        marker = self.root / 'child.pid'
        root_marker = self.root / 'root.pid'
        cancel = self.root / 'cancel'
        receipt = self.root / 'receipt'
        environment = dict(os.environ, STUDIO_OWNED_CANCEL=str(cancel), STUDIO_OWNED_RECEIPT=str(receipt))
        runner = hidden_popen(self.command(self.descendant_source(marker, 60, root_marker)),
                                  env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop, runner)
        child = self.identity(marker)
        root = self.identity(root_marker)
        self.assertFalse(receipt.exists())
        cancel.touch()
        _, error = runner.communicate(timeout=15)
        self.assertEqual(runner.returncode, 143, error)
        self.assertEqual(receipt.read_text(encoding='utf-8'), 'verified-empty\n')
        self.assertEqual(self.api.WaitForSingleObject(child, 0), 0)
        self.assertEqual(self.api.WaitForSingleObject(root, 0), 0)

    def test_production_cleanup_trap_cancels_and_releases_after_verified_closure(self):
        bash = Path('C:/Program Files/Git/bin/bash.exe')
        if not bash.exists():
            self.skipTest('Git Bash required')
        tools = RUNNER.parent
        source = (tools / 'godot_guarded.sh').read_text(encoding='utf-8')
        cleanup = source[source.index('cleanup() {'):source.index('godot_guard_acquire || exit 2')]
        marker = self.root / 'child.pid'
        root_marker = self.root / 'root.pid'
        shell_marker = self.root / 'shell.pid'
        control = self.root / 'control'
        control.mkdir()
        lock = self.root / 'machine.lock'
        script = self.root / 'trap.sh'
        quote = lambda value: shlex.quote(str(value).replace('\\', '/'))
        arguments = self.command(self.descendant_source(marker, 60, root_marker))
        # Normalize executable paths only; rewriting Python source corrupts nested escapes.
        arguments[0] = Path(arguments[0]).as_posix()
        arguments[1] = Path(arguments[1]).as_posix()
        arguments[3] = Path(arguments[3]).as_posix()
        command = ' '.join(shlex.quote(value) for value in arguments)
        script.write_text(
            'set -u\n. ' + quote(tools / 'lib/godot_guard.sh') + '\n'
            + 'YIELD_SECONDS=1\nCHILD=""\nMACHINE_LOCK=' + quote(lock) + '\nCONTROL=' + quote(control) + '\n'
            + '_GG_ME="$$ $(_gg_winpid $$)"\n_gg_wait "$MACHINE_LOCK" || exit 90\n'
            + cleanup
            + 'export STUDIO_OWNED_CANCEL="$(cygpath -w "$CONTROL/cancel")"\n'
            + 'export STUDIO_OWNED_RECEIPT="$(cygpath -w "$CONTROL/receipt")"\n'
            + command + ' &\nCHILD=$!\necho $$ > ' + quote(shell_marker) + '\nwait "$CHILD"\n',
            encoding='utf-8')
        unrelated = hidden_popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        self.addCleanup(self.stop, unrelated)
        runner = hidden_popen([str(bash), str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop, runner)
        child = self.identity(marker)
        root = self.identity(root_marker)
        shell_pid = shell_marker.read_text(encoding='utf-8').strip()
        self.assertTrue(shell_pid.isdecimal())
        subprocess.run([str(bash), '-c', 'kill -TERM ' + shell_pid], check=True, timeout=5)
        _, error = runner.communicate(timeout=20)
        self.assertEqual(runner.returncode, 143, error)
        self.assertIn('GODOT_OWNED_CLEANUP_OK', error)
        self.assertNotIn('UNVERIFIED', error)
        self.assertEqual(self.api.WaitForSingleObject(child, 0), 0)
        self.assertEqual(self.api.WaitForSingleObject(root, 0), 0)
        self.assertIsNone(unrelated.poll())
        self.assertFalse(lock.exists())
        self.assertFalse(control.exists())

    @staticmethod
    def stop(process):
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)


if __name__ == '__main__':
    unittest.main()

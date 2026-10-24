#!/usr/bin/env python3
"""Contain a guarded engine in a private Windows job or POSIX process group."""
import ctypes as c
from ctypes import wintypes as w
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


class BasicLimits(c.Structure):
    _fields_ = [("process_time", c.c_int64), ("job_time", c.c_int64),
                ("flags", w.DWORD), ("minimum", c.c_size_t), ("maximum", c.c_size_t),
                ("active_limit", w.DWORD), ("affinity", c.c_size_t),
                ("priority", w.DWORD), ("scheduling", w.DWORD)]


class ExtendedLimits(c.Structure):
    _fields_ = [("basic", BasicLimits), ("io", c.c_uint64 * 6),
                ("process_memory", c.c_size_t), ("job_memory", c.c_size_t),
                ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]


class Startup(c.Structure):
    _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR),
                ("title", w.LPWSTR), ("x", w.DWORD), ("y", w.DWORD),
                ("width", w.DWORD), ("height", w.DWORD), ("chars_x", w.DWORD),
                ("chars_y", w.DWORD), ("fill", w.DWORD), ("flags", w.DWORD),
                ("show", w.WORD), ("reserved_size", w.WORD), ("reserved_ptr", c.c_void_p),
                ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE)]


class StartupEx(c.Structure):
    _fields_ = [("startup", Startup), ("attributes", c.c_void_p)]


class ProcessInfo(c.Structure):
    _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE),
                ("pid", w.DWORD), ("tid", w.DWORD)]


class OwnedJob:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("Owned Windows job containment is required on this host")
        self.api = c.WinDLL("kernel32", use_last_error=True)
        self.job = None
        self.info = ProcessInfo()
        self.attributes = None
        self.attribute_ready = False
        self._bind("CreateJobObjectW", w.HANDLE, [c.c_void_p, w.LPCWSTR])
        self._bind("SetInformationJobObject", w.BOOL, [w.HANDLE, c.c_int, c.c_void_p, w.DWORD])
        self._bind("QueryInformationJobObject", w.BOOL, [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p])
        self._bind("TerminateJobObject", w.BOOL, [w.HANDLE, w.UINT])
        self._bind("CloseHandle", w.BOOL, [w.HANDLE])
        self._bind("InitializeProcThreadAttributeList", w.BOOL, [c.c_void_p, w.DWORD, w.DWORD, c.POINTER(c.c_size_t)])
        self._bind("UpdateProcThreadAttribute", w.BOOL, [c.c_void_p, w.DWORD, c.c_size_t, c.c_void_p, c.c_size_t, c.c_void_p, c.c_void_p])
        self._bind("DeleteProcThreadAttributeList", None, [c.c_void_p])
        self._bind("GetStdHandle", w.HANDLE, [w.DWORD])
        self._bind("CreateProcessW", w.BOOL, [w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p,
                   w.BOOL, w.DWORD, c.c_void_p, w.LPCWSTR, c.POINTER(StartupEx), c.POINTER(ProcessInfo)])
        self._bind("WaitForSingleObject", w.DWORD, [w.HANDLE, w.DWORD])
        self._bind("GetExitCodeProcess", w.BOOL, [w.HANDLE, c.POINTER(w.DWORD)])
        try:
            self.job = self.api.CreateJobObjectW(None, None)
            self._check(self.job, "CreateJobObjectW")
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
            self._check(self.api.SetInformationJobObject(self.job, 9, c.byref(limits), c.sizeof(limits)),
                        "SetInformationJobObject")
        except BaseException:
            if self.job:
                self.api.CloseHandle(self.job)
                self.job = None
            raise

    def _bind(self, name, result, arguments):
        function = getattr(self.api, name)
        function.restype = result
        function.argtypes = arguments

    @staticmethod
    def _check(value, operation):
        if not value:
            raise OSError(c.get_last_error(), operation + " failed")

    def start(self, command):
        if self.info.process:
            raise RuntimeError("One root process per owned job")
        if not command:
            raise ValueError("Missing command")
        if command[0].endswith(".sh"):
            bash = shutil.which("bash") or str(Path(shutil.which("git")).parent.parent / "bin/bash.exe")
            command = [bash, *command]
        executable = shutil.which(command[0])
        if not executable:
            raise FileNotFoundError(command[0])
        size = c.c_size_t()
        self.api.InitializeProcThreadAttributeList(None, 1, 0, c.byref(size))
        if not size.value:
            raise RuntimeError("Process attribute list unavailable")
        self.attributes = c.create_string_buffer(size.value)
        self._check(self.api.InitializeProcThreadAttributeList(self.attributes, 1, 0, c.byref(size)),
                    "InitializeProcThreadAttributeList")
        self.attribute_ready = True
        jobs = (w.HANDLE * 1)(self.job)
        # Atomic assignment closes the suspended-process orphan window.
        self._check(self.api.UpdateProcThreadAttribute(self.attributes, 0, 0x2000D,
                    c.byref(jobs), c.sizeof(jobs), None, None), "UpdateProcThreadAttribute/job list")
        startup = StartupEx()
        startup.startup.cb = c.sizeof(startup)
        startup.attributes = c.cast(self.attributes, c.c_void_p)
        startup.startup.flags = 0x100  # STARTF_USESTDHANDLES, inherited output stays in guard logs.
        startup.startup.stdin = self.api.GetStdHandle(w.DWORD(-10).value)
        startup.startup.stdout = self.api.GetStdHandle(w.DWORD(-11).value)
        startup.startup.stderr = self.api.GetStdHandle(w.DWORD(-12).value)
        line = c.create_unicode_buffer(subprocess.list2cmdline([executable, *command[1:]]))
        self._check(self.api.CreateProcessW(executable, line, None, None, True, 0x80000 | 0x08000000,
                    None, None, c.byref(startup), c.byref(self.info)), "CreateProcessW/owned job")
        print("GODOT_OWNED_STARTED pid=" + str(self.info.pid), file=sys.stderr, flush=True)
        return int(self.info.pid)

    def active_pids(self):
        capacity = 16
        while capacity <= 65536:
            buffer = c.create_string_buffer(8 + capacity * c.sizeof(c.c_size_t))
            ok = self.api.QueryInformationJobObject(self.job, 3, buffer, c.sizeof(buffer), None)
            assigned, count = (w.DWORD * 2).from_buffer(buffer)
            if ok and assigned == count:
                values = (c.c_size_t * count).from_buffer(buffer, 8)
                return [int(value) for value in values]
            if not ok and c.get_last_error() != 234:  # ERROR_MORE_DATA means enlarge, never assume idle.
                self._check(False, "QueryInformationJobObject")
            capacity = max(capacity * 2, int(assigned) + 16)
        raise RuntimeError("Owned process list exceeded bounded inventory")

    def wait(self):
        if not self.info.process:
            raise RuntimeError("No owned process started")
        deadline = time.monotonic() + float(os.environ.get("GODOT_RUN_TIMEOUT", "600"))
        while True:
            if time.monotonic() >= deadline:
                print("GODOT_OWNED_TIMEOUT", file=sys.stderr, flush=True)
                return 124
            cancel = os.environ.get("STUDIO_OWNED_CANCEL")
            if cancel and Path(cancel).is_file():
                return 143
            status = self.api.WaitForSingleObject(self.info.process, 100)
            if status == 0:
                code = w.DWORD()
                self._check(self.api.GetExitCodeProcess(self.info.process, c.byref(code)), "GetExitCodeProcess")
                return int(code.value)
            if status != 258:
                raise RuntimeError("Owned root wait failed")

    def close(self):
        if not self.job:
            return
        try:
            remaining = self.active_pids()
            if remaining:
                print("GODOT_OWNED_CLOSING pids=" + ",".join(map(str, remaining)), file=sys.stderr, flush=True)
                self._check(self.api.TerminateJobObject(self.job, 1), "TerminateJobObject")
            deadline = time.monotonic() + 10
            while self.active_pids():
                if time.monotonic() >= deadline:
                    raise RuntimeError("Owned engine closure could not be verified")
                time.sleep(0.05)
            print("GODOT_OWNED_CLEANUP_OK root=" + str(self.info.pid) + " active=0", file=sys.stderr, flush=True)
            receipt = os.environ.get("STUDIO_OWNED_RECEIPT")
            if receipt:
                # Only the private job's verified empty inventory authorizes this receipt.
                with open(receipt, "x", encoding="utf-8") as output:
                    output.write("verified-empty\n")
        finally:
            # The private job handle is non-inheritable. Closing it also covers abrupt wrapper death.
            self.api.CloseHandle(self.job)
            self.job = None
            if self.attribute_ready:
                self.api.DeleteProcThreadAttributeList(self.attributes)
                self.attribute_ready = False
            for handle in [self.info.thread, self.info.process]:
                if handle:
                    self.api.CloseHandle(handle)
            self.info = ProcessInfo()



def run_posix(command, timeout):
    """Use a private process group and close remaining descendants before the receipt."""
    import signal
    process = subprocess.Popen(command, start_new_session=True)
    print(f"GODOT_OWNED_STARTED pid={process.pid}", file=sys.stderr, flush=True)
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None:
            cancel = os.environ.get("STUDIO_OWNED_CANCEL")
            if cancel and Path(cancel).is_file():
                return 143
            if time.monotonic() >= deadline:
                return 124
            time.sleep(0.05)
        return process.returncode
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        closed_by = time.monotonic() + 5
        while True:
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            if time.monotonic() >= closed_by:
                raise RuntimeError("Owned process group closure could not be verified")
            time.sleep(0.05)
        print(f"GODOT_OWNED_CLEANUP_OK root={process.pid} active=0", file=sys.stderr, flush=True)
        receipt = os.environ.get("STUDIO_OWNED_RECEIPT")
        if receipt:
            with open(receipt, "x", encoding="utf-8") as output:
                output.write("verified-empty\n")


def main():
    command = sys.argv[1:]
    if command[:1] == ["--"]:
        command = command[1:]
    timeout = float(os.environ.get("GODOT_RUN_TIMEOUT", "600"))
    if not 1 <= timeout <= 86400:
        raise ValueError("GODOT_RUN_TIMEOUT must be from 1 to 86400 seconds")
    if os.name != "nt":
        return run_posix(command, timeout)
    job = OwnedJob()
    try:
        job.start(command)
        return job.wait()
    finally:
        job.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except (OSError, ValueError, RuntimeError) as error:
        print("GODOT_OWNED_FAILED: " + str(error), file=sys.stderr)
        sys.exit(3)

#!/usr/bin/env python3
"""Smoke-test an existing device while preserving app data and device settings.

Start a dedicated emulator separately if needed; this script never owns or stops
an emulator or adb server. A debuggable test package is required for scene options.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "{{PACKAGE}}"
APK = ROOT / "build/android/{{SLUG}}-debug.apk"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def positive(value):
    number = int(value)
    if not 1 <= number <= 600:
        raise argparse.ArgumentTypeError("Expected an integer from 1 to 600")
    return number


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--select-device", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-export", action="store_true")
    parser.add_argument("--wait", type=positive, default=20)
    parser.add_argument("--scene")
    parser.add_argument("--arg", action="append", default=[])
    parser.add_argument("--perf", type=positive)
    parser.add_argument("--shot", type=positive)
    args = parser.parse_args()
    if args.scene and (not args.scene.startswith("res://") or not args.scene.endswith(".tscn") or "'" in args.scene):
        parser.error("--scene must be a res:// scene path")
    if (args.arg or args.perf or args.shot) and not args.scene:
        parser.error("--arg, --perf and --shot require --scene")
    for value in args.arg:
        if "=" not in value or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value.split("=", 1)[0]):
            parser.error("--arg requires key=value with an identifier key")
    return args


def adb_path():
    sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
    if not sdk:
        sdk = str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Android/Sdk")
    candidate = Path(sdk) / "platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
    found = str(candidate) if candidate.is_file() else shutil.which("adb")
    if not found:
        raise RuntimeError("adb not found; set ANDROID_SDK_ROOT or PATH")
    return found


def run(command, *, data=None, checked=True):
    result = subprocess.run(command, input=data, capture_output=True, timeout=60)
    if checked and result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command[:5])}: {result.stderr.decode(errors='replace')[:500]}")
    return result


def select_device(adb):
    lines = run([adb, "devices"]).stdout.decode(errors="replace").splitlines()
    devices = [line.split()[0] for line in lines[1:] if len(line.split()) >= 2 and line.split()[1] == "device"]
    selected = os.environ.get("ANDROID_SERIAL")
    if selected:
        if selected not in devices:
            raise RuntimeError("ANDROID_SERIAL is not an authorized online device")
        return selected
    physical = [serial for serial in devices if not serial.startswith("emulator-")]
    if physical:
        return physical[0]
    if devices:
        return devices[0]
    raise RuntimeError("No authorized device available. Connect USB hardware or start a dedicated AVD separately")


def smoke(args, adb, serial):
    output = ROOT / "tools/out/android"
    output.mkdir(parents=True, exist_ok=True)
    def device(*arguments, **kwargs):
        return run([adb, "-s", serial, *arguments], **kwargs)
    def text(*arguments):
        return device(*arguments).stdout.decode(errors="replace").strip()
    if not args.no_export or not APK.is_file():
        bash = shutil.which("bash")
        if not bash and os.name == "nt":
            bash = str(Path(shutil.which("git")).parent.parent / "bin/bash.exe")
        if not bash or subprocess.run([bash, "tools/export.sh", "android", "debug"], cwd=ROOT).returncode:
            raise RuntimeError("Android debug export failed")
    # A signing mismatch is an error; never resolve it by deleting installed data.
    installed = device("install", "-r", str(APK))
    if b"Success" not in installed.stdout:
        raise RuntimeError("APK update did not report Success; installed app data was preserved")
    metadata = {"serial": serial, "model": text("shell", "getprop", "ro.product.model"), "screen": text("shell", "wm", "size")}
    (output / "device.txt").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    old_setting = text("shell", "settings", "get", "global", "stay_on_while_plugged_in")
    if not re.fullmatch(r"\d+|null", old_setting):
        raise RuntimeError("Could not read original stay-awake setting")
    backups = {}
    modified_launch = False
    setting_changed = False
    try:
        if args.scene:
            # Preserve preexisting test launch configuration and shot bytes exactly.
            for name in ("launch.json", "launch_shot.png"):
                exists = device("shell", "run-as", PACKAGE, "test", "-f", f"files/{name}", checked=False)
                if exists.returncode not in (0, 1) or exists.stderr:
                    raise RuntimeError("Cannot safely inspect debug launch files")
                backups[name] = device("exec-out", "run-as", PACKAGE, "cat", f"files/{name}").stdout if exists.returncode == 0 else None
            options = {"scene": args.scene, "args": dict(value.split("=", 1) for value in args.arg)}
            if args.perf:
                options["args"]["perf"] = args.perf
            shot = args.shot or (5 if args.perf else None)
            if shot:
                options["shot_after_s"] = shot
            modified_launch = True
            device("shell", "run-as", PACKAGE, "sh", "-c", "'mkdir -p files && cat > files/launch.json'", data=json.dumps(options).encode())
            device("shell", "run-as", PACKAGE, "rm", "-f", "files/launch_shot.png")
        else:
            shot = None
        setting_changed = True
        device("shell", "settings", "put", "global", "stay_on_while_plugged_in", "2")
        device("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        start = text("shell", "date", "+%m-%d_%H:%M:%S.000").replace("_", " ")
        device("shell", "am", "force-stop", PACKAGE)
        device("shell", "monkey", "-p", PACKAGE, "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(max(args.wait, (args.perf or 0) + 3, (shot or 0) + 3))
        pid = text("shell", "pidof", PACKAGE)
        if not re.fullmatch(r"\d+", pid):
            raise RuntimeError("Application process is not alive")
        log = device("logcat", "-d", "-v", "threadtime", "--pid", pid, "-T", start).stdout
        (output / "logcat.txt").write_bytes(log)
        log_text = log.decode(errors="replace")
        if re.search(r"FATAL EXCEPTION|Fatal signal|SCRIPT ERROR|Parse Error|Failed to load script", log_text):
            raise RuntimeError("Crash or script error in application log")
        expected = "LAUNCH_OPTIONS scene=" if args.scene else "SMOKE_OK"
        if expected not in log_text:
            raise RuntimeError(f"Missing application marker: {expected}")
        if args.perf and "PERF scene=" not in log_text:
            raise RuntimeError("Missing PERF marker")
        image = device("exec-out", "run-as", PACKAGE, "cat", "files/launch_shot.png").stdout if shot else device("exec-out", "screencap", "-p").stdout
        if not image.startswith(PNG_HEADER):
            raise RuntimeError("Screenshot is not a valid PNG stream")
        (output / "screen.png").write_bytes(image)
    finally:
        # Every restoration is attempted even if another one fails.
        restoration_errors = []
        try:
            device("shell", "am", "force-stop", PACKAGE)
        except Exception as error:
            restoration_errors.append(str(error))
        if modified_launch:
            for name, content in backups.items():
                try:
                    if content is None:
                        device("shell", "run-as", PACKAGE, "rm", "-f", f"files/{name}")
                    else:
                        device("shell", "run-as", PACKAGE, "sh", "-c", f"'cat > files/{name}'", data=content)
                except Exception as error:
                    restoration_errors.append(str(error))
        if setting_changed:
            try:
                if old_setting == "null":
                    device("shell", "settings", "delete", "global", "stay_on_while_plugged_in")
                else:
                    device("shell", "settings", "put", "global", "stay_on_while_plugged_in", old_setting)
            except Exception as error:
                restoration_errors.append(str(error))
        if restoration_errors:
            raise RuntimeError("Device restoration failed: " + "; ".join(restoration_errors))

    print(f"ANDROID_SMOKE_OK serial={serial} pid={pid} output={output}")


def main():
    args = parse_args()
    def interrupted(signum, _frame):
        raise RuntimeError(f"Device test interrupted by signal {signum}")
    signal.signal(signal.SIGTERM, interrupted)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, interrupted)
    try:
        adb = adb_path()
        serial = select_device(adb)
        if args.select_device:
            print(serial)
        else:
            smoke(args, adb, serial)
        return 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"ANDROID_SMOKE_FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

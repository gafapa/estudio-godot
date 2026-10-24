#!/usr/bin/env bash
# Export local builds. Android setup updates editor export settings under a machine-wide lock.
set -u
cd "$(dirname "$0")/.." || exit 2
GODOT_REAL="${GODOT:-godot}"; export GODOT_REAL
GODOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/godot_guarded.sh"   # Guarded engine.
. "$(dirname "$GODOT")/lib/godot_guard.sh"
trap godot_guard_release EXIT
godot_guard_acquire || exit 2
export GODOT_SHARED_DATA=1
godot_guard_device_lock export-settings || exit 2
trap 'godot_guard_device_unlock export-settings; godot_guard_release' EXIT
TARGET="${1:-}"; MODE="${2:-debug}"
case "$TARGET" in windows|linux|android) ;; *) echo "Usage: tools/export.sh windows|linux|android [debug|release]" >&2; exit 2 ;; esac
case "$MODE" in debug|release) ;; *) echo "Invalid mode: $MODE" >&2; exit 2 ;; esac

to_win() { cygpath -m "$1" 2>/dev/null || echo "$1"; }

set_setting() {
  local f="$1" k="$2" v="$3" line esc
  line="$k = \"$v\""
  esc="$(printf '%s' "$line" | sed 's/[&|\\]/\\&/g')"
  if grep -q "^$k = " "$f"; then
    grep -qxF "$line" "$f" || sed -i "s|^$k = .*|$esc|" "$f"
  else
    printf '%s\n' "$line" >> "$f"
  fi
}

setup_android() {
  local sdk jdk ks settings
  sdk="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$LOCALAPPDATA/Android/Sdk}}"
  jdk="${JAVA_HOME:-C:/Program Files/Android/Android Studio/jbr}"
  [ -d "$sdk" ] || { echo "Android SDK not found: $sdk" >&2; return 1; }
  [ -x "$jdk/bin/keytool.exe" ] || [ -x "$jdk/bin/keytool" ] || { echo "JDK not found: $jdk" >&2; return 1; }
  ks="$HOME/.android/debug.keystore"
  if [ ! -f "$ks" ]; then
    mkdir -p "$HOME/.android"
    "$jdk/bin/keytool" -genkeypair -v -keystore "$(to_win "$ks")" -storepass android -keypass android \
      -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1 \
      || { echo "Could not generate debug keystore" >&2; return 1; }
  fi
  settings="${APPDATA:-$HOME/AppData/Roaming}/Godot/editor_settings-{{GODOT_MINOR}}.tres"
  [ -f "$settings" ] || { "$GODOT" --headless --editor --quit --path . >/dev/null 2>&1 || true; }
  [ -f "$settings" ] || { echo "Editor settings not found: $settings" >&2; return 1; }
  set_setting "$settings" export/android/android_sdk_path "$(to_win "$sdk")"
  set_setting "$settings" export/android/java_sdk_path "$(to_win "$jdk")"
  set_setting "$settings" export/android/debug_keystore "$(to_win "$ks")"
  set_setting "$settings" export/android/debug_keystore_user androiddebugkey
  set_setting "$settings" export/android/debug_keystore_pass android
  if [ "$MODE" = release ]; then
    : "${GODOT_ANDROID_KEYSTORE_RELEASE_PATH:?define GODOT_ANDROID_KEYSTORE_RELEASE_PATH, _USER and _PASSWORD}"
    : "${GODOT_ANDROID_KEYSTORE_RELEASE_USER:?Missing release keystore user}"
    : "${GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD:?Missing release keystore password}"
    export GODOT_ANDROID_KEYSTORE_RELEASE_PATH GODOT_ANDROID_KEYSTORE_RELEASE_USER GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD
  fi
}

if [ ! -d .godot/imported ]; then
  "${PYTHON:-python}" tools/run_bounded.py 300 "$GODOT" --headless --path . --import || exit 1
fi

case "$TARGET" in
  windows) PRESET="Windows Desktop"; OUT="build/windows/{{EXE}}.exe" ;;
  linux)   PRESET="Linux"; OUT="build/linux/{{EXE}}.x86_64" ;;
  android) setup_android || exit 1
           PRESET="Android"; OUT="build/android/{{SLUG}}-$MODE.apk" ;;
esac
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
log="$(mktemp)"
"${PYTHON:-python}" tools/run_bounded.py "${EXPORT_TIMEOUT:-600}" "$GODOT" --headless --path . "--export-$MODE" "$PRESET" "$OUT" >"$log" 2>&1
rc=$?
if [ $rc -ne 0 ] || [ ! -s "$OUT" ] || grep -qE "^(ERROR|SCRIPT ERROR)" "$log"; then
  echo "EXPORT_FAILED $TARGET $MODE (rc=$rc)" >&2
  grep -E "ERROR|error" "$log" | head -15 >&2
  rm -f "$log"; exit 1
fi
rm -f "$log"
echo "EXPORT_OK $OUT ($(du -h "$OUT" | cut -f1))"

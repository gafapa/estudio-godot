#!/usr/bin/env bash
# One engine per checkout, bounded global slots, named mutexes and machine-wide device locks.
# Inherited lock ownership is accepted only for the exact same checkout.
_GG_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_GG_COMMON="$(git -C "$_GG_SOURCE" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
_GG_TOP="$(git -C "$_GG_SOURCE" rev-parse --show-toplevel 2>/dev/null)"
_GG_BASE="${_GG_COMMON:-${TMPDIR:-/tmp}}/{{SLUG}}-godot"
_GG_CHECKOUT="${_GG_TOP:-$_GG_SOURCE/../..}/tools/out/.godot-checkout.lock"
_GG_SLOT=""; _GG_MINE=0
_gg_default_slots() {
  local count
  count="$(nproc 2>/dev/null || echo "${NUMBER_OF_PROCESSORS:-4}")"
  count=$((count / 4)); [ "$count" -ge 1 ] || count=1; [ "$count" -le 4 ] || count=4
  echo "$count"
}
_GG_SLOTS="${GODOT_SLOTS:-$(_gg_default_slots)}"
_gg_winpid() { cat "/proc/$1/winpid" 2>/dev/null || echo "$1"; }
_gg_alive() { [ -n "$1" ] && command -v tasklist >/dev/null 2>&1 && tasklist //FI "PID eq $1" //NH 2>/dev/null | grep -q " $1 "; }
_gg_owner_alive() {
  local shell_pid windows_pid
  read -r shell_pid windows_pid <<< "$1"
  { [ -n "$shell_pid" ] && kill -0 "$shell_pid" 2>/dev/null; } || _gg_alive "${windows_pid:-}"
}
_gg_write_owner() {
  printf '%s\n' "$_GG_ME" > "$1/owner"
  printf '%s %s %s\n' "$(basename "$0")" "$(date +%H:%M:%S)" "$PWD" > "$1/what"
}
_gg_try() {
  local directory="$1" owner current
  [ ! -d "$directory.reap" ] || return 1
  if mkdir "$directory" 2>/dev/null; then _gg_write_owner "$directory"; return 0; fi
  owner="$(cat "$directory/owner" 2>/dev/null)"
  # Serialize stale-owner recovery. Re-read ownership after taking the recovery lock.
  if [ -n "$owner" ] && ! _gg_owner_alive "$owner"; then
    mkdir "$directory.reap" 2>/dev/null || return 1
    current="$(cat "$directory/owner" 2>/dev/null)"
    if [ "$current" = "$owner" ] && ! _gg_owner_alive "$current"; then
      rm -rf -- "$directory"
      if mkdir "$directory" 2>/dev/null; then
        _gg_write_owner "$directory"
        rmdir "$directory.reap"; return 0
      fi
    fi
    rmdir "$directory.reap"
  fi
  return 1
}
_gg_release_owned() {
  [ "$(cat "$1/owner" 2>/dev/null)" = "${_GG_ME:-}" ] || return 0
  rm -rf -- "$1"
}
_gg_wait() {
  local directory="$1" waited=0 maximum="${GODOT_LOCK_WAIT:-1800}"
  [[ "$maximum" =~ ^[0-9]+$ ]] || { echo 'GODOT_LOCK_WAIT must be nonnegative seconds' >&2; return 2; }
  until _gg_try "$directory"; do
    [ "$waited" -lt "$maximum" ] || { echo "LOCK_TIMEOUT: $directory (owner: $(cat "$directory/owner" 2>/dev/null))" >&2; return 2; }
    sleep 1; waited=$((waited + 1))
  done
}
godot_guard_acquire() {
  if [ "${GODOT_LOCK_CHECKOUT:-}" = "$_GG_CHECKOUT" ] && [ -n "${GODOT_LOCK_HELD:-}" ] && [ "$(cat "$_GG_CHECKOUT/owner" 2>/dev/null)" = "$GODOT_LOCK_HELD" ] && _gg_owner_alive "$GODOT_LOCK_HELD"; then return 0; fi
  [[ "$_GG_SLOTS" =~ ^[1-9][0-9]*$ ]] && [ "$_GG_SLOTS" -le 64 ] || { echo 'GODOT_SLOTS must be from 1 to 64' >&2; return 2; }
  _GG_ME="$$ $(_gg_winpid $$)"
  mkdir -p "$(dirname "$_GG_CHECKOUT")"
  _gg_wait "$_GG_CHECKOUT" || return 2
  local waited=0 maximum="${GODOT_LOCK_WAIT:-1800}" index
  while :; do
    for ((index=1; index<=_GG_SLOTS; index++)); do
      if _gg_try "$_GG_BASE.slot$index"; then _GG_SLOT="$_GG_BASE.slot$index"; break 2; fi
    done
    if [ "$waited" -ge "$maximum" ]; then _gg_release_owned "$_GG_CHECKOUT"; echo 'LOCK_TIMEOUT: Godot slots' >&2; return 2; fi
    sleep 1; waited=$((waited + 1))
  done
  _GG_MINE=1
  export GODOT_LOCK_HELD="$_GG_ME" GODOT_LOCK_CHECKOUT="$_GG_CHECKOUT"
}
godot_guard_release() {
  if [ "$_GG_MINE" = 1 ]; then
    [ -z "$_GG_SLOT" ] || _gg_release_owned "$_GG_SLOT"
    _gg_release_owned "$_GG_CHECKOUT"
    _GG_MINE=0; _GG_SLOT=""; unset GODOT_LOCK_HELD GODOT_LOCK_CHECKOUT
  fi
}
godot_guard_mutex() {
  [[ "$1" =~ ^[A-Za-z0-9_-]+$ ]] || return 2
  _GG_ME="${_GG_ME:-$$ $(_gg_winpid $$)}"
  _gg_wait "$_GG_BASE.$1"
}
godot_guard_unmutex() { _gg_release_owned "$_GG_BASE.$1"; }
_gg_device_dir() {
  local base="${GODOT_DEVICE_LOCK_DIR:-${TEMP:-${TMPDIR:-/tmp}}/godot-device-locks}"
  base="$(cygpath -u "$base" 2>/dev/null || echo "$base")"
  mkdir -p "$base"; echo "$base/${1//[^A-Za-z0-9._-]/_}"
}
godot_guard_device_lock() {
  _GG_ME="${_GG_ME:-$$ $(_gg_winpid $$)}"
  _gg_wait "$(_gg_device_dir "$1")"
}
godot_guard_device_unlock() { _gg_release_owned "$(_gg_device_dir "$1")"; }
# Windows editor detection is read-only; paths are passed through the environment.
godot_guard_foreign_on_checkout() {
  command -v powershell.exe >/dev/null 2>&1 || return 0
  tasklist //FO CSV //NH 2>/dev/null | grep -qi '^"godot' || return 0
  local detector="$_GG_SOURCE/detect_editor.ps1"
  detector="$(cygpath -w "$detector" 2>/dev/null || echo "$detector")"
  STUDIO_CHECKOUT_PATH="$(cygpath -w "$_GG_TOP" 2>/dev/null || echo "$_GG_TOP")" powershell.exe -NoProfile -File "$detector" 2>/dev/null | tr -d '\r' | tr '\n' ' '
}

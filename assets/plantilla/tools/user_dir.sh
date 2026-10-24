#!/usr/bin/env bash
# Print this checkout's isolated user data directory.
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
GH="$PWD/tools/out/godot-home"
NAME="$(sed -n 's/^config\/name="\(.*\)"/\1/p' project.godot | head -1)"
CUSTOM="$(sed -n 's/^config\/custom_user_dir_name="\(.*\)"/\1/p' project.godot | head -1)"
if grep -q '^config/use_custom_user_dir=true' project.godot && [ -n "$CUSTOM" ]; then
  REL="$CUSTOM"
else
  REL="Godot/app_userdata/$NAME"
fi
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) echo "$GH/appdata/$REL" ;;
  *) echo "$GH/xdg/data/${REL#Godot/}" | sed 's#app_userdata/#godot/app_userdata/#' ;;
esac

#!/usr/bin/env bash
# Capture the screen that is currently displayed on a connected Android device:
# a PNG, the uiautomator view hierarchy, and the foreground activity.
#
# Usage:
#   capture-screen.sh --out <dir> --name <slug> [--serial <serial>] [--no-dump] [--settle <sec>]
#
# Writes into <dir>:
#   <slug>.png          screenshot
#   <slug>.uix          raw uiautomator XML dump (skipped with --no-dump)
#   <slug>.meta.json    serial, model, android release, foreground activity, size, density, timestamp
#
# Exit codes: 0 ok, 2 bad usage, 3 no device, 4 capture failed.

set -euo pipefail

OUT=""
NAME=""
SERIAL="${ANDROID_SERIAL:-}"
DO_DUMP=1
SETTLE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --serial) SERIAL="${2:-}"; shift 2 ;;
    --no-dump) DO_DUMP=0; shift ;;
    --settle) SETTLE="${2:-0}"; shift 2 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -n "$OUT" ] || { echo "--out is required" >&2; exit 2; }
[ -n "$NAME" ] || { echo "--name is required" >&2; exit 2; }

# Resolve adb: PATH first, then the standard SDK locations.
ADB="$(command -v adb || true)"
if [ -z "$ADB" ]; then
  for c in "${ANDROID_HOME:-}/platform-tools/adb" \
           "${ANDROID_SDK_ROOT:-}/platform-tools/adb" \
           "$HOME/Library/Android/sdk/platform-tools/adb" \
           "$HOME/Android/Sdk/platform-tools/adb"; do
    [ -x "$c" ] && { ADB="$c"; break; }
  done
fi
[ -n "$ADB" ] || { echo "adb not found; install platform-tools or set ANDROID_HOME" >&2; exit 3; }

# `adb devices` separates serial and state with a TAB, and an mDNS serial such as
# `adb-XXXX-YYY (2)._adb-tls-connect._tcp` contains spaces — so split on TAB only.
if [ -z "$SERIAL" ]; then
  DEVICE_LIST="$("$ADB" devices | awk -F'\t' 'NR>1 && $2=="device" {print $1}')"
  DEVICE_COUNT="$(printf '%s\n' "$DEVICE_LIST" | grep -c . || true)"
  case "$DEVICE_COUNT" in
    0) echo "no device in state 'device'; run: $ADB devices" >&2; exit 3 ;;
    1) SERIAL="$(printf '%s\n' "$DEVICE_LIST" | head -1)" ;;
    *) echo "several devices attached; pass --serial with one of:" >&2
       printf '%s\n' "$DEVICE_LIST" | sed 's/^/  /' >&2; exit 3 ;;
  esac
fi

A=("$ADB" -s "$SERIAL")

if [ "$SETTLE" != "0" ]; then sleep "$SETTLE"; fi

mkdir -p "$OUT"
PNG="$OUT/$NAME.png"

# exec-out keeps the PNG binary-clean (no CRLF translation).
if ! "${A[@]}" exec-out screencap -p > "$PNG" 2>/dev/null; then
  echo "screencap failed on $SERIAL" >&2; exit 4
fi
[ -s "$PNG" ] || { echo "screencap produced an empty file on $SERIAL" >&2; rm -f "$PNG"; exit 4; }

UIX_STATUS="skipped"
if [ "$DO_DUMP" = "1" ]; then
  if "${A[@]}" shell uiautomator dump /sdcard/window_dump.xml >/dev/null 2>&1 &&
     "${A[@]}" exec-out cat /sdcard/window_dump.xml > "$OUT/$NAME.uix" 2>/dev/null &&
     [ -s "$OUT/$NAME.uix" ]; then
    UIX_STATUS="ok"
    "${A[@]}" shell rm -f /sdcard/window_dump.xml >/dev/null 2>&1 || true
  else
    UIX_STATUS="failed"
    rm -f "$OUT/$NAME.uix"
  fi
fi

# Metadata is best-effort: a field the device does not report must not fail the
# capture, so every probe ends in `|| true` (grep returning 1 would trip set -e).
meta_field() { { "${A[@]}" shell "$@" 2>/dev/null | tr -d '\r' | head -1; } || true; }

MODEL="$(meta_field getprop ro.product.model)"
RELEASE="$(meta_field getprop ro.build.version.release)"
SDKINT="$(meta_field getprop ro.build.version.sdk)"
SIZE="$(meta_field wm size | sed 's/.*: //' || true)"
DENSITY="$(meta_field wm density | sed 's/.*: //' || true)"
# Foreground activity: dumpsys wording differs across versions, so try both.
# The line is `mResumedActivity=`, `topResumedActivity=` or `ResumedActivity:`
# depending on the Android version, so match the shared `ResumedActivity` stem.
FG="$({ "${A[@]}" shell dumpsys activity activities 2>/dev/null | tr -d '\r' \
      | grep -E 'ResumedActivity' \
      | grep -Eo '[A-Za-z0-9_.]+/[A-Za-z0-9_.$]+' | head -1; } || true)"
[ -n "$FG" ] || FG="$({ "${A[@]}" shell dumpsys window 2>/dev/null | tr -d '\r' \
      | grep -Eo 'mCurrentFocus=[^ ]+ [^ ]+' \
      | grep -Eo '[A-Za-z0-9_.]+/[A-Za-z0-9_.$]+' | head -1; } || true)"
[ -n "$FG" ] || FG="unknown"

# Values travel through the environment, never inlined into the Python source:
# a model name or activity holding a quote would otherwise break the script.
CAP_NAME="$NAME" CAP_SERIAL="$SERIAL" CAP_MODEL="$MODEL" CAP_RELEASE="$RELEASE" \
CAP_SDK="$SDKINT" CAP_SIZE="$SIZE" CAP_DENSITY="$DENSITY" CAP_FG="$FG" \
CAP_UIX="$UIX_STATUS" python3 -I - "$OUT/$NAME.meta.json" <<'PY'
import datetime, json, os, sys

name = os.environ["CAP_NAME"]
uix = os.environ["CAP_UIX"]
json.dump(
    {
        "name": name,
        "captured_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "serial": os.environ["CAP_SERIAL"],
        "model": os.environ["CAP_MODEL"],
        "android_release": os.environ["CAP_RELEASE"],
        "sdk_int": os.environ["CAP_SDK"],
        "screen_size": os.environ["CAP_SIZE"],
        "density": os.environ["CAP_DENSITY"],
        "foreground_activity": os.environ["CAP_FG"],
        "screenshot": name + ".png",
        "view_hierarchy": (name + ".uix") if uix == "ok" else None,
        "view_hierarchy_status": uix,
    },
    open(sys.argv[1], "w", encoding="utf-8"),
    indent=2,
    ensure_ascii=False,
)
PY

echo "png=$PNG"
[ "$UIX_STATUS" = "ok" ] && echo "uix=$OUT/$NAME.uix"
echo "meta=$OUT/$NAME.meta.json"
echo "activity=$FG"
echo "uix_status=$UIX_STATUS"

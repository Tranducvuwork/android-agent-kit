---
name: adb-android-agent-control
description: "Control Android devices (and Linux handhelds) from an AI agent over ADB/SSH: wireless-debugging pairing, port rediscovery after reboot, screenshots vs UI dumps, input injection, and the decide-act-verify control loop. Use when: connecting an agent to a physical Android phone, ADB connect fails after a reboot, screenshots come back black, typing text into fields, driving a Steam Deck-class Gamescope handheld, 'control my phone', 'adb wireless debugging', 'pair device', 'screenshot is black', 'take over the device'."
---

# ADB Android Agent Control

The transport layer for agent-driven device control: get connected, stay connected across reboots, see the screen, send inputs, and verify every action.

## Wireless ADB — the two-ports trap

Wireless Debugging shows **two different ports**, and confusing them is the #1 setup failure:

- **Pairing port** — shown only in "Pair device with pairing code". Used once with `adb pair IP:PAIRING_PORT` + the 6-digit code.
- **Connection port** — shown on the main Wireless Debugging screen. Used every time with `adb connect IP:PORT`.

Setup sequence: Settings → About Phone → tap **Build Number 7 times** → Developer Options → USB Debugging ON → Wireless Debugging ON → pair → connect.

### Ports randomize — pairing persists

The connection port **changes on every phone reboot and every Wireless Debugging toggle**. The pairing itself survives. So: never ask the user to re-pair; rediscover the port.

**mDNS rediscovery** (no user interaction):

```bash
# Preferred: adb's built-in discovery — lines look like:
#   adb-<SERIAL>-... _adb-tls-connect._tcp <host>.local.:46377
adb mdns services

# Fallback: dns-sd browse + resolve (macOS; use avahi-browse on Linux)
dns-sd -B _adb-tls-connect._tcp local.
dns-sd -L <instance> _adb-tls-connect._tcp local.
# resolve output contains "can be reached at <host>.local.:<port>"
```

Then **serial-verify before trusting any rediscovered endpoint** — on a LAN with multiple phones, mDNS will happily hand you the wrong one:

```bash
adb connect <candidate>
adb -s <candidate> shell getprop ro.serialno   # must equal the serial on record
```

**Refuse to guess.** If the device registry entry has no serial recorded and its stored endpoint is stale, stop and ask for onboarding rather than latching onto whatever mDNS found — that is how you end up posting to the wrong physical phone. When the serial matches, patch the stored endpoint and continue.

Also handle:

- `unauthorized` in `adb devices` → check the phone screen for the "Allow USB debugging?" dialog; if none, `adb kill-server && adb start-server` and reconnect.
- `offline` → `adb disconnect && adb connect IP:PORT`.
- Developer Options vanished → some phones re-hide it after reboot; tap Build Number 7 times again.

## Seeing the screen: screencap vs uiautomator

Two vision channels, and you need both:

```bash
adb -s $DEVICE exec-out screencap -p > /tmp/screen.png   # pixels
adb -s $DEVICE shell uiautomator dump /dev/tty           # UI hierarchy XML (ground truth)
```

**Apps black out protected surfaces.** Some apps return an all-black screenshot on DRM-protected or sensitive screens while the UI hierarchy dump remains fully readable. A black screenshot does NOT mean failure. Rule: **trust the UI dump text over pixels.** The dump gives you every node's `text`, `content-desc`, `resource-id`, `class`, `clickable`, and `bounds` — enough to know exactly where you are and what to tap without rendering anything.

Dump to a file when `/dev/tty` is unreliable:

```bash
adb -s $DEVICE shell uiautomator dump /sdcard/ui.xml
adb -s $DEVICE exec-out cat /sdcard/ui.xml
```

## Input injection idioms

```bash
adb -s $DEVICE shell input tap X Y
adb -s $DEVICE shell input swipe X1 Y1 X2 Y2 DURATION_MS
adb -s $DEVICE shell input text "your%stext"        # %s = space (spaces break input text)
adb -s $DEVICE shell input keyevent KEYCODE          # 3=Home 4=Back 66=Enter 67=Del 224=Wake
adb -s $DEVICE shell input keycombination 113 29     # Ctrl+A (select all in a field)
adb -s $DEVICE shell monkey -p com.example.app 1     # launch app
adb -s $DEVICE shell am force-stop com.example.app   # hard reset app state
adb -s $DEVICE shell am start -a android.intent.action.VIEW -d "<url>" <pkg>  # deep link
```

Field-editing pattern that survives flaky keyboards (learned the hard way — Ctrl+A doesn't always work):

```bash
adb -s $DEVICE shell input keycombination 113 29   # select all
adb -s $DEVICE shell input keyevent 67             # delete
# then ~10 backup keyevent 67 calls, then VERIFY the field is empty via UI dump
```

After typing, **dismiss the keyboard with `keyevent 4`** before tapping anything near the bottom of the screen — an open keyboard covers bottom buttons and silently eats the tap.

`keyevent 224` wakes the screen without toggling it off (unlike the power key).

## The decide-act-verify loop

Every action, no exceptions:

1. **Screenshot + UI dump** — where am I?
2. **Decide** the target (see the selector-first skill — never blind coordinates)
3. **Act** — one input
4. **Verify** — dump again and check the expected post-condition appeared
5. On mismatch: screenshot, log state, recover (back button / force-stop + relaunch), retry with a cap (3 attempts), then exit with a real diagnosis instead of flailing

Poll for async states instead of fixed sleeps:

```python
def wait_for(ip, predicate, timeout=15.0, interval=0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        xml = ui_dump(ip)
        try:
            if predicate(xml):
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False
```

Time out generously on media-heavy transitions: one app's draft editor took **~30s to appear** (it downloads the uploaded video first) — a 12s wait lost every single post before anyone noticed. Measure the real latency on-device, then double it.

## Preflight for unattended runs

Before any autonomous session:

```bash
adb -s $DEVICE shell settings put global zen_mode 0                  # DND off — kills silent notification failures
adb -s $DEVICE shell settings put global stay_on_while_plugged_in 3  # screen stays awake on charger
adb -s $DEVICE shell input keyevent 224                              # wake
adb -s $DEVICE shell am force-stop com.example.app && sleep 2        # known state
adb -s $DEVICE shell monkey -p com.example.app 1 && sleep 5          # relaunch
```

For long-running 24/7 device fleets also consider: screen timeout to effectively-never, battery-optimizer/doze whitelists for the target app and `com.android.shell`, WiFi always-on, and pre-revoking permissions that spawn blocking prompts (see the selector-first skill's popup doctrine for why).

## Linux handhelds (Gamescope / Steam Deck-class)

SSH in and control over DBus — standard X11 tooling does NOT work. See `references/gamescope-handheld.md` for the full incantations, button event table, and the catalog of what returns black/blank. Headlines:

- Screenshots: **only** the Gamescope DBus `TakeScreenshot` method works; X11, x11grab, /dev/fb0 all return black or blank.
- Input: **only** InputPlumber's `SendButtonChord` DBus method; virtual uinput gamepads are ignored.
- Rendering: apps render only when launched through the device's own UI (PlayServe); apps started from SSH run but never display.
- Audio: `pw-play`/`pw-record` need `XDG_RUNTIME_DIR` set explicitly over SSH.

## LESSONS LEARNED

- Pairing is permanent; ports are not. Build rediscovery in from day one, never make re-pairing a manual step.
- Always serial-verify a rediscovered device before sending it any action. The failure mode is acting on the wrong physical phone.
- UI XML is ground truth; pixels lie (black screenshots on protected surfaces, protected dialogs that don't render into the dump — see the popup doctrine for the inverse case).
- Force-stop + relaunch before every autonomous run. Stale app state is the root cause of most "element not found" ghosts.
- `input text` can't take spaces — use `%s`. It also can't take many special characters; prefer per-character typing when fidelity matters.
- A tap that "did nothing" is usually an open keyboard covering the button, not a broken button.

## FAILURE CATALOG

| Symptom | Root cause | Fix |
|---|---|---|
| `adb connect` fails after phone reboot | Connection port randomized | mDNS rediscover + serial-verify + patch registry |
| `unauthorized` | Missing "Allow USB debugging?" approval | Check phone screen; else `adb kill-server && adb start-server` |
| `offline` | Stale ADB session | `adb disconnect && adb connect` |
| Screenshot is all black | App DRM on protected surface | Use `uiautomator dump` text as ground truth |
| Tap on bottom button does nothing | Keyboard still open | `keyevent 4` to dismiss, then tap |
| Typed text missing spaces / garbled | `input text` needs `%s` for spaces | Escape spaces; per-char typing for reliability |
| "Element not found" after idle period | Stale app state / app backgrounded | force-stop + relaunch in preflight |
| Flow times out waiting for editor/screen | Media download latency underestimated (~30s, not 12s) | Measure real latency on-device; poll with generous timeout |
| Gamescope screenshot black/blank | X11/fb0 blocked by compositor | DBus `TakeScreenshot` only (see reference) |
| Virtual gamepad input ignored | InputPlumber filters non-hardware devices | DBus `SendButtonChord` only |
| `pw-record` fails over SSH | Missing `XDG_RUNTIME_DIR` | Prefix `XDG_RUNTIME_DIR=/run/user/1000` |

## BEST PRACTICES

- One device registry file as source of truth (endpoint, serial, model, resolution); scripts rediscover-and-patch it, never the human.
- Poll predicates on the UI dump; never fixed sleeps for state transitions.
- Log every run: step log + per-step screenshot + per-step UI XML. Post-mortems are impossible without the XML.
- Keep a `ROBOTIC=1`-style env flag to disable human-pacing jitter when debugging (so coordinates in logs are exact), but never ship it on.
- Cap retries at 3 and exit with a structured failure (stage + adb output + candidates seen) instead of looping forever.

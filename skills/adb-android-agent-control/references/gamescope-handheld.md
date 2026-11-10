# Linux Handheld Reference (Gamescope devices: Steam Deck-class, Playtron GameOS)

Connection: SSH (key or password auth). Everything below runs over the SSH session.
Standard X11/SSH tooling silently fails on these devices — the working path for
screenshots and input is DBus.

## Screenshots — ONLY this works

```bash
busctl --user call org.shadowblip.Gamescope \
  /org/shadowblip/Gamescope/Wayland0 \
  org.shadowblip.Gamescope.Wayland \
  TakeScreenshot sy "/tmp/screenshot.png" 0

scp USER@DEVICE_IP:/tmp/screenshot.png /tmp/screen.png
```

### What DOESN'T work (all verified on-device)

| Method | Result |
|---|---|
| `DISPLAY=:0 import -window root` (ImageMagick) | black image — gamescope blocks X11 capture |
| `ffmpeg -f x11grab` | black image |
| raw framebuffer `sudo cat /dev/fb0` | white/blank image |
| PipeWire video capture | ffmpeg build lacks pipewire input support |

Fallback note: raw `/dev/fb0` capture *does* work on ordinary Linux PCs
(`sudo cat /dev/fb0` + ffmpeg rawvideo conversion) — just not under gamescope.

## Controller input — ONLY InputPlumber DBus works

```bash
DBUS="busctl --system call org.shadowblip.InputPlumber \
  /org/shadowblip/InputPlumber/CompositeDevice0 \
  org.shadowblip.Input.CompositeDevice SendButtonChord"

$DBUS as 1 "Gamepad:Button:South"   # A / confirm
```

### Button event names

| Button | Event name |
|---|---|
| A (confirm) | `Gamepad:Button:South` |
| B (back) | `Gamepad:Button:East` |
| X | `Gamepad:Button:West` |
| Y | `Gamepad:Button:North` |
| D-pad Up/Down/Left/Right | `Gamepad:Button:DPadUp` / `DPadDown` / `DPadLeft` / `DPadRight` |
| Start | `Gamepad:Button:Start` |
| Select | `Gamepad:Button:Select` |
| Guide/Home | `Gamepad:Button:Guide` |
| LB / RB | `Gamepad:Button:LeftBumper` / `RightBumper` |
| Stick clicks | `Gamepad:Button:LeftStick` / `RightStick` |

### What DOESN'T work for input

- Virtual gamepad via uinput/evdev → **InputPlumber ignores non-hardware devices.**
- Direct X11 key injection (`xdotool`) → gamescope doesn't pass it to apps.

## App launching — PlayServe-only rendering

Apps MUST be launched through the device's own UI (PlayServe / the game launcher)
to render inside gamescope. A flatpak started from SSH **runs but never displays**.
To open a game autonomously, drive the launcher UI itself with SendButtonChord
navigation.

## Audio

```bash
# Voice out: synthesize TTS locally, scp the mp3 over, then:
ssh USER@DEVICE_IP 'XDG_RUNTIME_DIR=/run/user/1000 pw-play /tmp/speech.mp3'

# Voice in: record from the mic, scp back, transcribe with Whisper
ssh USER@DEVICE_IP 'XDG_RUNTIME_DIR=/run/user/1000 timeout 6 pw-record \
  --target=AUDIO_SOURCE --format=s16 --rate=16000 --channels=1 /tmp/mic.wav'
# find source names: pactl list sources short
```

The `XDG_RUNTIME_DIR=/run/user/1000` prefix is mandatory — PipeWire's socket
lives there and SSH sessions don't have it in the environment. Symptom of
forgetting it: `pw-record`/`pw-play` fail with connection errors.

## Gamescope atoms (advanced: which app is focused?)

```bash
DISPLAY=:0 python3 -c "
from Xlib import display
d = display.Display(':0')
root = d.screen().root
for name in ['GAMESCOPE_FOCUSED_APP', 'GAMESCOPECTRL_BASELAYER_APPID']:
    atom = d.intern_atom(name)
    val = root.get_full_property(atom, 0)
    print(f'{name} = {val.value if val else None}')
"
```

## Linux PCs (non-gamescope)

- Screenshots: `DISPLAY=:0 import -window root /tmp/screen.png` or `grim` (Wayland)
- Input: `xdotool` / `ydotool` / evdev
- Audio: same PipeWire pattern as above

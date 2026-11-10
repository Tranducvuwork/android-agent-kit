# Selector Harvest Playbook

Operator-facing detail for the harvest / calibrate / regression loop described in SKILL.md.

## Guided calibration script shape

Screen-by-screen walk. For each screen: instruct the operator, wait for Enter,
dump + screenshot, resolve every target, print FOUND/MISS.

```python
SCREENS = [
    ("feed",              "Home feed (For You page)",            ["profile_tab", "inbox_tab"]),
    ("inbox",             "Inbox tab open",                      ["system_notifications"]),
    ("notification_list", "System notifications list open",      []),  # rows discovered structurally
    ("editor",            "Draft editor open ('Your Story' + 'Next' visible)", ["next_button"]),
    ("audio_picker",      "Audio picker open",                   ["delete_audio", "search_icon"]),
    ("search_results",    "Audio search results showing",        []),  # cards structurally
    ("publish",           "Publish screen (tapped Next)",        ["post_button"]),
]
```

Identity-check first, before trusting anything:

```python
model  = adb(ip, "shell", "getprop", "ro.product.model").stdout.strip()
serial = adb(ip, "shell", "getprop", "ro.serialno").stdout.strip()
wm     = adb(ip, "shell", "wm", "size").stdout.strip()
# warn loudly if serial != the registry's serial for this device key —
# you might be connected to the wrong phone.
```

Rules:

- **Never auto-write the registry.** Print a ready-to-paste `coords` fallback
  block (and save it into the calibration log dir) for human review. The
  selector registry stays hand-edited.
- Some targets can never be auto-derived (no selector, no heuristic — e.g.
  unlabeled check buttons that need the color scan). Keep an explicit
  MANUAL_ONLY list for those.
- Artifacts per run: one dir with `<screen>.png` + `<screen>.xml` per screen,
  so a MISS can be diagnosed offline.

## Per-target harvest log (keep one row per target)

| target | state | notes |
|---|---|---|
| `inbox_tab` | CONFIRMED | content-desc "Inbox"; bottom-nav ids obfuscated, use desc |
| `feed_like` | CONFIRMED | desc_contains "Like video", clickable |
| `comment_input` | CONFIRMED | EditText hint "Add comment..."; send button is the UNLABELED ImageView right of it — found by geometry |
| `next_button` | GUESSED | text + bottom region — confirm on first live run |
| `delete_audio` | HARVEST NEEDED | coords only; screen needs real content to reach |

State vocabulary: **CONFIRMED** (seen resolving on a live dump), **GUESSED**
(plausible but never seen live), **HARVEST NEEDED** (no working selector).
Log the app version next to every harvest so churn is diagnosable.

## Popup sighting log (feed the allowlist from these only)

| popup | trigger | buttons | handling | in uiautomator dump? |
|---|---|---|---|---|
| "Save login info?" | after profile tap | **Not now** / Save | generic sweep (Not now ∈ allowlist) | yes |
| "Add phone number" sheet | app launch | Continue / **Close ✕** | marker-gated special case → content-desc Close | yes |
| Contacts pre-permission | feed/launch | **Don't allow** / Open settings | generic sweep + `pm revoke READ_CONTACTS` pre-emption | **inconsistent** — in-window on one phone, separate undumpable window on another |

Record: trigger, screen, exact button text, dump-visibility. The
dump-visibility column is the one that predicts whether you need a
`pm revoke` pre-emption.

## Regression triggers

- After every target-app update: re-run calibrate; any previously-FOUND target
  now MISS = re-harvest that screen.
- In production run logs: any `tap_*_COORDS_FALLBACK` step.
- When adding a device with a new resolution: calibrate once; expect zero
  selector changes (region bands carry), only new coords fallbacks.

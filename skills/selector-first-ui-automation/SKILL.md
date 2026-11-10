---
name: selector-first-ui-automation
description: "Tap Android UI elements by selector resolved against the live uiautomator dump instead of hard-coded pixels: ordered selector lists, resolution-independent region bands, popup-dismissal doctrine with allowlist/denylist, color-scan fallback for unselectable buttons, and a FOUND/MISS harvest + regression workflow. Use when: automating taps in any Android app, coordinates broke after an app update or on a different-resolution phone, popups keep blocking a flow, 'resource-id is obfuscated', 'uiautomator selector', 'how do I tap the right button', 'calibrate selectors'."
---

# Selector-First UI Automation

Hard-coded pixel coordinates rot on every app update, every new device resolution, every locale change. This skill's rule: **resolve every tap target from the live `uiautomator dump`; per-device pixel coords are the logged, last-resort fallback only.**

## The selector model

A *selector* is one dict of match keys. A *target* is an **ordered list of selectors**, tried most-stable-first. Supported keys:

| Key | Match |
|---|---|
| `content-desc` | exact content-desc — **preferred** (usually human-readable and stable) |
| `desc_contains` | case-insensitive substring of content-desc |
| `text` | exact text |
| `text_contains` | case-insensitive substring of text |
| `region` | `"top"` / `"middle"` / `"bottom"` or a `(lo, hi)` y-fraction band, matched against node-center-y / screen-height — **resolution-independent** |
| `resource-id`, `class`, `clickable`, any raw node attr | exact match — resource-ids on big commercial apps are **obfuscated and churn across versions** (`com.zhiliaoapp.musically:id/xxx`); keep them last in the list knowing they will rot |

Region bands: `top` = (0.0, 0.25), `middle` = (0.25, 0.75), `bottom` = (0.75, 1.0) of screen height. They let one selector list work unchanged across a 1080×2400 phone and a 1200×2670 phone — only the thin per-device coords fallback differs.

Resolution algorithm (per tap attempt):

```
for selector in ordered_list:           # most stable first
    for node in ui_dump:
        if all keys match:
            return node_center(node), "selector:<spec>"
return coords_fallback, "coords_fallback"   # FINAL attempt only
```

Tap loop per target (`tap_element`): dismiss popups → dump → resolve → tap → poll a post-condition predicate; retry up to 3. **Use the coords fallback only on the final attempt** and log it loudly as `tap_<label>_COORDS_FALLBACK` — a fallback event in the run log means the selector harvest rotted and needs refreshing. That's your built-in rot detector.

## Screen-state disambiguation gotcha

The same label can appear on multiple screens (e.g. "System notifications" is both a row label on the inbox AND the header of the notification list). Disambiguate with a second landmark in a known region — e.g. the screen is "inbox" only if an exact `Inbox` title node exists with center-y in the top ~12% band. Screen-state classification is the foundation every verification gate stands on; make it structural, not single-string.

## Popup doctrine

Interstitials fire between flow steps and eat taps. Sweep for them before **every** target resolution, with a deliberately conservative policy:

**Allowlist** — only labels that are ~exclusively interstitial chrome:

```
not now, no thanks, maybe later, later, not interested, got it, don't allow, deny
```

`Cancel`, `Close`, `OK` are **deliberately excluded** — they also appear on flow-critical chrome (a search screen's Cancel, a picker's Close ✕) and auto-tapping them breaks the flow.

**Hard denylist** — never auto-tap these from a popup sweep, no matter what:

```
post, publish, delete, discard, allow, log out, logout, report, follow, share, next
```

Additional rules, each learned from a real incident:

- **Normalize labels before matching**: lowercase, strip, and fold curly apostrophes (U+2019) to ASCII — one app renders "Don't allow" with a curly `’` and it silently missed the straight-quote allowlist until normalization was added.
- **Marker-gated special cases**: some popups' only escape is a label that's excluded from the generic sweep (e.g. a bare Close ✕ on a "Add phone number" sheet). Handle those as `(markers, selector)` pairs: tap the selector **only if ALL marker strings** are present in the dump (e.g. `("Add phone", "Phone number")` → `content-desc: Close`).
- **Invisible-dialog gotcha**: some OS-style permission prompts render in a **window the uiautomator dump doesn't capture** — the dump shows the screen *behind* them and the run blocks forever. Rendering is inconsistent (the same prompt was dumpable on one phone, a separate undumpable window on another). Two-layer defense:
  1. **Pre-empt**: `pm revoke <package> READ_CONTACTS WRITE_CONTACTS GET_ACCOUNTS` in the keep-alive/preflight script, so the OS-permission variant never fires.
  2. **Catch**: when it does render in-window, the generic sweep dismisses it.
  If a separate-window variant still blocks a run, tap its negative button by coord or `pm revoke` whatever permission it's begging for.
- Harvest popups from **real sightings only**: log trigger, screen, exact button text, and whether it was visible in the dump. Never guess-add labels.

## Color-scan fallback (for buttons no selector can reach)

Some buttons have no usable text, desc, or stable id — e.g. an unlabeled red ✓ ImageView whose row position shifts with sheet height and scroll. Do NOT hard-code its y-coord. **Scan the screenshot for the brand color at a fixed x-column and group consecutive hits into button centers:**

```python
from PIL import Image
im = Image.open('/tmp/screen.png')
BRAND_RED = (254, 44, 85)
hits = [y for y in range(300, 2600, 10)
        if im.getpixel((1090, y))[:3] == BRAND_RED]
buttons, cur = [], []
for y in hits:
    if cur and y - cur[-1] > 30:   # gap > 30px = new button
        buttons.append(cur); cur = []
    cur.append(y)
if cur: buttons.append(cur)
centers = [(1090, sum(b) // len(b)) for b in buttons]   # tap these
```

The pattern generalizes to any app: pick the button's distinctive RGB, pick an x-column that crosses all rows of the list, scan, cluster, tap cluster centers. It's the fallback *below* coords — pixel-derived at runtime, not pixel-hard-coded.

## Harvest & regression workflow

Selectors are empirical. Maintain them like test fixtures:

1. **Harvest**: walk each flow screen on a real device (feed → inbox → list → editor → picker → publish), dump XML per screen, and for each target record the node's `content-desc`, `text`, `resource-id`, `class`, and whether it was CONFIRMED on-device or merely guessed. Mark guessed rows explicitly until a real run reaches that screen — screens behind real content (e.g. a draft editor) can't be harvested until the content exists.
2. **Registry**: one shared ordered selector list, hand-edited; per-device divergence goes in a per-device override block. The registry is NEVER auto-written by tooling — auto-derivation prints a ready-to-paste block for human review.
3. **Calibrate**: a guided script walks the operator screen-by-screen ("navigate to X, press Enter"), screenshots + dumps, resolves every target against the live dump and prints **FOUND/MISS per target** plus a derived coords-fallback block.
4. **Regression**: re-run calibrate after every app update. Every MISS on a previously-FOUND target = a selector rotted; refresh the harvest. A `COORDS_FALLBACK` in any production run log is the same signal, caught in the wild.
5. Calibrate also identity-checks the device (model + serial + `wm size`) and warns loudly on serial mismatch before you trust any results.

Full operator playbook — screen list, per-target harvest log template, popup sighting log, regression triggers: `references/selector-harvest-playbook.md`.

## Human-like pacing (for reliability, not stealth)

Pixel-identical taps, zero-latency actions, and robotic cadence correlate strongly with flaky automation *and* with platform automation-detection. Pace everything like a person, and treat it as a reliability feature:

- **Tap jitter**: randomize the tap point within ~9px of the resolved center (defeats pixel-identical-tap detection; ~14px on swipe endpoints).
- **Human-scale delays**: jitter sleeps ±35% around a base, or uniform in a range (e.g. 2.0–7.0s of "watch time" between feed actions).
- **Per-character typing**: 0.08–0.28s between characters instead of one instant `input text` blob.
- Keep an env flag (e.g. `ROBOTIC=1`) that disables pacing for debugging only — never in production runs.

## LESSONS LEARNED

- content-desc outlives resource-id by many app versions; obfuscated ids (`com.zhiliaoapp.musically:id/xxx`) churn constantly. Order selector lists accordingly.
- Region bands make one selector set work across resolutions — 1080×2400 and 1200×2670 needed zero selector divergence, only different coords fallbacks.
- Some screens can't be harvested until real content exists behind them; mark guessed selectors GUESSED and confirm on the first live run instead of trusting them.
- Popup handling that can tap `Post`/`Delete`/`Allow` will eventually do so. The denylist is a safety control, not a convenience.
- The same prompt can be dumpable on one device and an invisible separate window on another — pre-revoke the permission, don't rely on catching the dialog.
- An unlabeled button's row position depends on sheet height and scroll: derive it at runtime (color scan), never hard-code.
- Comments/inputs with a separate send button: tap send, then VERIFY the input cleared — don't type and move on.

## FAILURE CATALOG

| Symptom | Root cause | Fix |
|---|---|---|
| `tap_*_COORDS_FALLBACK` in run log | Selector rotted after app update | Re-harvest; calibrate FOUND/MISS regression |
| Taps land on wrong screen region | Same label exists on two screens | Disambiguate with a landmark node in a region band |
| Popup sweep broke the flow (closed search/picker) | Generic label like Cancel/Close in allowlist | Keep allowlist interstitial-exclusive; marker-gate special cases |
| "Don't allow" popup never dismissed | Curly apostrophe (U+2019) missed straight-quote label set | Normalize labels (lowercase + fold curly quotes) |
| Run blocked, dump shows normal screen behind | Separate-window permission dialog not in dump | `pm revoke` the permission in preflight; coord-tap fallback |
| Tap hits nothing after app update | Hard-coded pixel coords | Selector-first; coords only as final-attempt fallback |
| Tap on picker row does confusing things | Tapped a "videos with related sounds" carousel card, not a sound row | Expand sheet; use list rows found by color-scan, never carousel cards |
| Send-button tap "worked" but nothing sent | Typed but never verified | Verify input cleared after send; retry |
| Automation flagged / erratic blocks | Pixel-identical taps, zero latency | Human pacing: 9px jitter, human-scale delays, per-char typing |

## BEST PRACTICES

- Ordered selector lists: desc → text → region-banded attrs → resource-id last; coords fallback on the final attempt only, always logged.
- Every tap has a post-condition predicate; every step dumps UI XML + screenshot to the run dir.
- Popup sweep before every target resolution; allowlist/denylist harvested from real sightings only.
- Registry is hand-edited; tooling prints derived blocks for review, never auto-writes.
- Calibrate after every app update; treat production COORDS_FALLBACK events as regression alerts.
- Pace like a human everywhere; keep a debug-only flag to disable pacing.

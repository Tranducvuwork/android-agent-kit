---
name: android-screen-capture
description: Capture the screens of a running Android app from a connected device or emulator — screenshot, view hierarchy, and foreground activity — and write them into docs/features/<feature>/screens/ with a screens.md inventory that mold, blueprint, and the testing skills read. Use when the user says they will open a screen for you to capture, when a feature needs its current UI documented, or when a design exists only as the running app.
---

# Android Screen Capture

Goal: turn screens the user opens on a real device into files the rest of the kit can work from —
a PNG, a view hierarchy, and a written inventory — so no later step has to guess what the UI holds.

This is the entry point of the capture flow:

```
android-screen-capture → spark → [mold] → [slice] → blueprint → forge
```

`mold` reads the design. This skill **produces** that design when the only source is the running app.
It writes into the exact layout `mold` expects, so `mold` runs afterwards without conversion.

This skill only captures and writes docs. Never edit production source, resources, or the manifest.
Never install, uninstall, clear data, or change device settings — the user drives the app; you record it.

## Output

```
docs/features/<feature>/
  screens.md                   # inventory: every screen, its activity, actions, copy, open questions
  screens/
    <screen>.png               # the screenshot
    <screen>.uix               # uiautomator view hierarchy (when the dump succeeds)
    <screen>.meta.json         # device, activity, size, density, timestamp
    <screen>-<state>.png       # other states of the same screen, same naming as mold
```

`<feature>` is a kebab-case slug. `<screen>` is kebab-case, named after what the screen *is*
(`plant-detail`, `scan-camera`, `paywall`), never after the Activity class.

## Process

### 1. Check the device

```sh
adb devices
```

An mDNS/wireless serial contains spaces (`adb-XXXX-YYY (2)._adb-tls-connect._tcp`); always quote it.

- No device: tell the user to connect one and enable USB (or wireless) debugging, and stop.
- Several devices: ask which one, then pass `--serial` on every call.

Ask which app and which build is on the device if it is not obvious; record the answer in `screens.md`.

### 2. Agree the screen list before capturing

Ask the user, in one round:
- Which feature this is (the slug), and whether `docs/features/<slug>/` already exists.
- Which screens they will open, in which order, and which states of each matter
  (empty, loading, content, error, permission denied, logged out, dark mode).

Write the agreed list down. Capturing without a list produces files nobody can name later.

### 3. Capture, one screen at a time

For each screen: tell the user **exactly what to open**, in one short line, then wait for them to say
it is on screen. Never capture before they confirm — a capture of the wrong screen is worse than none,
because it looks like evidence.

```sh
bash "$SKILL_DIR/scripts/capture-screen.sh" \
  --out docs/features/<feature>/screens \
  --name <screen> \
  --serial "<serial>"      # omit when exactly one device is attached
```

Options: `--settle <sec>` waits before capturing (animations, splash); `--no-dump` skips the view
hierarchy when `uiautomator` is unavailable.

The script prints `png=`, `uix=`, `meta=`, `activity=` and `uix_status=`. Read the PNG yourself with the
Read tool before moving on — if it shows a different screen than asked for, say so and capture again.

For another state of the same screen, use `--name <screen>-<state>` (`plant-detail-error`), matching
`mold`'s state naming.

### 4. Read the hierarchy, don't guess from pixels

```sh
python3 -I "$SKILL_DIR/scripts/dump-to-outline.py" \
  docs/features/<feature>/screens/<screen>.uix --format markdown
```

`--format outline` gives the indented tree, `--format json` the raw nodes. Invisible and purely
structural containers are dropped; pass `--include-invisible` to keep them.

The outline is the ground truth for copy, `resource-id`s and what is actually clickable. The PNG is the
ground truth for layout, color and spacing. Use each for what it knows:

- Copy, ids and actions come from the dump, **verbatim**, including Vietnamese diacritics.
- Sizes, colors and spacing read from the PNG are estimates — write them as `(estimated)` or leave them out.
- `uix_status=failed`, obfuscated ids (`0_resource_name_obfuscated`), or a screen drawn in Compose with no
  `testTag` all mean the dump is thin: say so in `screens.md` rather than inventing ids.
- Anything illegible is `⚠ unreadable`, never a guess.

### 5. Match against the codebase

Use `activity=` from the capture to find the screen in the project (`grep` the Activity or Fragment name,
then its layout). Record for each screen: the Activity/Fragment, its layout file, and the strings
resource backing each piece of copy. This is what makes the inventory usable by `blueprint` and by
`android-automation-testing-setup`.

Stay read-only. Where a screen cannot be located in the source, write `not found in source` and move on.

### 6. Write screens.md

Use [assets/templates/screens-template.md](assets/templates/screens-template.md). Rules:

- One row per screen in the index; one `##` section per screen.
- Copy is verbatim; ids are as the dump prints them.
- Every claim traces to a file: the PNG, the `.uix`, or a source path.
- Open questions stay open. Do not resolve them by assumption.
- Do not describe implementation (no class to create, no architecture): that belongs to `blueprint`.

### 7. Finish

Report: the screens captured with their files, which dumps failed, what was not found in source, and the
open questions. Suggest the next step — `spark` for a new requirement over these screens, or `mold` when
a separate design also exists — and do not run it yourself.

## Privacy

Screenshots of a live app capture whatever is on screen: real accounts, tokens in a debug overlay,
personal data, payment details. Before writing a capture into the repo, check the PNG and the dump for
anything the user would not want committed, and tell them what you found. Never commit captures the user
has not seen. A screen holding credentials is described in words instead, with no PNG.

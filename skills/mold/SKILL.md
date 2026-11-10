---
name: mold
description: Read a feature's design once (Figma link, screenshots, or draw.io) and write docs/features/<feature>/design.md plus one file per screen, covering layout, states, copy, navigation, and assets, so later steps never re-read the design. Use after spark when a design or flow exists, or when the design changes.
---

# Mold

Goal: turn the design into text that slice, blueprint, and forge can work from without opening the design
again, and that a reviewer can check against the design in one pass.

The design is read **once**, here. The output describes **what the UI looks like and how it moves**, never
how to build it: no module, class, or Composable names. Mapping design names to code is `blueprint`'s job.

`task.md` holds the rules (what and why); `design.md` holds the presentation (layout, copy, transitions).
Never copy requirements into design.md; link to `AC-n` / `EC-n` instead.

This skill only writes docs and fetches design files: do not run build, test, lint, or format commands, even
if CLAUDE.md lists checks to run before finishing. Do not touch `res/` or any source set; `forge` moves
assets into the project.

Do not re-ask anything answered in the linked task.md.

## Output

```
docs/features/<feature>/
  design.md                 # index: sources, screen list, navigation, assets, cross-check
  screens/
    <screen>.md             # one per screen: layout, states, components, copy, notes
    <screen>.png            # screenshot of the default state
    <screen>-<state>.png    # screenshots of other states
  assets/                   # raw exported files: svg, png, lottie json
```

The structure is the same for every feature, even a one-screen one, so later skills never branch on it.

## Process

### 1. Collect the input

- Read `docs/features/<feature>/task.md`. If it doesn't exist, suggest `spark` first and stop. If it is
  Draft, warn the user and continue.
- If `design.md` already exists, go to **Updating** below.
- Accept any mix of: Figma links, screenshots or exported images, `.drawio` files, designer notes.
- No design at all: tell the user this skill needs one, and stop.

### 2. Read the design once

**Figma link**: read [figma.md](figma.md) and follow it for access, token rules, and fetching.

**Screenshots and draw.io** are read directly, no setup needed:
- Expect one screen per image. Propose a mapping of images to screens and states (from file names such as
  `bookmark-list-empty.png`, or from what you see for names like `IMG_2031.png` or an image holding several
  screens) and confirm it in one question. Copy each image into `screens/` under its final name; keep a
  multi-screen image whole as `screens/<feature>-flow.png`.
- Copy is read by eye: small text and Vietnamese diacritics are error-prone. Ask whether a text source
  exists (strings file, spreadsheet).
- Colors, sizes, and spacing are estimates only. Map them to the nearest theme token from step 3 and note
  `(estimated)`; never write a hex or dp value as if it were exact.
- Assets cannot be extracted from pixels: anything not matched in step 3 is `needs-export`.
- For `.drawio`, read every node, edge with its label, decision branch, and note.

Mark anything illegible `⚠ unreadable` instead of guessing.

Classify what you find:

| In the design | Becomes |
|---|---|
| Frame or image of one screen | A screen |
| Frames named `<Screen> / <State>`, images named `<screen>-<state>` | States of that screen |
| Dark, landscape, tablet, large-font, or RTL frame of a screen | A Variants row of that screen |
| Prototype interaction | A Navigation row, `Source: prototype` |
| Drawn arrow, connector, or `.drawio` edge | A Navigation row, `Source: drawn ⚠` |
| No flow in the design | Rows proposed from task.md and the screens, `Source: proposed` until confirmed |
| Text or sticky note beside a frame | Notes of that screen, verbatim |
| Icon, illustration, image, animation | A row in the Assets table |

### 3. Match against the project

Read only enough to name things that already exist: CLAUDE.md, the design system module, the theme
(color / typography / spacing token names), and `res/drawable*` / icon sets. Use this to:
- Mark assets that already exist (`exists`) or come from an icon library (`reuse`) instead of exporting.
- When a screen needs both states of an icon (filled and outline, on and off), always list both rows, even
  if the design draws only one or the other seems unneeded: later steps read only this table.
- Name tokens by the token name only (`textTertiary`, `bodyLarge`), never with a class, object, or package
  prefix (`SampleColors.`, `MaterialTheme.typography.`); otherwise by their Figma style name, or as the
  nearest token name marked `(estimated)` when read from an image. When the Figma file defines no color
  or text styles, say so in the design's visual tokens and record the raw values read from the frames
  (hex, gradient stops, sizes); don't map them to the project's theme names.

### 4. Cross-check

List every mismatch between screens, flow, and task.md:
- A screen no flow leads to. A screen the user rules out of scope is still listed as an orphan if no flow
  leads to it.
- A flow destination with no screen design.
- A state with no way out (error without retry, dead end without back).
- A trigger in the flow with no matching control on the screen.
- A UI state or flow step that task.md requires but the design doesn't show, and the reverse.

### 5. Ask in rounds

Ask 2–4 multiple-choice questions per round, recommended option first with a short reason, about the
cross-check items and anything ambiguous: missing states, unreadable copy, assets with no source, drawn or
proposed flow. Always allow a free-text answer. An unanswered item stays under Open questions.

### 6. Write the files

Use the templates below. Rules:
- **Screen file names follow the design**, not code: the Figma frame name or the confirmed image name,
  slugified to kebab-case, with numbering prefixes dropped and diacritics removed
  (`01 - Bookmark List` → `bookmark-list`).
- **Stable key**: the Figma node id when the source is Figma; the screen file name otherwise. Store it in
  the screen file so updates find the right file.
- **Copy is verbatim**, including punctuation. Placeholder copy in wireframes is marked `_placeholder_`.
- **No duplication**: Navigation and Assets live only in design.md; screen files list asset names only.
  A component used on several screens is described in the first screen that uses it and referenced by name
  elsewhere.
- Set `Fidelity`: `wireframe` (no final copy, colors, or assets), `mockup`, or `final`.
- **Variants**: fill the table for dark, landscape / tablet, and large font (add RTL if task.md needs it).
  `no` means not designed, not "not needed"; if task.md requires a variant the design lacks, list it in
  Cross-check. Write `yes` only for a variant the design actually draws (a frame or an explicit note);
  never infer one from the theme or from the example below.

Show the user the paths with a short summary (screens and states, asset counts by status, open questions)
and ask them to review. Set `Status: Confirmed` only when they approve.

### 7. Finish

- If the design revealed requirements task.md lacks (a confirm dialog, a back-stack rule, a new state),
  list them and suggest updating task.md through `spark`. Do not edit task.md yourself. This includes a
  requirement the design asks for that the user ruled out of scope in this round (a gesture, a sort): name
  it and say it would need `spark` to come back in.
- Suggest the next step without running it: `slice` for a large task, otherwise `blueprint`.

## design.md template

```markdown
# <Feature name> — Design

Status: Draft | Confirmed
Requirement: [task.md](task.md)
Fidelity: wireframe | mockup | final
Source: <Figma link | image paths | drawio path>
Captured: <YYYY-MM-DD>

## Screens
| Screen | File | States |
|---|---|---|
| Bookmark List | [bookmark-list](screens/bookmark-list.md) | Content, Empty, Loading, Error |

## Navigation
| From | Trigger | To | Back | Source |
|---|---|---|---|---|
| bookmark-list | tap item | bookmark-detail | to bookmark-list | prototype |
| add-bookmark | tap Save (succeeds) | bookmark-list | removes add-bookmark | drawn ⚠ |

Entry points: <tab, deep link, notification...>

## Assets
| Name | Type | Source | Status | Used in | Notes |
|---|---|---|---|---|---|
| ic_bookmark | vector | core designsystem | exists | bookmark-list | tinted with text color |
| img_empty_saved | vector | Figma 45:120 → assets/img_empty_saved.svg | provided | bookmark-list | dark variant |

Status: `exists` (in the project) · `reuse` (icon library, name only) · `provided` (file in assets/) ·
`needs-export` (no file yet). Names follow Android prefixes: `ic_`, `img_`, `bg_`, `anim_`.

## Cross-check
- ⚠ <mismatch> → <resolution or open question>

## Open questions
- [ ] ...

## Change log
- <YYYY-MM-DD>: Initial version.
```

## screens/<screen>.md template

````markdown
# <Screen name>

Key: <Figma node id `12:34` | screen name when the source is images>
Screenshots: [default](<screen>.png), [empty](<screen>-empty.png)
Covers: AC-1, AC-3, EC-2

## Layout
```
┌─────────────────────────┐
│ ← Saved            🔍   │  top bar
├─────────────────────────┤
│ [img] Title         ⋮   │  item × n
└─────────────────────────┘
```

## States
| State | What is shown | Actions |
|---|---|---|

## Components
- <Component>: <parts, variants, tokens used, sizes that matter>

## Copy
- Title: "Saved"
- Empty: "Nothing saved yet"

## Assets
- ic_bookmark, img_empty_saved

## Variants
| Variant | Designed | Differences |
|---|---|---|
| Dark | no | |
| Landscape / tablet | yes | 5 columns instead of 3 |
| Large font | no | |

## Notes
- <designer notes, verbatim>
````

## Updating

When the design changes (new link, new images, or `update` in the request):
1. Read the current design.md and screen files.
2. Find what changed. Figma gives no per-frame change date, so re-fetch only the structure (frame ids,
   names, sizes, text) for the link and compare it with the screen files by stable key; images are
   compared by name and by eye with the saved screenshots. Fetch details and screenshots only for the
   frames that differ; if the structure shows no difference, make no detail or screenshot call at all, and
   report that nothing changed. If a Figma frame was renamed, ask whether to rename the file; if a new image
   matches no screen, ask whether it is a new screen or a renamed one.
3. Show the changes as a short list (screens, states, navigation, assets: added / changed / removed) and
   wait for approval. Answers to the questions in step 2 (a rename, a new screen) do not replace this:
   print the list afterwards, ask "Apply these changes?", and edit nothing before the yes.
4. Apply them, add a Change log line, update `Captured`, and set `Status: Draft` until re-approved.
5. If `subtasks/` or `implement-plans/` exist next to task.md, list the ones affected and suggest updating
   them (`slice` for subtasks, `blueprint` for plans). Do not edit them yourself.

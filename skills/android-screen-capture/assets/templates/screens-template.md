# Screens — <Feature name>

Status: Draft | Confirmed
Captured: <yyyy-mm-dd>
App: `<applicationId>` · Build: `<variant / version name>`
Device: `<model>` · Android `<release>` (SDK `<int>`) · `<width>x<height>` @ `<density>`dpi

> Captured from the running app with `android-screen-capture`. Copy and `resource-id`s are read from the
> view hierarchy and are verbatim. Sizes, colors and spacing are read from the screenshots and are
> estimates unless a source file is cited.

## Index

| # | Screen | File | Activity / Fragment | Layout | States captured |
|---|---|---|---|---|---|
| 1 | <Screen name> | `screens/<screen>.png` | `<Activity>` | `res/layout/<file>.xml` | default, empty, error |

## Flow

| From | Trigger | To | Source |
|---|---|---|---|
| <screen> | <control the user taps> | <screen> | observed / proposed |

`observed` = seen during capture. `proposed` = inferred, still to confirm.

---

## <Screen name>

- **File**: `screens/<screen>.png` · hierarchy `screens/<screen>.uix` · meta `screens/<screen>.meta.json`
- **Activity**: `<package>/<Activity>`
- **Source**: `app/src/main/java/.../<Activity>.kt` · layout `res/layout/<file>.xml`
- **Purpose**: <one line: what the user does here>

### Copy

| Text (verbatim) | resource-id | String resource |
|---|---|---|
| <text> | `<id>` | `R.string.<name>` / not found |

### Actions

| Control | resource-id | What it does | Goes to |
|---|---|---|---|
| <label> | `<id>` | <observed or stated behavior> | <screen> / stays |

### Inputs

| Field | resource-id | Type | Validation seen |
|---|---|---|---|

### States

| State | Screenshot | How to reach it | What changes |
|---|---|---|---|
| default | `screens/<screen>.png` | — | — |
| empty | `screens/<screen>-empty.png` | <steps> | <what the user sees> |
| error | `screens/<screen>-error.png` | <steps> | <message, retry control> |

### Layout notes

- <structure read from the screenshot: regions, order, what scrolls> — spacing and colors `(estimated)`.

### Not captured

- <state or variant that was agreed but could not be reached, and why>

---

## Gaps and open questions

- [ ] <question> — <why it matters, what would answer it>

## Capture quality

| Screen | Hierarchy dump | Ids usable | Notes |
|---|---|---|---|
| <screen> | ok / failed / skipped | yes / obfuscated / none | <e.g. Compose with no testTag> |

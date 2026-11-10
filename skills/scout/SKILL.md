---
name: scout
description: Explore an Android codebase and generate or update a concise CLAUDE.md (setup, commands, modules, architecture, conventions, reusable components, do-nots). Use when starting on a new repo, or when asked to onboard, analyze the codebase, or create/refresh CLAUDE.md.
---

# Scout

Goal: a CLAUDE.md that lets Claude write code that fits this project on the first try — right module, right
pattern, existing components reused, no boilerplate the project doesn't use. It is a map and a rulebook,
not a tutorial.

## Principles

- **Evidence over assumption.** Every statement in CLAUDE.md must come from a file you read or a command
  you ran. Do not write "uses MVVM" because it is an Android project; write it because you saw the ViewModels.
- **Only what Claude can't cheaply infer.** Skip anything obvious from one file read (e.g. "Kotlin files end
  in .kt"). Keep what costs many reads to discover or is easy to get wrong.
- **Concrete names.** Real class, module, plugin, and task names — not "use the base class".
- **Short.** Target 100–150 lines. Per-layer detail belongs in `.claude/rules/` (see the `rulebook` skill).
- **Read-only** until the user approves the draft. No source edits, ever.

## Process

### 1. Check what exists

- Read any existing `CLAUDE.md`, `AGENTS.md`, `README*`, `docs/`, `CONTRIBUTING*`, `.github/` (workflows,
  PR templates), `.claude/rules/`.
- If CLAUDE.md exists: treat it as a hypothesis. You will verify each claim and propose a diff (step 6),
  not rewrite blindly. Verify its Setup section against the build files too: every `local.properties`
  key or secret the build reads (`BuildConfig` fields, `localProperties`, `System.getenv`) must be named
  there. One that is missing from Setup goes under **Missing**, even if another section mentions it.

### 2. Explore (read-only)

Cover each area below. For large repos, dispatch parallel read-only subagents (one per area) and ask each for
findings with file paths as evidence, not file dumps.

| Area | Look at | Capture |
|---|---|---|
| Build & toolchain | `settings.gradle(.kts)`, root and module build files, `gradle/libs.versions.toml`, `gradle.properties`, `build-logic/` or `buildSrc/`, `gradle-wrapper.properties` | JDK, compile/min/target SDK, Kotlin/AGP versions, flavors and build types, convention plugins, config cache / isolated projects, required `local.properties` keys or secrets |
| Commands | CI workflows, convention plugins, README | Exact build, unit test, UI/screenshot test, lint, format, static analysis commands CI actually runs |
| Modules | `settings.gradle(.kts)` includes, each module's build file dependencies | Module list grouped by type, purpose, allowed dependencies (who may depend on whom) |
| Architecture | 2–3 representative features end to end | Layers and data flow (UI → state holder → domain → data → sources), state modeling, error/loading handling, threading |
| UI | Screens, design system module, theme | Compose or Views, design system components, navigation library and how routes are declared and wired |
| Data | Repositories, network, database, preferences, sync | Network client, DB, local storage, offline/caching strategy, model mapping between layers |
| DI | DI modules, entry points | Library (Hilt/Koin/manual), where bindings live, flavor-specific bindings |
| Testing | `src/test`, `src/androidTest`, test modules | Frameworks, fakes vs mocks, test rules, naming, screenshot testing, where test doubles live |
| Conventions | Lint config, custom lint rules, formatter config, license headers, git log | Naming, resource prefixes, commit/branch style, enforced rules |
| Generated/baseline files | Schemas, baselines, golden images, dependency lists | Files that must not be hand-edited and the task that regenerates each |

Pick a **reference feature**: the most complete feature (full stack + tests) and the simplest one, to point
new work at.

### 3. Verify commands

Confirm every command you plan to document exists, without running a real build:
- `./gradlew tasks --all` (or `./gradlew :<module>:tasks`) filtered with grep, or `./gradlew <task> --dry-run`.
- Note tasks that only work under certain flags (e.g. disabled under isolated projects) and the workaround.
If the wrapper can't run (missing SDK/JDK), say so and mark the commands as unverified.

### 4. Ask the user

Ask only what code can't answer, in one round of multiple-choice questions where possible. Typical:
- Contradictions found (two patterns for the same thing — which is the target, which is legacy?).
- Intent: which modules/patterns are deprecated or being migrated away from.
- Team rules not encoded anywhere (review rules, commit format, branch naming, definition of done).
- Which commands must run before a change is considered finished.
Skip the round if nothing is unclear.

### 5. Draft CLAUDE.md

Use this structure; drop sections that don't apply, keep headings short:

```markdown
# <Project name>

<One or two lines: what the app is + main stack. Any build-wide constraint that affects how code is written.>

## Setup
- JDK, SDK levels, required local config/secrets, flavors and which variant to use day to day.

## Commands
- Build / unit tests (one module, all) / UI or screenshot tests / format / lint / static analysis.

## Before finishing a code change
Applies only when source or build files changed. Docs-only changes (`*.md`): run nothing. Report results honestly.

Default (after every code change): build and unit-test touched modules, auto-format, regenerate
baselines if dependencies changed. Keep this tier fast.

Full (only when the user asks, or before opening a PR): format check, lint, static analysis,
screenshot verify if UI changed, instrumented tests. If skipped, say which ones in the report.

## Architecture
- Layers and data flow, state holder pattern, UI state shape, navigation pattern, model mapping chain.

## Modules
| Module | Purpose | May depend on |

## Conventions
- New modules, resources, DI, threading, analytics/logging, tests (doubles, naming), commits/branches.

## Reuse before you create
| Need | Use | Module |

## Reference features
- <feature> - what it demonstrates.

## Do not
- Concrete prohibitions, each with the correct alternative or the regenerate command.
```

Writing rules:
- One fact per bullet; imperative voice for rules ("Inject dispatchers with X; never Y").
- Commands in backticks, exactly as runnable.
- Every "do not" names the right way.
- No version numbers that change often (library versions) unless they constrain how code is written.
- If `.claude/rules/` exists or will exist, add a one-line pointer to it.
- Always split "Before finishing" into the two tiers above, scoped to code changes. A single unscoped
  checklist makes Claude run slow checks after docs-only work and conflicts with skills that limit checks.
- Put a command in the default tier only if it runs in about a minute per module; anything slower
  (lint over all variants, screenshot, instrumented) goes in the full tier.
- "Reuse before you create" is a short signpost, not a catalog: at most ~12 rows. Include only components
  Claude would likely re-implement if not told — shared, used in 2+ places or living in a core/shared
  module, and not obvious from one file read (design system prefix, result/error wrapper, dispatcher or
  scope injection, shared UI pieces, test doubles). Prefer a naming pattern plus module (`Xyz*` in
  `core:designsystem`) over listing every class. The `blueprint` skill does the full per-task search.

### 6. Review with the user

- New file: show the full draft.
- Existing file: show a diff-style summary grouped as **Wrong (fix)**, **Missing (add)**, **Stale (remove)**,
  each with its evidence (file path), then the full proposed file: every line of it, with no `…` or
  "unchanged" placeholder standing in for a section.
- Ask for approval or changes. Iterate until approved. Write the file only after an explicit yes.

### 7. Finish

- Write `CLAUDE.md` at the repo root.
- Report: line count, sections, commands verified vs unverified, open questions left.
- Suggest next step: run `rulebook` for per-layer rules. Do not run it yourself.

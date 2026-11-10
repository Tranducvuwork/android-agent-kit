---
name: blueprint
description: Write an implementation plan of ordered, buildable steps mapped to acceptance criteria for an Android requirement (task.md, subtask, chat, or ticket). Writes no production code. Use before implementing any non-trivial change.
---

# Blueprint

Goal: a plan concrete enough that the `forge` skill can execute it without new decisions, and that a
reviewer can check before any code exists. Every decision is made here; every question is answered here.

This skill only writes docs: do not run build, test, lint, or format commands, even if CLAUDE.md lists
checks to run before finishing. Read-only searches (grep, find, git log) are fine.

Do not re-ask anything answered in the linked task.md / subtask / plan.

## Process

### 1. Load the requirement

- **task.md / subtask file**: read it, plus task.md when the input is a subtask. Use its `AC-n` / `EC-n` IDs.
- **Chat, ticket, bug report**: extract acceptance criteria (Given/When/Then, numbered `AC-1...`) and edge
  cases yourself, and confirm them with the user before planning. Pick a feature slug for the output path.
- **Design**: if `design.md` exists next to task.md, read it and the screen files the subtask's `Design:`
  line links (all of them when planning from task.md). Do not open the design itself (Figma, images).
- If the requirement or design.md is Draft or has open questions that block planning, list them and ask
  first.
- If the plan file already exists (see the output path in step 5), go to **Updating** below.

### 2. Load the project rules

Read `CLAUDE.md` and every `.claude/rules/*.md` whose paths match the modules you expect to touch. These
override your defaults. When they conflict with what you see in code, follow the rules and mention the conflict.

### 3. Explore the codebase

Find, with file paths as evidence:
- **Where it goes**: the modules and packages to touch or create, and their allowed dependencies.
- **Closest existing example**: a feature or class that already does something similar — the plan copies its shape.
- **Components to reuse**: start from CLAUDE.md's "Reuse before you create" table, then sweep the
  categories below that the requirement touches. Search before planning anything new; a new component
  needs a reason why no existing one fits.
- **Patterns to follow**: state holder and UI state shape, error/result handling, threading, model mapping,
  resource naming, test style.
- **Design mapping** (when design.md exists): each screen to a screen and route, each component to an
  existing design system component (or a reason for a new one), each token to its theme name, each
  Navigation row to how navigation is wired, and each asset to its destination (shared design system
  module or the feature module) and format (VectorDrawable, WebP, `res/raw` for Lottie). Map each Copy
  line to a string resource (key, module, existing shared string to reuse, which locales need it;
  `_placeholder_` copy is listed under Risks), and each designed Variant to how it is handled (theme
  attribute, `-night` / `-land` / `-sw600dp` resource, or layout logic).

Reuse checklist (skip categories the requirement doesn't touch):

| Category | Look for |
|---|---|
| UI components | Design system: buttons, text fields, top bar, dialogs, list items, loading, empty/error states. Views: custom views, base adapters |
| Theme & resources | Theme, color/typography tokens, icon set, dimens, shared strings |
| Screen scaffolding | Base screen/Fragment/Activity, state holder base, UI state wrappers, preview helpers |
| Navigation | How routes/destinations are declared and wired, navigation helpers, deep links |
| Network | HTTP client, API services, interceptors, response/error wrapping, DTOs |
| Local storage | Database, DAOs, entities, migrations, preferences/DataStore, cache policy |
| Data & domain | Repositories, use cases, result/either type, mappers, paging |
| Async & background | Dispatcher injection, shared coroutine scopes, WorkManager/sync |
| Cross-cutting | Logging, analytics, error reporting, permissions, image loading, date/time/format utils, feature flags |
| DI | Qualifiers, scopes, a module to copy |
| Testing | Fakes/test doubles, test rules (main dispatcher...), fixtures/test data, screenshot helpers |

How to search: list the public API of core/common/shared modules; grep feature modules for the most
imported prefixes, base classes, and extension functions; check custom lint rules, which usually point
at components that must be used.

For broad searches use read-only subagents and ask for conclusions with paths, not file dumps.

### 4. Ask the user

Ask in rounds of 2–4 multiple-choice questions, recommended option first with a one-line reason, covering:
- **Technical choices** with real trade-offs: new module vs existing, new API field vs derive locally,
  schema change and migration, library addition.
- **Requirement gaps** found while exploring: behavior the requirement didn't specify but the code forces a
  choice on (e.g. what to show when the cached copy is stale).
Don't ask what CLAUDE.md, rules, or existing code already answer. Continue until nothing is open.

### 5. Write the plan

Output path:
- From a subtask: `docs/features/<feature>/implement-plans/NN-<slug>.md` (same name as the subtask).
- From task.md or another input: `docs/features/<feature>/implement-plan.md`.

```markdown
# Plan: <title>

Requirement: [<subtask or task>](<relative path>) | <chat / ticket link>
Status: Draft | Approved | In progress | Done

## Summary
<2–4 sentences: approach and why.>

## Decisions
- <Decision> — <reason>. (Answers from the user, with the alternative rejected.)

## Reuse
| Need | Existing component | Location |

## Design mapping
<Only when design.md exists.>
| Design (screen / component / token / navigation / copy / variant) | Code |

## Assets
<Only when design.md lists assets.>
| Asset | Status | Action | Destination | Step |

## Changes overview
| Module | Files (new / modified) | Why |

## Steps
### Step 1: <title>  (AC-1, AC-2)
- Files: `path/New.kt` (new), `path/Existing.kt` (modify)
- What: <changes in bullets: classes, function signatures, UiState shape, DI bindings, resources>
- Pseudo-code: <only for logic that isn't obvious>
- Unit tests: <test class, cases by name>
- Compile: `<compile command for the modules this step touches>`

### Step 2: ...

## Traceability
| AC / EC | Step(s) | Test(s) |

## Out of scope
- <What this plan intentionally does not do, and where it is handled.>

## Risks
- <Risk> — <mitigation>.
```

Rules for steps:
- Ordered so that **after each step the project compiles**; unit tests run once after the last step.
- Signatures and data shapes, not full implementations. Pseudo-code only for non-obvious logic.
- Every AC and EC appears in Traceability with at least one step and one test (or a manual check, stated).
- Only the files the requirement needs. No speculative abstractions, base classes, or "for later" hooks.
- Commands are the real ones from CLAUDE.md.
- Assets are added in the step that first uses them: `provided` ones converted from `assets/` into the
  destination, `exists` and `reuse` ones referenced. `needs-export` ones get a placeholder, and the plan
  lists them under Risks.
- If a step changes the public API of a shared module, its Compile line also covers the modules that
  depend on it, and Changes overview lists them as affected.

### 6. Review

Self-check before showing it: every reused component exists at the stated path; the dependency direction
follows CLAUDE.md; nothing in the plan duplicates an existing component. Then ask the user to review the
file. Apply changes they ask for. Set `Status: Approved` only after an explicit yes; if the input was a
subtask, set its `Status: Planned` at the same time.

### 7. Finish

Suggest running `forge` on the plan. Do not start coding.

## Updating

When the plan exists and the requirement, design, or the user's request has changed:
1. Read the plan, its Status, and which steps are ticked (`✅`, done by `forge`).
2. Work out what the change affects through the AC/EC IDs and design screens it touches, using
   Traceability and Design mapping. Explore and ask (steps 3–4) only for the affected part.
3. Show the changes as a short list (steps added / changed / removed, decisions changed) and wait for
   approval. Ticked steps are never rewritten: a change to finished work becomes a new step after them.
   Never renumber steps; new steps go at the end or take a suffix (`Step 3b`).
4. Apply them, update Traceability, add a `## Change log` line, and set `Status: Draft` until re-approved.
   If any step was ticked, say that `forge` should resume from the first unticked step.

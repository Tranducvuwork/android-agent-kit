---
name: spark
description: Clarify a feature idea or requirement through rounds of questions and write docs/features/<feature>/task.md, the source of truth for the requirement. Use to brainstorm or at the start of a new feature, when a feature request is vague, or when asked to change an existing requirement.
---

# Spark

Goal: turn an idea into a `task.md` that a reviewer agrees with and that later steps (slice,
blueprint) can work from without asking again what the feature is supposed to do.

`task.md` describes **what** and **why**, never **how**. No module, class, or library names unless the
requirement itself demands them (e.g. "must work offline", "must use the existing login").

This skill only writes docs: do not run build, test, lint, or format commands, even if CLAUDE.md lists
checks to run before finishing.

## Process

### 1. Collect the input

Accept any mix of:
- Chat text.
- File paths (markdown, PRD, notes): read them fully.
- Images, screenshots, designs: take only what the requirement needs (screens, states, actions, flow) and
  confirm it. Leave layout, copy, and assets to `mold`; note the design under `Source`.
- Ticket or wiki links: read through an available connector. If none is available, ask the user to paste the content.

List `docs/features/`. If a folder looks like the same or an overlapping feature (by slug or by its task.md
Goal), ask whether this is an update to it or a new feature. For an update, go to **Updating task.md** below.
When the request names an existing feature's slug (`/spark <slug>: …`), it is an update: go straight to
**Updating task.md** without asking.

### 2. Light context read

Read only enough of the project to ask good questions: CLAUDE.md, the screens or features the idea touches,
and related existing behavior. The point is to spot conflicts and reuse ("there is already a bookmark
feature — should this extend it?"), not to design the solution.

### 3. Ask in rounds

Ask 2–4 multiple-choice questions per round, with a recommended option first and a short reason. Always
allow a free-text answer. Go through these topics in order, skipping what the input already answers:

1. **Goal** — the user problem, who it is for, how success is judged.
2. **Scope** — what is in, what is explicitly out, which screens/entry points.
3. **Behavior** — main flow step by step, UI states (empty, loading, content, error), user actions and their results.
4. **Edge cases** — no network, empty data, permission denied, interruption (background, rotation, process
   death), very long or missing content, repeated actions, concurrency.
5. **Constraints** — platforms/API levels, offline, performance, accessibility, localization, analytics,
   privacy, existing behavior that must not change.

Rules:
- Never assume an answer silently. If you choose a default, state it and let the user override it.
- Each round builds on the last; don't re-ask what's settled.
- Stop when every topic is either answered or explicitly deferred. Usually 2–4 rounds.

### 4. Confirm the summary

Before writing, post a short summary in chat: goal, in/out of scope, main flow, the acceptance criteria as
one-liners, and open questions. Ask the user to confirm or correct it. Iterate until confirmed.

### 5. Write task.md

Pick a short kebab-case feature slug (confirm it with the user if not obvious) and write
`docs/features/<feature>/task.md`:

```markdown
# <Feature name>

Status: Draft | Confirmed
Source: <chat / file path / ticket link>

## Goal
<Problem, target user, and the outcome in 2–4 sentences.>

## Scope
### In scope
- ...
### Out of scope
- ...

## User flow
1. ...

## UI states
| State | When | What the user sees / can do |

## Acceptance criteria
- **AC-1** <short title>
  - Given ...
  - When ...
  - Then ...

## Edge cases
- **EC-1** <situation> -> <expected behavior>

## Constraints
- ...

## Open questions
- [ ] ... (owner, needed before which step)

## Change log
- <YYYY-MM-DD>: Initial version.
```

Rules for the content:
- Every acceptance criterion is observable and testable by a user or a test; no "should work well".
- IDs (`AC-n`, `EC-n`) are stable: never renumber; mark removed ones `~~AC-3~~ (removed: reason)`.
- Edge cases state the expected behavior, not just the situation.
- UI states say when a state happens and what the user can do; how it looks and its exact copy belong in
  `design.md` (`mold`).
- Keep it to what was agreed. Don't invent requirements the user didn't confirm.

Show the user the path and ask them to review. Set `Status: Confirmed` only when they approve.
`Confirmed` may keep open questions only if each names its owner and the step it is needed before, and none
is needed before the next step (`mold`, `slice`, or `blueprint`). Resolve those first, or keep `Draft`.

### 6. Finish

Suggest the next step without running it:
- A design or flow exists (Figma link, screenshots, draw.io): `mold` first, then the steps below.
- Large task (several screens, several layers, or more than one reviewable diff): `slice`.
- Small task: `blueprint` directly on task.md.

## Updating task.md

When the user asks to change the requirement (in chat or with new material):
1. Read the current task.md.
2. Ask questions only about what the change leaves unclear, in the same round style: how it touches
   behavior the task.md already defines (does removing a title here also clear it elsewhere?), 2–4
   questions in total. Before asking, reread the request: whatever it states (a gesture, the outcome of
   an action, an Undo) is settled, so do not ask it again. Do not ask how to split the work into
   subtasks or plans; `slice` and `blueprint` do that (step 5). Settle the remaining details (Undo timing,
   accessibility, rotation, process death) with a default and record it as `(assumed)` in the new
   criteria instead of asking.
3. Show the proposed changes as a short list (added / changed / removed, with IDs) and wait for approval.
4. Apply them, keep IDs stable, add a Change log line, and set `Status: Draft` until re-approved.
5. If `design.md`, `subtasks/`, or `implement-plans/` exist next to task.md, list the ones affected by the
   change and suggest updating them (`mold` for design.md, `slice` for subtasks, `blueprint` for plans). Do
   not edit them yourself.

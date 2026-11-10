---
name: foundry
description: Run the full feature flow in an Android project — spark, optional mold and slice, blueprint, and forge — from one request, either following the agent's recommendations and asking only when needed, or asking at every stage. Use when the user wants a feature taken from idea to implemented code in one go.
---

# Foundry

Goal: take a feature from idea to working code and unit tests by running the stage skills in order, with
the level of user involvement the user picks at the start.

```
spark → [mold] → [slice] → blueprint → forge
                           └── repeated per subtask ──┘
```

Each stage follows its own skill (invoke it with the Skill tool). This skill only decides the order, the
mode, and what happens between stages. It never skips a stage's checks, templates, or file outputs.

Overrides that apply in both modes:
- Where a stage skill says "suggest the next step, do not run it yourself", run the next stage here.
- Where `forge` says "do not commit", follow the commit choice from step 1 instead.

## 1. Start

1. Collect the input the same way `spark` does (chat text, files, images, ticket links).
2. If `docs/features/<feature>/` already has artifacts, resume instead of starting over.
   - **Changed input first.** If the input brings a requirement or design that differs from task.md or
     design.md (new behavior, a new design link or images, "change X"), it is a change request: run
     spark's Updating flow for requirement changes, mold's Updating flow for design changes, then
     slice's Updating flow if subtasks exist, then blueprint's Updating flow for each affected plan.
   - **Then the first unfinished artifact**: task.md not Confirmed → spark; design.md not Confirmed, or
     a design in the input and no design.md → mold; subtasks not written → slice; then the first
     subtask by `NN` that is not `Done`: an Approved or In progress plan → forge, otherwise → blueprint.
     A plan with `Manual verification: pending` has all its code done: skip it, carry on with the next
     subtask, and list it in the final report.
3. Ask, in one round (skip any question the user's request already answers):
   - **Mode**
     - **Auto (recommended)** — follow the agent's recommended option at each decision and ask only
       when needed (see "When auto mode still asks").
     - **Interactive** — ask the questions and approvals of spark, mold, slice, and
       blueprint as each skill describes.
   - **Commit after each subtask?** — Yes, using the commit style in CLAUDE.md (recommended when the
     feature is split into subtasks) / No, leave everything uncommitted for review.
4. If the user chose to commit and the current branch is the default branch (`main`, `master`, `develop`,
   or the remote's HEAD), create a feature branch first, named by CLAUDE.md's branch convention or
   `feature/<feature>`, and tell the user. Never commit to the default branch.

## 2. Run the stages

1. **spark** → `task.md`.
2. **mold** → `design.md`, only if the input has a design or flow (Figma link, screenshots, draw.io).
   With no design, skip it; never sketch one.
3. **slice**, only if the task meets slice's "When to use". Otherwise go straight to step 4 with
   task.md.
4. For each subtask in order (or once for task.md):
   1. **blueprint** → the plan.
   2. **forge** → code and unit tests.
   3. If forge left the plan `In progress` (tests failing, a Traceability gap), stop: show its report and
      do not commit or start the next subtask, in either mode. If it is `In progress` only with
      `Manual verification: pending`, the code is done: commit if the user chose it, then continue with the
      next subtask (in Auto mode without asking; in Interactive mode forge has already asked). Otherwise
      (`Done`) commit if the user chose it, then continue.

Both modes stop at the same hard stops of `forge`: a large deviation from the plan, or the same
compile error or test failure after 3 attempts.

### Keeping the context small

Every artifact lives on disk, so a stage never needs this conversation's history to run.
- **Auto mode**: run each subtask's blueprint + forge in its own subagent. Give it the subtask path, the
  mode, the "When auto mode still asks" list, and the instruction to invoke `blueprint` then `forge` with
  the Skill tool and not to commit. It returns forge's report, or the question it stopped on. Ask that
  question here and start a new subagent with the answer; it records it where the stage keeps decisions
  (the plan's `## Decisions`, or `## Deviations` for forge), and blueprint and forge resume from the files. Run subagents one at a time: subtasks build on each other. Commit here,
  after checking the plan's Status.
- **Interactive mode**: stages stay in this conversation, since they ask the user directly. After every
  two subtasks, if more remain, offer to continue in a fresh session; foundry resumes from the files.

## 3. Interactive mode

Run each stage skill exactly as written, including every question round, summary confirmation, outline
preview, and approval. Between subtasks, show the subtask's report and wait for "continue".

## 4. Auto mode

Run each stage skill, with these overrides:

- **Questions** — do not ask. Take the option you would have marked as recommended, and record it in
  the artifact where the skill keeps decisions, marked `(auto)` with a one-line reason:
  - spark: task.md, as normal content plus a line under `## Open questions` →
    `- [x] <question> → <choice> (auto: <reason>)`.
  - mold: design.md `## Open questions` → `- [x] <question> → <choice> (auto: <reason>)`. Drawn or
    proposed Navigation rows are accepted as they are and listed for review. Requirements the design
    reveals are added to task.md through spark's Updating flow, marked `(auto)`.
  - slice: keep the split as proposed unless a subtask is S and trivial, then merge it into a
    neighbour.
  - blueprint: `## Decisions` → `- <Decision> (auto) — <reason>; rejected: <alternative>`.
- **Summaries, previews, approvals** — do not wait. Set `Status: Confirmed` / `Approved` yourself and
  move on. Do not skip writing the summaries into the files.
- **Between subtasks** — continue without waiting; post a one-line progress note.

### When auto mode still asks

Stop and ask (one round, recommended option first) only when guessing would be costly or the input can't
answer it:

- The goal or main user flow can't be inferred from the input and code.
- The inputs contradict each other (ticket vs design vs existing behavior), or the feature conflicts
  with existing behavior that the input doesn't say to change.
- A choice is hard to reverse or affects other features: database schema change or migration, new
  library, new module, change to a shared module's public API, removing or changing existing behavior.
  Adding, changing, or removing any public member (method, property, parameter, type) of a class or
  interface in a shared module counts, even when it only adds a method to an existing repository.
- The design can't be read: a Figma link with no Figma MCP and no `$FIGMA_TOKEN`.
- Anything the stage skills treat as a hard stop.

After the answer, carry on in auto mode.

## 5. Finish

Report to the user:
- Artifacts written: task.md, design.md, subtasks, plans (paths).
- Per subtask: status, files changed by module, commit hash if committed.
- **Auto decisions to review**: a section with exactly this heading. List every `(auto)` decision across
  task.md, design.md, and plans, one per line, keeping the `(auto)` tag and linking the file that holds
  it, so the user can review what was chosen for them in one place.
- **Awaiting manual verification**: a section with exactly this heading. List every plan with
  `Manual verification: pending`, including plans skipped because an earlier run left them so, each with
  its AC/EC and the "How to test" steps written out (a pointer to the file is not enough). Tell the user
  to run them and mark each plan `Done` (or run `forge` on it again to be asked). Don't replace these two
  sections with a general "to check on a device" note.
- What was not verified: the `forge` report's list (UI, instrumented, screenshot tests).
- If nothing was committed, ask whether to commit.

---
name: slice
description: Split a large task.md into ordered, reviewable vertical-slice subtasks under docs/features/<feature>/subtasks/. Use when asked to break down a feature, or when it spans several screens or layers or is too big for one reviewable diff; skip it when the task fits one implement plan.
---

# Slice

Goal: a sequence of subtasks where each one is small enough to review, complete enough to implement
without guessing, and testable as a real flow in the running app.

This skill only writes docs: do not run build, test, lint, or format commands, even if CLAUDE.md lists
checks to run before finishing.

Do not re-ask anything answered in the linked task.md / subtask / plan.

## When to use

Use when the task touches several screens or layers, or would produce more than one reviewable diff
(~400 lines of production code or more than 3 modules). Otherwise tell the user to go straight to
`blueprint` with task.md, and stop.

## Slicing rules

- **Vertical, not horizontal.** Each subtask cuts through every layer it needs (UI -> state -> data -> source)
  so a user flow works at the end. Never "subtask 1: all data layer, subtask 2: all UI".
- **Happy path first.** Subtask 1 makes the main flow work end to end with real data, minimal states.
  Example for "news list": 1) screen + load from API + show items; 2) loading, pull-to-refresh, error and
  retry; 3) offline cache, empty state, edge cases.
- **Then robustness, in this order** (merge or skip what doesn't apply): loading / refresh / errors ->
  caching / offline / sync -> edge cases (empty, long content, interruption, process death) -> polish
  (analytics, accessibility, animations).
- **Each subtask leaves the app shippable**: builds, existing tests pass, no half-visible feature without a
  guard (hide behind a flag or keep the entry point out until the flow works).
- **Size**: about ≤400 lines of production code and ≤3 modules. Split further if bigger; merge if trivial.
- **Coverage**: every `AC-n` and `EC-n` from task.md lands in exactly one subtask (or is partially covered
  in one and completed in a later one, stated explicitly). Nothing new is invented, and nothing is
  dropped: moving an AC/EC out of this feature is a requirement change, made in task.md through `spark`,
  not by leaving it out of the subtasks.

## Process

If `docs/features/<feature>/subtasks/` already has files, go to **Updating** below.

1. **Read** task.md (status should be Confirmed; if Draft, warn the user), CLAUDE.md, and skim the
   areas the feature touches — only to judge size and layers, not to design. If `design.md` exists, read
   it (not the screen files): its screens, states, and Navigation help size the slices. Slices still
   follow user flows, not one subtask per screen.
2. **Draft the split**: subtasks, the ACs/ECs each covers, layers touched, dependencies.
3. **Show the outline in chat for preview, and stop.** Write it as plain chat text: short, just enough to
   judge the split, no files yet. Do not ask a question with a question tool in this turn; a question dialog
   can cover the outline before the user has read it.

   | # | Subtask | Goal (one line) | Covers | Layers | Depends on | Size |

   - Size is S / M / L against the ≤400-line limit.
   - Below the table, list any AC/EC that is split across subtasks, and check that every AC/EC in
     task.md appears in the table.
   - Then list the candidate merges as plain text, so the user can weigh them while reading. A candidate is
     two adjacent subtasks where the later one depends only on the earlier one. Write each as, for example,
     "01 + 02 (≈ M, 4 modules)". Mark a merge "(over the size limit)" if it would exceed ~400 lines or 3
     modules.
   - End with one line asking the user to reply when they have looked: "ok" to continue, or a grouping or
     correction in their own words.
4. **After the user replies, settle scope and grouping.** If the reply already gives a grouping or a change,
   apply it and skip the matching question. Otherwise ask, in one round:
   - Scope questions, only if something is unclear. Typical:
     - A slice is too big — which part ships first?
     - An AC could live in two subtasks — which?
     - Something isn't needed for a first release — put it in the last subtask, or take it out of the
       feature? Taking it out means stopping here and updating task.md through `spark` (moved to Out of
       scope), then slicing the updated task.md.
   - The grouping question, always, even when nothing else is unclear. The user decides how many reviews
     and commits the feature takes.
     - Use one multi-select question with the candidate merges from step 3, including their combined size
       and the "(over the size limit)" mark.
     - Add a "Keep the split as proposed" option (recommended unless a subtask is S and trivial). The user
       can also type any other grouping, such as "01–03 together".
   - Apply the answer:
     - Renumber the subtasks.
     - Combine their Covers, Layers, and How to test.
     - Keep Depends on correct.
     - Show the updated outline again.
   - The user's choice overrides the size rule. Note the size risk in the outline instead of re-asking.
5. **Iterate** on the outline (merge, split, reorder, move ACs) until the user approves it.
6. **Write** one file per approved subtask: `docs/features/<feature>/subtasks/NN-<slug>.md`
   (NN = 01, 02, ...), matching the outline exactly. Ask the user to review the files.
7. **Finish**: add a `## Subtasks` section with links at the end of task.md, then suggest running
   `blueprint` on subtask 01. Do not run it yourself.

## Subtask file template

```markdown
# NN - <Subtask title>

Feature: [task.md](../task.md)
Depends on: <none | NN-...>
Design: <none | [<screen>](../screens/<screen>.md), ... (with the states this subtask covers)>
Status: Todo | Planned | In progress | Done

## Goal
<What works after this subtask, from the user's point of view, in 1–3 sentences.>

## Scope
### In scope
- ...
### Out of scope (handled later)
- <item> -> NN-<slug>

## Acceptance criteria
- **AC-1** <copied from task.md, Given/When/Then; mark "(partial: ...)" if only partly covered>

## Edge cases
- **EC-2** ...

## Layers touched
- <e.g. UI, state holder, repository, network> (no class or file names)

## How to test
1. <Manual steps in the running app that exercise this flow, with expected results.>
```

Keep AC/EC IDs identical to task.md so plans, code reviews, and tests can trace back to the requirement.

New subtasks start as `Todo`. `blueprint` sets `Planned` when their plan is approved; `forge`
sets `In progress` when it starts and `Done` when it finishes.

## Updating

When task.md or design.md changed after the subtasks were written:
1. Read task.md (its Change log shows what changed), design.md if it exists, and every subtask with its
   Status.
2. Find the affected subtasks through the AC/EC IDs and design screens the change touches.
3. Draft the changes under these rules:
   - `Done` and `In progress` subtasks are never rewritten. A change to their scope becomes a new
     subtask.
   - `Todo` subtasks may be edited, split, merged, or removed.
   - A `Planned` subtask that changes goes back to `Todo`, and its plan is listed for `blueprint`
     Updating.
   - Never renumber. New subtasks take the next free `NN` and declare `Depends on` as needed.
   - Every AC/EC in task.md is still covered by exactly one subtask (or split, stated explicitly), and
     removed ones (`~~AC-n~~`) are covered by none.
4. Show the changes in chat as in step 3 (added / changed / removed, with IDs and the subtasks
   affected), and wait for approval. Removing a subtask file needs that approval.
5. Apply them, update task.md's `## Subtasks` links, and list the plans in `implement-plans/` that need
   `blueprint` Updating. Do not edit plans yourself.

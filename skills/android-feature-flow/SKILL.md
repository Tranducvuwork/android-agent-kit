---
name: android-feature-flow
description: Run an Android feature end to end — capture the screens, clarify the requirement, plan it, implement it, review the diff, then write and run the tests and the policy audit. Chains android-screen-capture, spark, mold, slice, blueprint, forge, android-change-review, android-automation-testing-setup and android-app-policy-test. Use when the user wants a feature taken from idea or screenshot all the way to tested code in one go.
---

# Android Feature Flow

Goal: one request takes a feature from "here is the screen" to "code written, reviewed, tested, audited",
without the user re-explaining anything between stages.

```
                 once per repo
scout → rulebook ─────────────────────────────────────────────────────┐
                                                                      │
android-screen-capture → spark → [mold] → [slice] → blueprint → forge ┤
         (capture)      (what)  (design)  (split)   (plan)   (code)   │
                                                                      │
      → android-change-review → android-automation-testing-setup      │
              (review)                  (tests)                       │
      → android-app-policy-test ───────────────────────────────────────┘
              (policy audit)
```

This skill decides the **order**, the **mode**, and what happens **between** stages. Each stage is run by
invoking its own skill with the Skill tool; never re-implement a stage here, and never skip its checks,
templates, or file outputs.

`foundry` covers spark → forge on its own. This skill is the wider arc: it adds the capture stage before,
and the review, test and audit stages after. When a feature needs only spark → forge, call `foundry`
instead and stop.

## 1. Start

1. **Check the repo is onboarded.** If there is no `CLAUDE.md` / `AGENTS.md` at the root, run `scout`
   first, then `rulebook`. A repo already onboarded skips both; say so in one line and move on.
2. **Collect the input**: chat text, files, images, ticket links, and whether a device is attached.
3. **Resume rather than restart.** If `docs/features/<feature>/` already holds artifacts, pick up at the
   first unfinished one, exactly as `foundry` does: changed input first (spark / mold update flows), then
   `screens.md` → `task.md` → `design.md` → subtasks → plans → code.
4. **Ask once, in one round** (skip what the request already answers):
   - **Capture** — will the user open screens on a device now (`android-screen-capture`), is there a
     separate design (`mold`), both, or neither?
   - **Mode** — **Auto** (follow the recommended option at each decision, ask only when guessing would be
     costly) or **Interactive** (every stage asks as its own skill describes).
   - **Commit after each subtask?** — yes, using the repo's commit style, or no, leave it for review.
   - **After the code** — which of review / tests / policy audit to run. Default: all three.
5. If committing and the branch is the default branch (`main`, `master`, `develop`, or the remote's HEAD),
   create `feature/<feature>` first and say so. Never commit to the default branch.

## 2. Capture (optional)

Run `android-screen-capture`. It writes `docs/features/<feature>/screens/` and `screens.md`.

The user drives the app; you only record. Do not start capturing before the user confirms each screen is
on screen, and read every PNG before accepting it.

Pass `screens.md` to `spark` as input. When a separate design also exists (Figma, mockups), `mold` runs
after `spark` as usual and treats `screens.md` as **current behavior**, not as the target design —
where the two disagree, that difference is a requirement, and it goes into `task.md`, not into `design.md`.

## 3. Specify and plan

1. **spark** → `task.md`. Feed it `screens.md` when it exists.
2. **mold** → `design.md` + `screens/<screen>.md`, only when a design or flow exists. With no design, skip
   it; never sketch one.
3. **slice** → ordered subtasks, only when the task meets slice's "When to use".
4. For each subtask in order (or once for `task.md`): **blueprint** → the plan.

### Plan review gate

A plan is reviewed before any code is written. Offer the user, once, two ways to do it:

- **Review here** — walk the plan against `task.md` and `screens.md` yourself: every AC/EC mapped to a
  step, every step buildable, no decision left open, no file invented.
- **Review in another agent** (Codex, Gemini CLI, Cursor) — the plan is a file on disk, so hand over the
  path and let them read it. Stop and wait for the user to bring back the verdict.

Either way, nothing proceeds to `forge` until the plan's `Status` is `Approved`. Record the review's
findings in the plan's `## Decisions` before approving.

## 4. Implement

**forge** → production code and unit tests, compiling after each step.

Hard stops, in both modes: a large deviation from the plan, or the same compile error or test failure
after 3 attempts. On a hard stop, show forge's report and do not commit or start the next subtask.

If the user chose to commit, commit after each subtask whose plan reached `Done`, or `In progress` with
only `Manual verification: pending`.

### Keeping the context small

Every artifact is on disk, so a stage never needs this conversation's history.
In Auto mode, run each subtask's blueprint + forge in its own subagent, one at a time, giving it the
subtask path and the mode; it returns forge's report or the one question it stopped on. Commit here,
after checking the plan's `Status`.

## 5. Review the diff

**android-change-review** over the changes this flow produced
(`git diff --cached`, or `git diff <base>...HEAD` when commits were made).

Findings are triaged, not auto-applied:
- **Crash, lifecycle and regression risks** → fix now, through the plan (add a step, note it under
  `## Deviations`), then re-run forge's checks.
- **Style and preference** → list them, change nothing.

Say which files the review skipped if the diff was large enough to triage.

## 6. Test

**android-automation-testing-setup**, `TEST` mode, scoped to the modules this feature touched.

It writes and runs the automation, collects evidence, and produces
`autotesting-reports/<run-id>/report.md` plus the v2 coverage artifact. Its rules hold here without
exception, and this flow does not soften them:

- It changes test code and minimal test configuration only — never production source, resources, the
  manifest, DI, or release settings. If a test needs a production change, the case is `BLOCKED`; bring it
  back to `blueprint` as a new step rather than editing production from the test stage.
- A case that was not actually run is `NOT_TESTED` or `BLOCKED`, never `PASS`. Reading the source is not
  a run. Report the four statuses exactly as the skill computes them.

The first full TEST run on a feature becomes its baseline; later runs are `RETEST` against it.

## 7. Policy audit

**android-app-policy-test** over the feature's source, writing `qa-reports/`.

Run it when the feature touches anything the checklist covers — permissions, billing, ads, SDK or target
SDK, data collection, ProGuard/release config, strings. For a change that touches none of these, say why
you skipped it instead of running it for form.

## 8. Finish

Report, in this order:

- **Artifacts**: `screens.md`, `task.md`, `design.md`, subtasks, plans — with paths.
- **Code**: per subtask, status, files changed by module, commit hash if committed.
- **Auto decisions to review**: a section with exactly this heading, listing every `(auto)` decision across
  task.md, design.md and the plans, each linking the file that holds it.
- **Awaiting manual verification**: a section with exactly this heading, listing every plan with
  `Manual verification: pending`, with its AC/EC and the "How to test" steps written out in full.
- **Review**: the counts by severity, what was fixed, what was listed and left.
- **Tests**: the report path, the baseline path, and the case count per status
  (`PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED`).
- **Policy audit**: the report path and the failing rule ids, or why it was skipped.
- **Not verified**: UI, instrumented and screenshot tests that were not run, and anything the capture
  stage could not reach.

If nothing was committed, ask whether to commit.

## Honesty rules

These override any stage's own wording, and the Auto mode never relaxes them:

- A stage that did not run is reported as not run. Never infer a result from a stage's inputs.
- A test that did not execute is not a pass, and a build that did not run is not a green build.
- A plan the user has not approved is not approved, in either mode — Auto mode may approve its own
  *decisions*, never skip the user's plan review when the user asked for one.
- Every path reported must exist. Check before reporting it.

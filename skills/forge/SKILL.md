---
name: forge
description: Execute an approved implement plan in an Android project: write production code and unit tests step by step, compiling as it goes. Does not commit. Use when asked to implement a plan file.
---

# Forge

Goal: turn an approved plan into working code and unit tests, step by step, so that every step leaves the
project compiling, the unit tests pass at the end, and the final diff matches the plan.

Do not re-ask anything answered in the linked task.md / subtask / plan.

## Before starting

1. Read the plan (`docs/features/<feature>/implement-plan.md` or `implement-plans/NN-<slug>.md`) and the
   requirement it links to.
   - If `Status` is `Draft`, ask the user to confirm the plan first. If it is `Done`, say so and stop.
   - If no plan exists, suggest `blueprint` and stop.
   - **Resuming**: if `Status` is `In progress`, or any step is ticked (`✅`), continue the earlier run.
     Compile the modules of the ticked steps (main and unit test sources) to confirm they still build,
     then start at the first unticked step. If they don't build, report it before writing anything.
2. Read `CLAUDE.md` and the `.claude/rules/*.md` matching the modules in the plan's Changes overview.
   If the plan has a Design mapping, also read the screen files (`screens/<screen>.md`) it names, and
   open their screenshots only when the layout text isn't enough.
3. Check `git status`. If there are unrelated uncommitted changes, tell the user before touching anything.
4. Set the plan `Status: In progress` and, if the plan came from a subtask, the subtask's
   `Status: In progress`.

## For each unticked step, in order

1. **Read before writing.** Open the files to modify and the reference/reuse components the step names.
   Match the surrounding code: naming, structure, comment density, idioms.
2. **Write the code** for the step — only what the step describes. For UI from a design:
   - Copy text verbatim from the screen file's Copy section into the string resources the plan's Design
     mapping names (key, module, locales); reuse the shared strings it lists instead of adding new ones.
   - Handle each Variant the way the Design mapping says (theme attribute, qualified resource, or layout
     logic).
   - Add assets as the plan's Assets table says. Convert simple SVGs (paths, fills, strokes) to
     VectorDrawable XML; an SVG with gradients, masks, filters, or text gets a placeholder instead, noted
     as a deviation. `needs-export` assets get a placeholder.
3. **Write the unit tests** listed in the step, using the project's test doubles and rules (no new mocking
   library unless the project uses one).
4. **Compile** the modules the step touched, main and unit test sources, without running tests (e.g.
   `./gradlew :<module>:compile<Variant>Kotlin :<module>:compile<Variant>UnitTestKotlin`; use the
   project's equivalent tasks if it differs). This catches errors before later steps build on them.
   If the step changed the public API of a shared module (`core:*`, `common`, or any module others depend
   on), also compile the modules that depend on it; find them by grepping build files for
   `project(":<module>")` or the matching type-safe accessor.
5. **Fix until it compiles.** Read the error and fix the cause; never suppress a compiler error without a
   reason. After 3 failed attempts on the same error, stop and report it with the output.
6. **Tick the step** in the plan (`### Step 1: ... ✅`) and move on.

Unit tests run once, in Finish. Run long Gradle commands in the background when they may exceed ~2 minutes.

Do **not** run UI tests, instrumented tests, or screenshot verification — they are too slow for this loop.
If a step changes UI that has screenshot tests, note in the final report that screenshots need to be
verified or re-recorded.

## Deviations from the plan

- **Small** (a renamed class, a missing import or dependency line, a different but equivalent existing
  helper, an extra private function): do it, and add a line to a `## Deviations` section at the end of the
  plan.
- **Large** (a component the plan relies on doesn't exist or doesn't fit, a new module or library, a schema
  change not planned, any change to behavior or acceptance criteria): **stop**, explain what you found and
  the options, and wait for the user. Update the plan with the decision before continuing.

## Guardrails

- Only change files the plan lists (plus build files, DI, and resources they need). No drive-by refactors.
- No speculative code: no unused parameters, abstractions, or TODO hooks "for later".
- Follow every "Do not" in CLAUDE.md (generated files, baselines, design system, dependency direction).
- New source files get the project's license header / formatting.

## Finish

1. Run the **default tier** of CLAUDE.md's "Before finishing a code change" over every touched module,
   plus the dependent modules of any shared module whose public API changed (build, unit tests,
   auto-format, baselines if dependencies changed). Run the full tier (format check,
   lint, screenshot, instrumented) only if the user asks for it.
2. **Fix failing tests.** Use the plan's Traceability table to find the step behind each failure, fix the
   cause in code (never delete or weaken a test to pass), and re-run only the failing modules. After 3
   failed attempts on the same failure, stop and report it with the output.
3. If formatting changed files, re-run the touched modules' build and unit tests once.
4. Walk the plan's Traceability table: confirm each AC/EC has code and a verification this run executed
   and passed (a unit test, or a build / lint check the plan names for it). A manual "How to test" step
   or a check that was skipped does not count as verified.
5. Decide the status:
   - Every check in step 1 passed and every AC/EC is verified: set the plan `Status: Done` and, if the
     input was a subtask, its `Status: Done`.
   - A check failed, or an AC/EC has no code or no verification at all: leave both `In progress` and list
     each gap in the report.
   - Everything automated passed and the only AC/EC left are covered by manual "How to test" steps: leave
     both `In progress`, add the line `Manual verification: pending` under the plan's `Status`, and list
     those AC/EC with their steps. Then ask once, after all steps: "Have you run these steps? Mark Done?".
     On yes, set both `Done` and remove the line; on no, leave them as they are. When foundry's Auto mode
     invoked you, do not ask: leave the status, the line, and the list in the report.
6. Report to the user:
   - Steps done, files changed (grouped by module), deviations.
   - Commands run and their results, stated honestly (pass / fail with output).
   - What was not verified: UI / instrumented / screenshot tests, manual "How to test" steps.
   - Placeholder assets still waiting for a real file, if any.
   - Do not commit. Ask whether to commit once they have reviewed, using the commit style in CLAUDE.md
     (or the style of recent `git log` if CLAUDE.md doesn't state one).

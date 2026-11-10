---
name: rulebook
description: Generate path-scoped rule files in .claude/rules/ for an Android project, one per architectural layer. Use after onboarding (CLAUDE.md exists), or when asked to generate, refresh, or add rules for layers or modules.
---

# Rulebook

Goal: when Claude edits a file, the matching rule loads and tells it how that layer is written in *this*
project — what it owns, what it may depend on, which file to copy, the steps to add something new, and the
mistakes to avoid. CLAUDE.md stays global and short; layer detail lives here.

## Rule file format

Each rule is `.claude/rules/<layer>.md` with path-scoped frontmatter:

```markdown
---
paths:
  - "core/data/**"
  - "feature/*/data/**"
---

# <Layer name>

## Responsibility
- What this layer owns and what it must not do. Allowed and forbidden dependencies.

## Pattern
- How a typical class is written here, in a few bullets or a short skeleton.
- Reference: `path/to/RealFile.kt` (what to copy from it).

## Adding a new <thing>
1. Ordered steps across files (e.g. entity -> DAO -> database version + migration -> mapper -> test).

## Do / Don't
- Do X. / Don't Y — do Z instead.

## Testing
- How this layer is tested: doubles used, rules, naming, reference test file.
```

Keep each rule 30–80 lines. Every claim must be backed by a file you read; every reference path must exist.

## Process

1. **Prerequisites.** Read `CLAUDE.md` (if missing, suggest `scout` first and stop) and any
   existing `.claude/rules/`. Existing rules are hypotheses to verify, not to discard.

2. **Map modules to layers.** List modules from `settings.gradle(.kts)`; classify each by its build plugins,
   dependencies, and contents. Group into layers; derive path globs per layer (module globs for modular
   projects, package globs like `**/data/**` for single-module projects). A module may appear in several
   layers only when it truly mixes them.

3. **Propose and confirm.** Show a table to the user before reading deeply:

   | Rule file | Layer | Path globs | Modules covered | Reference files |

   Also list modules left uncovered and why, and for existing rules: keep / update / merge / delete.
   Ask questions only where code is ambiguous (two competing patterns, legacy vs target). Wait for approval.

4. **Research each layer.** For each approved layer, read 2–3 representative files end to end plus their tests.
   For several layers, dispatch parallel read-only subagents, one per layer, each returning findings with
   file-path evidence for the five sections above.

5. **Draft and review.** Write drafts, then self-check each one:
   - Globs match the intended files and nothing unintended: `git ls-files ':(glob)<glob>'`. The
     `:(glob)` prefix is required; without it git lets `*` match `/`, so `feature/*/data/**` would also
     match `feature/a/b/data/...` and the check would pass on files the rule won't actually cover.
   - Every referenced path exists.
   - No duplication of CLAUDE.md content; no contradiction with it or between rules.
   - Nothing generic that holds for every Android project — only this project's choices.
   Show the user a summary (file, globs, line count, key rules) and the full text on request.

6. **Write** only after approval. Report files written, updated, deleted, and modules still uncovered.
   If CLAUDE.md lacks a pointer to `.claude/rules/`, propose adding one line.

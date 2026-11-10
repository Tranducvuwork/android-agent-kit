# Repository Guidelines

This repository is a **skill kit**, not an application. It holds agent instructions for Android work and
the scripts that install and validate them. There is no app to build here.

## Project structure

| Path | What it holds |
|---|---|
| `skills/<name>/SKILL.md` | the skill itself — the only file an agent loads first |
| `skills/<name>/references/` | long material the SKILL.md links to, read on demand |
| `skills/<name>/assets/templates/` | document templates a skill writes from |
| `skills/<name>/scripts/` | executable helpers the skill calls |
| `skills/<name>/agents/openai.yaml` | the Codex descriptor (display name, prompt, invocation policy) |
| `scripts/install-skills.py` | installs skills into an Android project, for five agents |
| `scripts/validate-skills.py` | checks every package before install or publish |
| `scripts/prepare-skill.py` | syncs `docs/` sources into the packaged skills |
| `docs/dev-checklist.md`, `docs/testing-setup/` | **sources** for the QA skills — edit here, not in `skills/` |

## Commands

```bash
python3 -I scripts/validate-skills.py          # every skill
python3 -I scripts/validate-skills.py --skill blueprint
python3 -I scripts/prepare-skill.py --check    # packaged docs match their sources
python3 -I scripts/install-skills.py <project> --dry-run
```

Run Python with `-I` so nothing is imported from the working directory. Python 3.9+.

Both checks run in CI (`.github/workflows/validate-skills.yml`) and must pass before merge.

## Writing a skill

- `SKILL.md` opens with YAML frontmatter holding exactly `name` and `description`. `name` is
  lowercase-kebab-case and **equal to the directory name**; the validator enforces this.
- `description` is one paragraph: what the skill does, then *when to use it*. The agent picks a skill from
  this line alone, so name the trigger ("Use when the user asks to…"), in English and, where the team works
  in Vietnamese, with the Vietnamese trigger words too.
- Keep `SKILL.md` to roughly 150–250 lines. Anything longer goes to `references/` behind a link.
- Write the process as numbered steps with observable outputs. Say what the skill writes and where.
- State what the skill must **not** do. Most failures here are a skill quietly editing production code or
  reporting a step it never ran.
- Links inside ``` fences are treated as templates and are not resolved; links in prose must resolve to a
  file in the package.
- A skill that calls a script refers to it as `$SKILL_DIR/scripts/<file>`. The installer rewrites that for
  the agents that have no `$SKILL_DIR`.

## Writing a script

- Shell scripts target bash on macOS (bash 3.2) as well as Linux: no `mapfile`, no associative arrays.
- `adb devices` separates serial from state with a **tab**, and wireless serials contain spaces. Split on
  tab, and quote every serial.
- Under `set -euo pipefail`, a `grep` that matches nothing kills the script. End best-effort probes with
  `|| true`.
- Never inline shell variables into a heredoc of another language; pass them through the environment.
- Python scripts take `--dry-run` where they write, and print what they changed.

## Reporting rules

These apply to every skill in the kit and to changes made to it:

- A step that did not run is reported as not run. A test that did not execute is not a pass.
- Every path reported must exist; check before naming it.
- Screenshots and dumps are real user data. Check them for credentials and personal data before committing.

## Commits

Concise imperative subjects (`Add android-screen-capture skill`). Keep a pull request to one skill or one
script where possible, and say in the description which skills you validated and how.

## Third-party content

`skills/` holds material from four upstream repositories, two of them without a license. Read
[ATTRIBUTION.md](ATTRIBUTION.md) before adding, editing, or publishing any of it, and update the commit
hash there whenever you pull a newer upstream version.

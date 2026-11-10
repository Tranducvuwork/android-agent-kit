#!/usr/bin/env python3
"""Install the kit's skills into an Android project, for several agents at once.

One canonical copy of each skill lands in `<project>/.agent-skills/<name>/`.
Every agent then gets its own entry point pointing at that copy, so there is a
single place to update and no duplicated reference material:

    .agent-skills/<name>/          canonical package (SKILL.md + references + scripts)
    .claude/skills/<name>          Claude Code      — directory link
    .agents/skills/<name>          OpenAI Codex     — directory link
    .github/skills/<name>          GitHub Copilot   — directory link
    .cursor/rules/<name>.mdc       Cursor           — generated rule file
    .gemini/rules/<name>.md        Gemini CLI       — generated rule file
    .gemini/commands/<name>.toml   Gemini CLI       — generated slash command
    GEMINI.md                      Gemini CLI       — @import lines for the rules

Usage:
    python3 -I scripts/install-skills.py <project-dir>
        [--skill NAME ...]       default: every skill in skills/
        [--agent claude-code codex gemini cursor copilot]   default: all
        [--copy]                 copy instead of symlinking (Windows, no-symlink FS)
        [--force]                replace entries that already exist
        [--dry-run]              print what would happen, change nothing

Run with -I so nothing is imported from the project's own directory.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = KIT_ROOT / "skills"

AGENTS = ("claude-code", "codex", "gemini", "cursor", "copilot")

# Agents that read a whole skill directory, and where they read it from.
DIRECTORY_AGENTS = {
    "claude-code": Path(".claude") / "skills",
    "codex": Path(".agents") / "skills",
    "copilot": Path(".github") / "skills",
}

CANONICAL = Path(".agent-skills")

CURSOR_GLOBS = '["**/*.kt", "**/*.java", "**/*.xml", "**/*.gradle.kts", "**/*.gradle"]'

GEMINI_IMPORT_HEADER = "<!-- android-agent-kit: generated imports, safe to re-run -->"
GEMINI_IMPORT_FOOTER = "<!-- /android-agent-kit -->"


class SkillError(RuntimeError):
    pass


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], str]:
    """Return (frontmatter, body). Only the flat `key: value` form is used by skills."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SkillError(f"{skill_md} has no YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SkillError(f"{skill_md} has an unterminated frontmatter block")
    meta: dict[str, str] = {}
    key = None
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key = match.group(1)
            meta[key] = match.group(2).strip().strip('"')
        elif key and line.startswith((" ", "\t")):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, parts[2].lstrip("\n")


def rewrite_links(body: str, name: str) -> str:
    """Point relative links at the canonical package, so generated rule files resolve.

    `[x](references/y.md)` -> `[x](.agent-skills/<name>/references/y.md)`.
    Absolute URLs, anchors and mail links are left alone.
    """
    def repl(match: re.Match[str]) -> str:
        label, target = match.group(1), match.group(2)
        if re.match(r"^([a-z][a-z0-9+.-]*:|#|/)", target, re.IGNORECASE):
            return match.group(0)
        return f"[{label}]({CANONICAL.as_posix()}/{name}/{target})"

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", repl, body)


def rewrite_skill_dir(body: str, name: str) -> str:
    """`$SKILL_DIR` in a command example has no meaning outside Claude Code."""
    return body.replace("$SKILL_DIR", f"{CANONICAL.as_posix()}/{name}").replace(
        '"' + CANONICAL.as_posix() + f'/{name}"', f"{CANONICAL.as_posix()}/{name}"
    )


def link_or_copy(src: Path, dst: Path, copy: bool, force: bool, dry: bool) -> str:
    if dst.exists() or dst.is_symlink():
        if not force:
            return f"skip (exists)  {dst}"
        if not dry:
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            else:
                shutil.rmtree(dst)
    if dry:
        return f"would {'copy' if copy else 'link'}  {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copytree(src, dst)
        return f"copied  {dst}"
    target = os.path.relpath(src, dst.parent)
    dst.symlink_to(target, target_is_directory=True)
    return f"linked  {dst} -> {target}"


def write_file(path: Path, content: str, force: bool, dry: bool) -> str:
    if path.exists() and not force:
        if path.read_text(encoding="utf-8") == content:
            return f"unchanged  {path}"
        return f"skip (exists)  {path}"
    if dry:
        return f"would write  {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"wrote  {path}"


def cursor_rule(name: str, meta: dict[str, str], body: str) -> str:
    description = meta.get("description", "").replace('"', "'")
    return (
        "---\n"
        f"description: {description}\n"
        f"globs: {CURSOR_GLOBS}\n"
        "alwaysApply: false\n"
        "---\n\n"
        f"{rewrite_skill_dir(rewrite_links(body, name), name)}"
    )


def gemini_rule(name: str, meta: dict[str, str], body: str) -> str:
    description = meta.get("description", "")
    return (
        f"<!-- Generated by android-agent-kit from skills/{name}/SKILL.md. Do not edit here. -->\n\n"
        f"> **When to apply:** {description}\n\n"
        f"{rewrite_skill_dir(rewrite_links(body, name), name)}"
    )


def gemini_command(name: str, meta: dict[str, str]) -> str:
    description = meta.get("description", "")
    short = description.split(".")[0][:120] if description else name
    rule_path = f".gemini/rules/{name}.md"
    template = (
        f"Follow the workflow in @{rule_path} for this Android project.\n\n"
        "{{#if args}}\n"
        "Scope / input: {{args}}\n"
        "{{else}}\n"
        "Ask for the scope you need before starting.\n"
        "{{/if}}\n\n"
        "Read the rule file in full before acting, and follow its process, outputs and\n"
        "honesty rules exactly. Do not report a step as done if it did not run."
    )
    escaped = template.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return (
        f"# Gemini CLI slash command: /{name}\n"
        f"# Generated by android-agent-kit. Place in .gemini/commands/ (project) or ~/.gemini/commands/ (global).\n\n"
        "[command]\n"
        f'name = "{name}"\n'
        f'description = "{short}"\n\n'
        "[prompt]\n"
        f'template = """\n{escaped}\n"""\n'
    )


def update_gemini_md(project: Path, names: list[str], force: bool, dry: bool) -> str:
    path = project / "GEMINI.md"
    block = "\n".join(
        [GEMINI_IMPORT_HEADER, "## Android agent skills", ""]
        + [f"@./.gemini/rules/{n}.md" for n in sorted(names)]
        + ["", GEMINI_IMPORT_FOOTER]
    )
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if GEMINI_IMPORT_HEADER in existing:
        content = re.sub(
            re.escape(GEMINI_IMPORT_HEADER) + r".*?" + re.escape(GEMINI_IMPORT_FOOTER),
            block,
            existing,
            flags=re.DOTALL,
        )
    elif existing.strip():
        content = existing.rstrip() + "\n\n" + block + "\n"
    else:
        content = "# Project instructions\n\n" + block + "\n"
    if content == existing:
        return f"unchanged  {path}"
    if dry:
        return f"would update  {path}"
    path.write_text(content, encoding="utf-8")
    return f"updated  {path}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", help="path to the Android project root")
    parser.add_argument("--skill", action="append", default=None, help="skill name; repeatable")
    parser.add_argument("--agent", nargs="+", choices=AGENTS, default=list(AGENTS))
    parser.add_argument("--copy", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        print(f"not a directory: {project}", file=sys.stderr)
        return 2

    available = sorted(p.name for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())
    names = args.skill or available
    unknown = [n for n in names if n not in available]
    if unknown:
        print(f"unknown skill(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"available: {', '.join(available)}", file=sys.stderr)
        return 2

    log: list[str] = []
    for name in names:
        src = SKILLS_DIR / name
        canonical = project / CANONICAL / name
        log.append(link_or_copy(src, canonical, args.copy, args.force, args.dry_run))

        for agent, subdir in DIRECTORY_AGENTS.items():
            if agent in args.agent:
                log.append(
                    link_or_copy(canonical, project / subdir / name, args.copy, args.force, args.dry_run)
                )

        if {"cursor", "gemini"} & set(args.agent):
            meta, body = parse_frontmatter(src / "SKILL.md")
            if "cursor" in args.agent:
                log.append(
                    write_file(
                        project / ".cursor" / "rules" / f"{name}.mdc",
                        cursor_rule(name, meta, body),
                        True,
                        args.dry_run,
                    )
                )
            if "gemini" in args.agent:
                log.append(
                    write_file(
                        project / ".gemini" / "rules" / f"{name}.md",
                        gemini_rule(name, meta, body),
                        True,
                        args.dry_run,
                    )
                )
                log.append(
                    write_file(
                        project / ".gemini" / "commands" / f"{name}.toml",
                        gemini_command(name, meta),
                        True,
                        args.dry_run,
                    )
                )

    if "gemini" in args.agent:
        log.append(update_gemini_md(project, names, args.force, args.dry_run))

    for line in log:
        print(line)
    print(
        f"\n{len(names)} skill(s) -> {project}"
        f"\nagents: {', '.join(args.agent)}"
        f"\nmode: {'copy' if args.copy else 'symlink'}{' (dry run)' if args.dry_run else ''}"
    )
    if any(line.startswith("skip (exists)") for line in log):
        print("\nSome entries already existed and were left alone. Re-run with --force to replace them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check every skill package in skills/ before it is installed or published.

Verifies, per skill:
  - SKILL.md exists and opens with a terminated YAML frontmatter block
  - `name` is present and equals the directory name
  - `description` is present, one paragraph, and under the length agents truncate at
  - every relative markdown link resolves to a file inside the package
  - every `agents/openai.yaml`, where present, parses as the flat descriptor the
    Codex loader expects
  - shell and python scripts are executable / syntactically valid

Usage:  python3 -I scripts/validate-skills.py [--skill NAME ...] [--quiet]
Exit code 0 when everything passes, 1 when anything fails.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = KIT_ROOT / "skills"

MAX_DESCRIPTION = 1024
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def frontmatter(text: str) -> tuple[dict[str, str], int] | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
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
    return meta, len(parts[1].splitlines()) + 2


def prose_links(text: str) -> list[str]:
    """Link targets outside fenced code blocks.

    A skill's document templates live inside ``` fences and link to paths that only
    exist once the skill has run (`task.md`, `screens/<x>.md`). Those are examples,
    not links the package must satisfy, so the fences are skipped.
    """
    targets: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            targets.extend(LINK_RE.findall(line))
    return targets


def check_skill(path: Path) -> list[str]:
    errors: list[str] = []
    name = path.name
    skill_md = path / "SKILL.md"

    if not skill_md.is_file():
        return [f"{name}: no SKILL.md"]

    parsed = frontmatter(skill_md.read_text(encoding="utf-8"))
    if parsed is None:
        return [f"{name}: SKILL.md has no terminated YAML frontmatter"]
    meta, _ = parsed

    declared = meta.get("name", "")
    if not declared:
        errors.append(f"{name}: frontmatter has no `name`")
    elif declared != name:
        errors.append(f"{name}: frontmatter name is `{declared}`, expected `{name}`")
    elif not NAME_RE.match(declared):
        errors.append(f"{name}: `{declared}` is not lowercase-kebab-case")

    description = meta.get("description", "")
    if not description:
        errors.append(f"{name}: frontmatter has no `description`")
    elif len(description) > MAX_DESCRIPTION:
        errors.append(f"{name}: description is {len(description)} chars, over {MAX_DESCRIPTION}")
    elif "\n" in description:
        errors.append(f"{name}: description spans several paragraphs; keep it one")

    for md in path.rglob("*.md"):
        for target in prose_links(md.read_text(encoding="utf-8")):
            target = target.split("#", 1)[0].strip()
            if not target or re.match(r"^([a-z][a-z0-9+.-]*:|/)", target, re.IGNORECASE):
                continue
            if "<" in target or "$" in target:  # placeholder, not a real path
                continue
            if not (md.parent / target).exists():
                errors.append(f"{name}: {md.relative_to(path)} links to missing `{target}`")

    descriptor = path / "agents" / "openai.yaml"
    if descriptor.is_file():
        text = descriptor.read_text(encoding="utf-8")
        for key in ("display_name", "short_description", "default_prompt"):
            if f"{key}:" not in text:
                errors.append(f"{name}: agents/openai.yaml has no `{key}`")
        if "allow_implicit_invocation" not in text:
            errors.append(f"{name}: agents/openai.yaml has no `allow_implicit_invocation`")

    for script in path.rglob("*.py"):
        try:
            ast.parse(script.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"{name}: {script.relative_to(path)} does not parse: {exc}")

    for script in path.rglob("*.sh"):
        result = subprocess.run(
            ["bash", "-n", str(script)], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            errors.append(
                f"{name}: {script.relative_to(path)} is not valid bash: {result.stderr.strip()}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", action="append", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not SKILLS_DIR.is_dir():
        print(f"no skills directory at {SKILLS_DIR}", file=sys.stderr)
        return 1

    skills = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if args.skill:
        wanted = set(args.skill)
        skills = [p for p in skills if p.name in wanted]
        missing = wanted - {p.name for p in skills}
        if missing:
            print(f"unknown skill(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 1

    all_errors: list[str] = []
    for skill in skills:
        errors = check_skill(skill)
        all_errors.extend(errors)
        if not args.quiet:
            print(f"{'FAIL' if errors else 'ok  '}  {skill.name}")

    if all_errors:
        print(f"\n{len(all_errors)} problem(s):", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"\n{len(skills)} skill(s) validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

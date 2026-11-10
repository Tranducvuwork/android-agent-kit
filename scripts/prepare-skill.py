#!/usr/bin/env python3
"""Sync maintained docs into the standalone Android skill packages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "android-app-policy-test"
CHECKLIST_SOURCE = REPOSITORY_ROOT / "docs" / "dev-checklist.md"
CHECKLIST_DESTINATION = SKILL_ROOT / "references" / "dev-checklist.md"
LEGACY_CHECKLIST_DESTINATION = SKILL_ROOT / "checklists" / "dev-checklist.md"
TESTING_SETUP_SOURCE = REPOSITORY_ROOT / "docs" / "testing-setup"
TESTING_SETUP_DESTINATION = REPOSITORY_ROOT / "skills" / "android-automation-testing-setup"

SOURCE_TEMPLATE_LINK = (
    b"](../skills/android-app-policy-test/assets/templates/user-rules-template.md)"
)
PACKAGED_TEMPLATE_LINK = b"](../assets/templates/user-rules-template.md)"

AUTOMATION_REPORTING_RESOURCES = (
    "references/automation-reporting-workflow.md",
    "references/coverage-workflow.md",
    "references/coverage-format.md",
    "references/failure-evidence.md",
    "assets/templates/test-report-template.md",
    "assets/templates/retest-report-template.md",
    "assets/templates/group-report-template.md",
    "assets/templates/coverage-template.json",
    "assets/templates/FailureEvidence.kt",
    "scripts/validate-coverage.py",
    "scripts/production-guard.py",
    "scripts/runner_evidence.py",
    "scripts/record-test-run.py",
)
AUTOMATION_REPORTING_EXTENSION = b"""
## Mandatory project extension: coverage and production protection

These requirements take precedence over the preserved twelve-step guide below.
Use this skill across Android XML/Views projects; discover project-specific
packages and workflows instead of assuming an app, module, variant or DI stack.

- Write and run automation tests; never fix application bugs or change production
  code, resources, manifests, DI, interfaces, business behavior or release settings.
  This overrides the test-seam/DI changes suggested in Steps 2 and 4. Allow only
  test source sets, test helpers/fixtures, reports and minimal test-only dependency
  or runner configuration. Keep existing user changes intact. If testing requires
  a production change, retain the case as blocked and explain the prerequisite.
- Read [coverage-workflow.md](references/coverage-workflow.md) and
  [automation-reporting-workflow.md](references/automation-reporting-workflow.md)
  before planning. Default TEST covers all applicable workflows of the selected
  app/variant, including contributing modules. Explicit focused or analysis-only
  requests retain their scope. Unsupported UI remains an explicit coverage gap.
- Inventory packages, workflows and behavioral branches before selecting cases.
  Mirror production packages for component tests; separate multi-screen and long
  journeys under test-only workflows packages. Every case has one primary owner.
- Use [coverage-format.md](references/coverage-format.md) for the versioned
  coverage v2 artifact, runner collector and design/implementation/execution gates.
  Execution reparses current runner evidence and checks production live.
  Do not claim full-app coverage from a small passing suite or a case count alone.
- Read [failure-evidence.md](references/failure-evidence.md) when adding UI tests.
  Capture reproducible UI failures before cleanup where possible, preserve all
  attempts and the original exception, and explain unavailable screenshots.
- Save PROJECT_ROOT/autotesting-reports/<run-id>/report.md and grouped reports.
  PASS/FAIL require current runner evidence. RETEST preserves all baseline IDs,
  expected results and history; expanded coverage needs a new TEST baseline.

The original twelve steps and references are preserved as framework guidance.
"""


def validate_automation_reporting_resources() -> bool:
    valid = True
    for relative_path in AUTOMATION_REPORTING_RESOURCES:
        path = TESTING_SETUP_DESTINATION / relative_path
        if not path.is_file():
            print(f"Required automation reporting resource not found: {path}", file=sys.stderr)
            valid = False
        elif not path.read_bytes().strip():
            print(f"Required automation reporting resource is empty: {path}", file=sys.stderr)
            valid = False
    if not valid:
        print(
            "Restore the maintained reporting workflow/templates in the skill package; "
            "they are not generated from docs/testing-setup/.",
            file=sys.stderr,
        )
    return valid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if packaged skill files differ from their maintained sources",
    )
    args = parser.parse_args()

    if not validate_automation_reporting_resources():
        return 1

    if not CHECKLIST_SOURCE.is_file():
        print(f"Checklist source not found: {CHECKLIST_SOURCE}", file=sys.stderr)
        return 1

    checklist_source_content = CHECKLIST_SOURCE.read_bytes()
    if checklist_source_content.count(SOURCE_TEMPLATE_LINK) != 1:
        print(
            f"Expected exactly one template link in checklist source: {CHECKLIST_SOURCE}",
            file=sys.stderr,
        )
        return 1

    checklist_package_content = checklist_source_content.replace(
        SOURCE_TEMPLATE_LINK, PACKAGED_TEMPLATE_LINK
    )
    testing_setup_entrypoint = TESTING_SETUP_SOURCE / "SKILL.md"
    if not testing_setup_entrypoint.is_file():
        print(f"Testing setup source not found: {testing_setup_entrypoint}", file=sys.stderr)
        return 1

    testing_setup_content = testing_setup_entrypoint.read_bytes()
    source_header = b"---\nname: testing-setup\n"
    if not testing_setup_content.startswith(source_header):
        print(
            f"Expected testing-setup name at the start of: {testing_setup_entrypoint}",
            file=sys.stderr,
        )
        return 1

    frontmatter_end = testing_setup_content.find(b"\n---\n", len(source_header))
    if frontmatter_end < 0:
        print("Testing setup source has no closing frontmatter", file=sys.stderr)
        return 1
    frontmatter_end += len(b"\n---\n")
    testing_setup_package_content = (
        b"---\nname: android-automation-testing-setup\n"
        + testing_setup_content[len(source_header):frontmatter_end]
        + AUTOMATION_REPORTING_EXTENSION
        + testing_setup_content[frontmatter_end:]
    )
    packaged_files = [
        (CHECKLIST_DESTINATION, checklist_package_content, "Packaged checklist"),
        (
            TESTING_SETUP_DESTINATION / "SKILL.md",
            testing_setup_package_content,
            "Packaged Android testing setup",
        ),
    ]
    for source_path in sorted(TESTING_SETUP_SOURCE.rglob("*")):
        if source_path.is_file() and source_path != testing_setup_entrypoint:
            relative_path = source_path.relative_to(TESTING_SETUP_SOURCE)
            if relative_path.as_posix() in AUTOMATION_REPORTING_RESOURCES:
                print(
                    f"Source file would overwrite a maintained reporting resource: {source_path}",
                    file=sys.stderr,
                )
                return 1
            packaged_files.append(
                (
                    TESTING_SETUP_DESTINATION / relative_path,
                    source_path.read_bytes(),
                    "Packaged testing setup reference",
                )
            )

    if args.check:
        stale = False
        for path, expected_content, description in packaged_files:
            if not path.is_file():
                print(f"{description} not found: {path}", file=sys.stderr)
                stale = True
            elif path.read_bytes() != expected_content:
                print(f"{description} is out of date: {path}", file=sys.stderr)
                stale = True
        if LEGACY_CHECKLIST_DESTINATION.exists():
            print(
                f"Checklist remains at the old package path: {LEGACY_CHECKLIST_DESTINATION}",
                file=sys.stderr,
            )
            stale = True
        if stale:
            print(
                "Run `python3 scripts/prepare-skill.py` to update packaged files.",
                file=sys.stderr,
            )
            return 1
        print("Packaged checklist, Android testing setup and reporting resources are valid.")
        return 0

    for path, content, _description in packaged_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        print(f"Updated {path.relative_to(REPOSITORY_ROOT)}")

    if LEGACY_CHECKLIST_DESTINATION.exists():
        LEGACY_CHECKLIST_DESTINATION.unlink()
        try:
            LEGACY_CHECKLIST_DESTINATION.parent.rmdir()
        except OSError:
            pass
        print("Removed checklist from its old package path.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

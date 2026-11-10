"""Packaging behavior for the maintained Android automation skill extension."""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "android-automation-testing-setup"
REPORTING_RESOURCES = (
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


class PrepareSkillTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="qa-skill-test-")
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        (self.root / "scripts").mkdir()
        (self.root / "docs").mkdir()
        shutil.copy2(
            REPOSITORY_ROOT / "scripts/prepare-skill.py",
            self.root / "scripts/prepare-skill.py",
        )
        shutil.copy2(REPOSITORY_ROOT / "docs/dev-checklist.md", self.root / "docs/dev-checklist.md")
        shutil.copytree(
            REPOSITORY_ROOT / "docs/testing-setup", self.root / "docs/testing-setup"
        )
        self.source = self.root / "docs/testing-setup"
        self.package = self.root / "skills" / SKILL_NAME
        for relative_path in REPORTING_RESOURCES:
            destination = self.package / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                REPOSITORY_ROOT / "skills" / SKILL_NAME / relative_path, destination
            )

    def run_prepare(self, *arguments):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/prepare-skill.py"), *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def assert_sync_succeeds(self):
        result = self.run_prepare()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_prepare("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def source_bytes(self):
        return {
            p.relative_to(self.source): p.read_bytes()
            for p in self.source.rglob("*")
            if p.is_file()
        }

    def test_sync_preserves_original_guide_and_references(self):
        original_source = self.source_bytes()
        self.assert_sync_succeeds()
        self.assertEqual(self.source_bytes(), original_source)
        expected_guide = original_source[Path("SKILL.md")].replace(
            b"---\nname: testing-setup\n", b"---\nname: android-automation-testing-setup\n", 1
        )
        entrypoint = (self.package / "SKILL.md").read_bytes()
        header, body = expected_guide.split(b"\n---\n", 1)
        self.assertTrue(entrypoint.startswith(header + b"\n---\n"))
        self.assertTrue(entrypoint.endswith(body))
        self.assertLess(entrypoint.index(b"Mandatory project extension"), entrypoint.index(b"## Step 1:"))
        for relative_path, expected in original_source.items():
            if relative_path != Path("SKILL.md"):
                self.assertEqual((self.package / relative_path).read_bytes(), expected)
        self.assertFalse(
            (self.root / "skills/android-app-policy-test/references/testing-setup.md").exists()
        )

    def test_repeated_sync_keeps_maintained_reporting_resources(self):
        resource = self.package / REPORTING_RESOURCES[0]
        resource.write_bytes(resource.read_bytes() + b"\nMaintainer extension.\n")
        expected = {p: (self.package / p).read_bytes() for p in REPORTING_RESOURCES}
        self.assert_sync_succeeds()
        self.assert_sync_succeeds()
        self.assertEqual({p: (self.package / p).read_bytes() for p in REPORTING_RESOURCES}, expected)

    def test_check_detects_and_sync_repairs_generated_entrypoint(self):
        self.assert_sync_succeeds()
        entrypoint = self.package / "SKILL.md"
        expected = entrypoint.read_bytes()
        entrypoint.write_bytes(b"Changed generated guide.\n")
        result = self.run_prepare("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("out of date", result.stderr)
        self.assert_sync_succeeds()
        self.assertEqual(entrypoint.read_bytes(), expected)

    def test_check_detects_and_sync_repairs_generated_reference(self):
        self.assert_sync_succeeds()
        reference = next((self.source / "references").rglob("*.md"))
        packaged_reference = self.package / reference.relative_to(self.source)
        packaged_reference.write_bytes(b"Changed generated reference.\n")
        self.assertEqual(self.run_prepare("--check").returncode, 1)
        self.assert_sync_succeeds()
        self.assertEqual(packaged_reference.read_bytes(), reference.read_bytes())

    def test_check_detects_and_sync_repairs_policy_checklist(self):
        self.assert_sync_succeeds()
        checklist = self.root / "skills/android-app-policy-test/references/dev-checklist.md"
        expected = checklist.read_bytes()
        checklist.write_bytes(b"Changed generated checklist.\n")
        self.assertEqual(self.run_prepare("--check").returncode, 1)
        self.assert_sync_succeeds()
        self.assertEqual(checklist.read_bytes(), expected)

    def test_missing_reporting_resources_fail_before_writing_generated_files(self):
        for relative_path in REPORTING_RESOURCES:
            with self.subTest(resource=relative_path):
                path = self.package / relative_path
                content = path.read_bytes()
                path.unlink()
                try:
                    for arguments in [(), ("--check",)]:
                        result = self.run_prepare(*arguments)
                        self.assertEqual(result.returncode, 1)
                        self.assertIn(relative_path, result.stderr)
                    self.assertFalse((self.package / "SKILL.md").exists())
                finally:
                    path.write_bytes(content)

    def test_empty_reporting_resource_is_rejected(self):
        resource = self.package / REPORTING_RESOURCES[1]
        resource.write_bytes(b" \n\t")
        result = self.run_prepare()
        self.assertEqual(result.returncode, 1)
        self.assertIn("is empty", result.stderr)
        self.assertFalse((self.package / "SKILL.md").exists())

    def test_source_cannot_overwrite_a_maintained_reporting_resource(self):
        for relative_path in REPORTING_RESOURCES:
            with self.subTest(resource=relative_path):
                collision = self.source / relative_path
                collision.parent.mkdir(parents=True, exist_ok=True)
                collision.write_bytes(b"Conflicting upstream file.\n")
                expected = (self.package / relative_path).read_bytes()
                try:
                    result = self.run_prepare()
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("would overwrite", result.stderr)
                    self.assertEqual((self.package / relative_path).read_bytes(), expected)
                    self.assertFalse((self.package / "SKILL.md").exists())
                finally:
                    collision.unlink()

    def test_invalid_source_name_is_rejected_without_changing_source(self):
        source_entrypoint = self.source / "SKILL.md"
        changed = source_entrypoint.read_bytes().replace(
            b"name: testing-setup\n", b"name: unexpected-name\n", 1
        )
        source_entrypoint.write_bytes(changed)
        result = self.run_prepare()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Expected testing-setup name", result.stderr)
        self.assertEqual(source_entrypoint.read_bytes(), changed)
        self.assertFalse((self.package / "SKILL.md").exists())

    def test_missing_source_is_reported_without_creating_an_entrypoint(self):
        (self.source / "SKILL.md").unlink()
        result = self.run_prepare()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Testing setup source not found", result.stderr)
        self.assertFalse((self.package / "SKILL.md").exists())

    def test_copied_package_keeps_all_reporting_links_inside_the_installation(self):
        self.assert_sync_succeeds()
        installation = self.root / "unrelated-app/.agents/skills" / SKILL_NAME
        shutil.copytree(self.package, installation)
        for document in installation.rglob("*.md"):
            targets = re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", document.read_text())
            for target in targets:
                if "://" in target or target.startswith(("#", "mailto:")) or "<" in target:
                    continue
                resolved = (document.parent / target.split("#", 1)[0]).resolve()
                with self.subTest(document=document, target=target):
                    self.assertTrue(resolved.exists())
                    self.assertIn(installation.resolve(), (resolved, *resolved.parents))

        # Both entrypoints find sibling dependencies through copy and symlink installs.
        linked = self.root / "unrelated-app/.claude/skills" / SKILL_NAME
        linked.parent.mkdir(parents=True)
        linked.symlink_to(self.package, target_is_directory=True)
        for installed in (installation, linked):
            for script in ("validate-coverage.py", "record-test-run.py"):
                result = subprocess.run(
                    [sys.executable, str(installed / "scripts" / script), "--help"],
                    cwd=self.root, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

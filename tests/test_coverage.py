"""Coverage/production protection fixtures; never results for a real Android app."""

import base64
import copy
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1] / "skills/android-automation-testing-setup"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), PACKAGE / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coverage = load_script("validate-coverage")
guard = load_script("production-guard")
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="automation-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.run = self.root / "autotesting-reports/fixture-test"
        self.run.mkdir(parents=True)
        self.put_project("app/src/main/java/fixture/editor/Editor.kt", "// fixture production, never modified by test tooling\n")
        self.put_project("app/src/main/res/layout/editor.xml", "<FrameLayout />")
        self.data = self.fixture("fixture.notes")

    def put_project(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)

    def put(self, path, content):
        destination = self.run / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content if isinstance(content, bytes) else content.encode())
        return path

    def fixture(self, base):
        packages = [base + ".editor", base + ".storage"]
        cases = []
        for number in (1, 2):
            cid = "AT-%03d" % number
            cases.append({
                "id": cid, "name": "fixture scenario " + str(number),
                "module": "app", "variant": "debug",
                "owner": {"kind": "package", "id": packages[0]} if number == 1 else {"kind": "workflow", "id": "WF-001"},
                "related_packages": packages if number == 2 else packages[:1],
                "workflow_ids": ["WF-001"], "screens": ["Editor", "Detail"] if number == 2 else [],
                "layer": "unit" if number == 1 else "ui", "preconditions": "isolated fixture only",
                "steps": ["enter fixed title", "save and inspect outcome"], "expected": "saved fixture title",
                "checkpoints": [{"id": "enter", "action": "enter title", "expected": "title accepted"}, {"id": "save", "action": "save", "expected": "detail shows title"}],
                "automation": {"implemented": False, "symbol": "", "source": ""},
                "result": {"status": "NOT_TESTED", "reason": "fixture not executed", "attempts": []},
            })
        return {
            "version": 2,
            "project": {"root": str(self.root), "application_id": base, "module": "app", "variant": "debug", "source_ref": "fixture-source-v1", "branch": "fixture", "skill_ref": "fixture-skill-v1"},
            "run": {"id": "fixture-test", "mode": "TEST", "started_at": "2026-10-30T09:00:00+07:00", "ended_at": "2026-10-30T11:00:00+07:00"},
            "executions": [],
            "scope": {"kind": "full_app", "description": "simulated coverage fixture, not real app results", "discovery_complete": True, "discovery_sources": ["app/src/main/AndroidManifest.xml", "app/src/main/java"], "exclusions": []},
            "packages": [{"id": p, "source_refs": ["app/src/main/java"], "disposition": "covered"} for p in packages],
            "workflows": [{"id": "WF-001", "name": "save and inspect fixture", "kind": "multi_screen", "source_refs": ["app/src/main/java"], "related_packages": packages, "screens": ["Editor", "Detail"]}],
            "obligations": [
                {"id": "OB-001", "package_id": packages[0], "workflow_id": "WF-001", "description": "validate input", "expected": "accepted", "applicable": True, "case_ids": ["AT-001"]},
                {"id": "OB-002", "package_id": packages[1], "workflow_id": "WF-001", "description": "persist title", "expected": "saved", "applicable": True, "case_ids": ["AT-002"]},
            ],
            "cases": cases,
            "test_config_changes": [],
        }

    def complete(self):
        for case in self.data["cases"]:
            package = case["owner"]["id"] if case["owner"]["kind"] == "package" else self.data["project"]["application_id"] + ".workflows.fixture"
            source = "app/src/%s/java/%s/%s.kt" % ("test" if case["layer"] == "unit" else "androidTest", package.replace(".", "/"), case["id"])
            self.put_project(source, "// fixture test source\n")
            case["automation"] = {"implemented": True, "symbol": "fixture.Tests." + case["id"], "source": source}
            case["result"] = {"status": "PASS", "reason": "", "attempts": [{
                "id": "attempt-1", "run_id": self.data["run"]["id"], "source_ref": self.data["project"]["source_ref"],
                "module": case["module"], "variant": case["variant"],
                "symbol": case["automation"]["symbol"], "status": "PASS", "actual": "simulated runner fixture; not an app execution",
                "started_at": "2026-10-30T10:00:00+07:00", "ended_at": "2026-10-30T10:00:01+07:00",
                "evidence": [self.put("test-evidence/checks/" + case["id"] + ".txt", "SIMULATED FIXTURE PASS\n")],
            }]}
            self.execution(case)
        state = json.dumps(guard.snapshot(self.root))
        self.data["production_guard"] = {
            "before": self.put("test-evidence/inputs/production-before.json", state),
            "after": self.put("test-evidence/inputs/production-after.json", state),
            "unchanged": True,
        }

    def execution(self, case):
        """Write explicit SIMULATED raw runner evidence, never Android execution."""
        eid = case["id"]
        directory = "test-evidence/checks/executions/" + eid + "/"
        symbol = case["automation"]["symbol"]
        class_name, _, name = symbol.rpartition(".")
        xml = '<testsuite name="SIMULATED FIXTURE">'
        for ordinal, attempt in enumerate(case["result"]["attempts"], 1):
            xml += '<testcase classname="%s" name="%s">%s</testcase>' % (class_name, name, '<failure message="SIMULATED"/>' if attempt["status"] == "FAIL" else '')
            attempt["runner_result"] = {"execution_id": eid, "class_name": class_name, "test_name": name, "ordinal": ordinal}
        path = self.put(directory + "result.xml", xml + '</testsuite>')
        hashed = coverage.runner.digest(self.run / path)
        files = [{"path": path, "role": "result", "sha256": hashed, "before": None, "after": {"sha256": hashed}}]
        for role in ("stdout", "stderr"):
            log = self.put(directory + role + '.txt', 'SIMULATED FIXTURE\n')
            files.append({"path": log, "role": role, "sha256": coverage.runner.digest(self.run / log)})
        manifest = {"version": 1, "id": eid, "run_id": self.data["run"]["id"], "source_ref": self.data["project"]["source_ref"],
                    "project_root": str(self.root), "working_directory": str(self.root), "module": case["module"], "variant": case["variant"],
                    "started_at": "2026-10-30T10:00:00+07:00", "ended_at": "2026-10-30T10:01:00+07:00", "exit_code": 0,
                    "format": "junit-xml", "command": ["SIMULATED-FIXTURE"], "files": files}
        path = self.put(directory + 'manifest.json', json.dumps(manifest))
        row = {"id": eid, "manifest": path, "sha256": coverage.runner.digest(self.run / path)}
        self.data["executions"] = [item for item in self.data["executions"] if item["id"] != eid] + [row]

    def baseline_reference(self, baseline):
        directory = self.root / "autotesting-reports/baseline-fixture"
        path = directory / coverage.ARTIFACT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(baseline))
        self.data["baseline"] = {"run_dir": "../baseline-fixture", "sha256": coverage.runner.digest(path)}

    def failure(self, case_index=1, screenshot=True):
        case = self.data["cases"][case_index]
        case["result"]["status"] = "FAIL"
        attempt = case["result"]["attempts"][0]
        attempt["status"] = "FAIL"
        attempt["actual"] = "SIMULATED FIXTURE assertion failure at save"
        if screenshot:
            path = "test-evidence/screenshots/" + case["id"] + "/attempt-1/save.png"
            self.put(path, PNG)
            attempt["screenshot"] = {"status": "captured", "files": [{"path": path, "checkpoint_id": "save", "timing": "failure", "captured_at": "2026-10-30T10:00:01+07:00"}]}
        else:
            attempt["screenshot"] = {"status": "unavailable", "reason": "fixture device disconnected", "files": []}
        self.execution(case)
        return case

    def validate(self, phase="design", baseline=None):
        return coverage.validate(self.data, self.run, phase, baseline)

    def assert_invalid(self, fragment, phase="design", baseline=None):
        result = self.validate(phase, baseline)
        self.assertFalse(result["valid"], result)
        self.assertTrue(any(fragment in message for message in result["errors"]), result)

    def test_design_can_be_complete_before_automation_exists(self):
        self.assertTrue(self.validate()["valid"])
        self.assert_invalid("not implemented", "implementation")

    def test_two_different_apps_use_same_contract_without_hardcoded_packages(self):
        for base in ("fixture.notes", "other.catalog.checkout"):
            with self.subTest(base=base):
                self.data = self.fixture(base)
                self.assertTrue(self.validate()["valid"])

    def test_package_missing_obligations_is_a_gap(self):
        self.data["packages"].append({"id": "fixture.camera", "source_refs": ["Camera.kt"], "disposition": "covered"})
        self.assert_invalid("no applicable obligations")

    def test_missing_error_branch_mapping_fails_even_when_existing_cases_pass(self):
        self.complete()
        obligation = copy.deepcopy(self.data["obligations"][0])
        obligation.update(id="OB-003", description="server failure", case_ids=[])
        self.data["obligations"].append(obligation)
        self.assert_invalid("unmapped behavioral branch", "execution")

    def test_unknown_expected_or_incomplete_discovery_prevents_baseline_claim(self):
        self.data["scope"]["discovery_complete"] = False
        self.data["obligations"][0]["expected"] = ""
        self.assert_invalid("discovery is incomplete")
        self.assert_invalid("missing expected")

    def test_full_app_cannot_drop_package_due_to_environment(self):
        self.data["packages"][0].update(disposition="out_of_scope", reason="no emulator")
        self.assert_invalid("cannot exclude")

    def test_journey_must_have_separate_owner(self):
        self.data["cases"][1]["owner"] = {"kind": "package", "id": self.data["packages"][1]["id"]}
        self.assert_invalid("missing independently runnable journey")
        self.assert_invalid("multi-screen test must")

    def test_long_workflow_requires_meaningful_checkpoints(self):
        self.data["cases"][1]["checkpoints"] = [{"id": "save", "action": "save", "expected": ""}]
        self.assert_invalid("checkpoint missing")
        self.assert_invalid("at least two")

    def test_duplicate_cases_and_multiple_primary_owners_are_rejected(self):
        self.data["cases"].append(copy.deepcopy(self.data["cases"][0]))
        self.assert_invalid("duplicate id")
        self.data["cases"].pop()
        self.data["cases"][0]["owner"] = [{"kind": "package", "id": "x"}]
        self.assert_invalid("exactly one primary owner")

    def test_related_mapping_does_not_double_count(self):
        self.complete()
        self.data["obligations"][0]["case_ids"].append("AT-002")
        result = self.validate("execution")
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["summary"]["cases"], 2)
        self.assertEqual(result["summary"]["statuses"]["PASS"], 2)

    def test_failed_ui_case_with_real_png_fixture_has_evidence(self):
        self.complete()
        self.failure()
        self.assertTrue(self.validate("execution")["valid"])

    def test_unavailable_screenshot_does_not_hide_original_failure(self):
        self.complete()
        self.failure(screenshot=False)
        result = self.validate("execution")
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["summary"]["statuses"]["FAIL"], 1)

    def test_ui_failure_without_capture_or_reason_is_rejected(self):
        self.complete()
        case = self.failure(screenshot=False)
        case["result"]["attempts"][0]["screenshot"]["reason"] = ""
        self.assert_invalid("missing screenshot reason", "execution")

    def test_jvm_failure_can_explain_why_screenshot_does_not_apply(self):
        self.complete()
        case = self.failure(case_index=0, screenshot=False)
        case["result"]["attempts"][0]["screenshot"] = {"status": "not_applicable", "reason": "pure JVM assertion, no UI"}
        self.assertTrue(self.validate("execution")["valid"])

    def test_screenshot_attribution_and_format_are_validated(self):
        self.complete()
        case = self.failure()
        image = case["result"]["attempts"][0]["screenshot"]["files"][0]
        image["path"] = self.put("test-evidence/screenshots/AT-999/attempt-1/save.png", b"not an image")
        image["checkpoint_id"] = "unknown"
        self.assert_invalid("wrong case/attempt", "execution")
        self.assert_invalid("not PNG", "execution")
        self.assert_invalid("unknown screenshot checkpoint", "execution")

    def test_successful_retry_cannot_erase_failure_in_same_run(self):
        self.complete()
        case = self.failure()
        retry = copy.deepcopy(case["result"]["attempts"][0])
        retry.update(id="attempt-2", status="PASS", actual="SIMULATED successful retry")
        retry.pop("screenshot")
        case["result"]["attempts"].append(retry)
        case["result"]["status"] = "PASS"
        self.assert_invalid("retry must not hide", "execution")

    def test_stale_source_evidence_and_path_traversal_fail(self):
        self.complete()
        attempt = self.data["cases"][0]["result"]["attempts"][0]
        attempt["source_ref"] = "old-source"
        attempt["evidence"] = ["../../outside.txt"]
        self.assert_invalid("stale run/source", "execution")
        self.assert_invalid("escapes run directory", "execution")

    def test_symlink_cannot_smuggle_evidence_from_another_run(self):
        self.complete()
        outside = self.root / "outside.txt"
        outside.write_text("old evidence")
        link = self.run / "test-evidence/checks/link.txt"
        link.symlink_to(outside)
        self.data["cases"][0]["result"]["attempts"][0]["evidence"] = [str(link.relative_to(self.run))]
        self.assert_invalid("escapes run directory", "execution")

    def test_missing_device_does_not_prevent_unit_execution(self):
        self.complete()
        self.data["cases"][1]["result"] = {"status": "BLOCKED", "reason": "fixture has no emulator", "attempts": []}
        self.assertTrue(self.validate("implementation")["valid"])
        self.assert_invalid("execution is incomplete", "execution")
        self.assertEqual(self.validate("implementation")["summary"]["executed"], 1)

    def test_production_snapshot_mismatch_blocks_completion(self):
        self.complete()
        state = guard.snapshot(self.root)
        state["files"]["app/src/main/java/New.kt"] = "changed"
        self.put(self.data["production_guard"]["after"], json.dumps(state))
        self.assert_invalid("production snapshots differ", "execution")

    def test_test_configuration_needs_explicit_diff_review(self):
        self.complete()
        self.data["test_config_changes"] = [{"path": "app/build.gradle.kts", "reason": "test runner", "test_only_reviewed": False}]
        self.assert_invalid("test-only diff review", "execution")

    def test_automation_cannot_point_at_production_or_missing_test_source(self):
        self.complete()
        self.data["cases"][0]["automation"]["source"] = "app/src/main/java/fixture/editor/Editor.kt"
        self.assert_invalid("must belong to a test source set", "implementation")
        self.data["cases"][0]["automation"]["source"] = "app/src/test/java/Missing.kt"
        self.assert_invalid("test source file is missing", "implementation")

    def test_missing_snapshot_is_reported_without_crashing(self):
        self.complete()
        self.data["production_guard"]["after"] = "test-evidence/inputs/missing.json"
        self.assert_invalid("evidence file missing", "execution")

    def test_test_source_organization_matches_primary_owner(self):
        self.complete()
        misplaced = "app/src/androidTest/java/fixture/Misplaced.kt"
        self.put_project(misplaced, "// fixture misplaced source")
        self.data["cases"][1]["automation"]["source"] = misplaced
        self.assert_invalid("stored under workflows package", "implementation")
        self.data["cases"][0]["automation"]["source"] = misplaced
        self.assert_invalid("mirror its production package", "implementation")

    def test_contributing_module_case_requires_matching_runner_target(self):
        self.data["cases"][0]["module"] = "feature:storage"
        self.complete()
        self.assertTrue(self.validate("execution")["valid"])
        self.data["cases"][0]["result"]["attempts"][0]["module"] = "app"
        self.assert_invalid("runner module/variant", "execution")

    def test_test_path_symlink_cannot_point_to_production(self):
        self.complete()
        source = self.root / self.data["cases"][0]["automation"]["source"]
        source.unlink()
        source.symlink_to(self.root / "app/src/main/java/fixture/editor/Editor.kt")
        self.assert_invalid("must belong to a test source set", "implementation")

    def test_retest_allows_new_execution_but_preserves_definitions(self):
        baseline = copy.deepcopy(self.data)
        self.data["run"].update(id="fixture-retest", mode="RETEST")
        self.run = self.root / "autotesting-reports/fixture-retest"
        self.run.mkdir()
        self.baseline_reference(baseline)
        self.complete()
        self.assertTrue(self.validate("execution", baseline)["valid"])
        self.data["cases"][0]["expected"] = "changed expected"
        self.assert_invalid("baseline testcase definition changed", "execution", baseline)

    def test_retest_cannot_expand_inventory_or_use_other_project(self):
        baseline = copy.deepcopy(self.data)
        self.data["run"]["mode"] = "RETEST"
        self.data["cases"].pop()
        baseline["project"]["variant"] = "release"
        self.assert_invalid("baseline testcase IDs changed", baseline=baseline)
        self.assert_invalid("baseline project mismatch", baseline=baseline)

    def test_declared_totals_cannot_count_references_as_cases(self):
        self.data["summary"] = {"cases": 100}
        self.assert_invalid("declared summary")

    def test_cli_reports_invalid_json_without_traceback(self):
        self.put(coverage.ARTIFACT, "{")
        result = subprocess.run([sys.executable, str(PACKAGE / "scripts/validate-coverage.py"), str(self.run), "--phase", "design"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stdout)["valid"])
        self.assertNotIn("Traceback", result.stderr)

    def rewrite_execution(self, case, change):
        row = next(r for r in self.data["executions"] if r["id"] == case["id"])
        path = self.run / row["manifest"]
        manifest = json.loads(path.read_text())
        change(manifest)
        path.write_text(json.dumps(manifest))
        row["sha256"] = coverage.runner.digest(path)

    def replace_raw(self, case, content):
        def replace(manifest):
            entry = next(f for f in manifest["files"] if f["role"] == "result")
            (self.run / entry["path"]).write_text(content)
            entry["sha256"] = coverage.runner.digest(self.run / entry["path"])
            entry["after"]["sha256"] = entry["sha256"]
        self.rewrite_execution(case, replace)

    def test_screenshot_traversal_between_cases_is_rejected(self):
        self.complete()
        case = self.failure()
        self.put("test-evidence/screenshots/AT-001/attempt-1/save.png", PNG)
        case["result"]["attempts"][0]["screenshot"]["files"][0]["path"] = "test-evidence/screenshots/AT-002/attempt-1/../../AT-001/attempt-1/save.png"
        self.assert_invalid("unsafe path", "execution")

    def test_screenshot_symlink_and_absolute_path_are_rejected(self):
        self.complete()
        case = self.failure()
        image = case["result"]["attempts"][0]["screenshot"]["files"][0]
        original = self.run / image["path"]
        alias = original.with_name("alias.png")
        alias.symlink_to(original)
        image["path"] = str(alias.relative_to(self.run))
        self.assert_invalid("symlink", "execution")
        image["path"] = str(original)
        self.assert_invalid("unsafe path", "execution")

    def test_independent_identical_screenshots_allowed_but_hardlink_reuse_rejected(self):
        self.complete()
        a, b = self.failure(0), self.failure(1)
        self.assertTrue(self.validate("execution")["valid"])
        source = self.run / a["result"]["attempts"][0]["screenshot"]["files"][0]["path"]
        target = self.run / b["result"]["attempts"][0]["screenshot"]["files"][0]["path"]
        target.unlink()
        os.link(source, target)
        self.assert_invalid("screenshot reused", "execution")

    def test_skipped_runner_result_cannot_be_declared_pass(self):
        self.complete()
        case = self.data["cases"][0]
        self.replace_raw(case, '<testsuite><testcase classname="fixture.Tests" name="AT-001"><skipped/></testcase></testsuite>')
        self.assert_invalid("runner status mismatch", "execution")

    def test_runner_parameter_identity_is_exact(self):
        self.complete()
        case = self.data["cases"][0]
        self.replace_raw(case, '<testsuite><testcase classname="fixture.Tests" name="AT-001[parameter=2]"/></testsuite>')
        self.assert_invalid("runner result missing", "execution")

    def test_runner_symbol_and_execution_metadata_must_match(self):
        for field, value, fragment in (("module", "other", "module/variant"), ("variant", "release", "module/variant"),
                                       ("source_ref", "old", "stale run/source"), ("run_id", "old", "stale run/source")):
            with self.subTest(field=field):
                self.complete()
                case = self.data["cases"][0]
                self.rewrite_execution(case, lambda manifest: manifest.update({field: value}))
                self.assert_invalid(fragment, "execution")
        self.complete()
        self.data["cases"][0]["automation"]["symbol"] = "other.Class.method"
        self.assert_invalid("runner symbol mismatch", "execution")

    def test_raw_evidence_and_manifest_mutation_are_detected(self):
        self.complete()
        row = self.data["executions"][0]
        path = self.run / row["manifest"]
        original = path.read_text()
        path.write_text(original + ' ')
        self.assert_invalid("manifest path/hash", "execution")
        path.write_text(original)
        manifest = json.loads(original)
        raw = self.run / manifest["files"][0]["path"]
        raw.write_text('<testsuite/>')
        self.assert_invalid("evidence hash mismatch", "execution")

    def test_runner_result_cannot_be_reused_by_another_attempt(self):
        self.complete()
        case = self.data["cases"][0]
        retry = copy.deepcopy(case["result"]["attempts"][0])
        retry["id"] = "attempt-2"
        case["result"]["attempts"].append(retry)
        self.assert_invalid("runner result reused", "execution")

    def test_merged_flaky_failure_cannot_be_omitted(self):
        self.complete()
        case = self.data["cases"][0]
        self.replace_raw(case, '<testsuite><testcase classname="fixture.Tests" name="AT-001"><flakyFailure/></testcase></testsuite>')
        case["result"]["attempts"][0]["runner_result"]["ordinal"] = 2
        self.assert_invalid("runner retry omitted", "execution")

    def test_live_guard_detects_changes_after_identical_saved_snapshots(self):
        self.complete()
        self.put_project("app/src/main/java/fixture/editor/Editor.kt", "changed after snapshots")
        (self.root / "app/src/main/res/layout/editor.xml").unlink()
        self.put_project("app/src/main/java/New.kt", "new production")
        result = self.validate("execution")
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["production_guard"]["changed_paths"]), 3)
        self.assertIn("checked_at", result["production_guard"])

    def test_live_guard_ignores_test_and_build_output_changes(self):
        self.complete()
        self.put_project("app/src/test/java/NewTest.kt", "test")
        self.put_project("app/build/generated/Generated.kt", "build")
        self.assertTrue(self.validate("execution")["valid"])

    def test_v1_is_readable_but_cannot_pass_execution(self):
        self.complete()
        self.data["version"] = 1
        self.assertTrue(self.validate("design")["valid"])
        self.assertTrue(self.validate("implementation")["valid"])
        self.assert_invalid("new coverage v2 run", "execution")

    def test_v2_retest_accepts_unmodified_v1_baseline_and_rejects_old_run_id(self):
        baseline = copy.deepcopy(self.data)
        baseline["version"] = 1
        self.data["run"].update(id="fixture-retest", mode="RETEST")
        self.run = self.root / "autotesting-reports/fixture-retest"
        self.run.mkdir()
        self.baseline_reference(baseline)
        self.complete()
        self.assertTrue(self.validate("execution", baseline)["valid"])
        self.data["run"]["id"] = baseline["run"]["id"]
        self.assert_invalid("different run id", "execution", baseline)

    def test_retest_rejects_baseline_directory_alias_and_changed_hash(self):
        baseline = copy.deepcopy(self.data)
        baseline["run"]["id"] = "original-test"
        self.data["run"]["mode"] = "RETEST"
        artifact = self.run / coverage.ARTIFACT
        artifact.parent.mkdir(parents=True)
        artifact.write_text(json.dumps(baseline))
        alias = self.run.parent / "baseline-alias"
        alias.symlink_to(self.run, target_is_directory=True)
        self.data["baseline"] = {"run_dir": "../baseline-alias", "sha256": coverage.runner.digest(artifact)}
        self.assert_invalid("different run directory", baseline=baseline)
        self.data["baseline"]["sha256"] = "wrong"
        self.assert_invalid("baseline artifact hash mismatch", baseline=baseline)

    def test_real_collector_output_passes_full_execution_gate(self):
        self.complete()
        shutil.rmtree(self.run / "test-evidence/checks/executions")  # discard simulated setup before actual subprocess fixture
        self.data["executions"] = []
        self.data["run"]["started_at"] = coverage.runner.now()
        self.data["run"]["ended_at"] = None
        self.put(coverage.ARTIFACT, json.dumps(self.data))
        xml = '<testsuite name="SIMULATED SUBPROCESS"><testcase classname="fixture.Tests" name="AT-001"/><testcase classname="fixture.Tests" name="AT-002"/></testsuite>'
        code = "from pathlib import Path; p=Path('app/build/results'); p.mkdir(parents=True); (p/'fixture.xml').write_text(%r); print('SIMULATED SUBPROCESS')" % xml
        command = [sys.executable, str(PACKAGE / "scripts/record-test-run.py"), str(self.run), "--execution-id", "subprocess",
                   "--module", "app", "--variant", "debug", "--format", "junit-xml", "--results", "app/build/results/*.xml",
                   "--", sys.executable, "-c", code]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        row = json.loads(result.stdout)
        self.data["executions"] = [{"id": row["execution_id"], "manifest": row["manifest"], "sha256": row["sha256"]}]
        manifest = json.loads((self.run / row["manifest"]).read_text())
        for case in self.data["cases"]:
            attempt = case["result"]["attempts"][0]
            attempt.update(started_at=manifest["started_at"], ended_at=manifest["ended_at"], evidence=[row["manifest"]])
            attempt["runner_result"]["execution_id"] = row["execution_id"]
        self.data["run"]["ended_at"] = coverage.runner.now()
        checked = self.validate("execution")
        self.assertTrue(checked["valid"], checked)

    def test_execution_cannot_be_dropped_from_catalog_to_hide_history(self):
        self.complete()
        self.failure(0)
        self.data["executions"] = self.data["executions"][1:]
        self.assert_invalid("unregistered execution", "execution")

    def test_failed_retry_history_is_valid_when_all_attempts_are_preserved(self):
        self.complete()
        case = self.failure(0)
        retry = copy.deepcopy(case["result"]["attempts"][0])
        retry.update(id="attempt-2", status="PASS", actual="SIMULATED successful retry")
        retry.pop("screenshot")
        case["result"]["attempts"].append(retry)
        self.execution(case)
        result = self.validate("execution")
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["summary"]["statuses"]["FAIL"], 1)

    def test_execution_normalized_results_cannot_override_raw_status(self):
        self.complete()
        case = self.data["cases"][0]
        self.replace_raw(case, '<testsuite><testcase classname="fixture.Tests" name="AT-001"><error/></testcase></testsuite>')
        self.rewrite_execution(case, lambda manifest: manifest.update(results=[{"class_name": "fixture.Tests", "test_name": "AT-001", "ordinal": 1, "status": "PASS"}]))
        self.assert_invalid("runner status mismatch", "execution")

    def test_missing_live_guard_script_fails_as_json_without_traceback(self):
        with tempfile.TemporaryDirectory(prefix="missing-guard-fixture-") as directory:
            package = Path(directory)
            for script in ("validate-coverage.py", "runner_evidence.py"):
                shutil.copy2(PACKAGE / "scripts" / script, package / script)
            self.complete()
            self.put(coverage.ARTIFACT, json.dumps(self.data))
            result = subprocess.run([sys.executable, str(package / "validate-coverage.py"), str(self.run), "--phase", "execution"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse(json.loads(result.stdout)["production_guard"]["unchanged"])
            self.assertNotIn("Traceback", result.stderr)


class ProductionGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="production-guard-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def put(self, path, text="fixture"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def test_dirty_production_is_preserved_and_new_deleted_changed_files_detected(self):
        original = self.put("app/src/main/java/Existing.kt", "user dirty state")
        removed = self.put("feature/src/main/res/layout/item.xml")
        before = guard.snapshot(self.root)
        self.assertEqual(guard.check(self.root, before), [])
        self.assertEqual(original.read_text(), "user dirty state")
        original.write_text("changed")
        removed.unlink()
        self.put("feature/src/debug/AndroidManifest.xml")
        self.assertEqual(len(guard.check(self.root, before)), 3)

    def test_test_sources_and_build_outputs_are_allowed_but_production_package_named_build_is_protected(self):
        self.put("app/src/main/java/build/Important.kt")
        before = guard.snapshot(self.root)
        self.put("app/src/test/java/UnitTest.kt")
        self.put("app/src/androidTestDemoDebug/java/UiTest.kt")
        self.put("app/src/testFixtures/java/Fake.kt")
        self.put("app/build/generated/Generated.kt")
        self.put("autotesting-reports/run/snapshot.json")
        self.assertEqual(guard.check(self.root, before), [])
        self.put("app/src/main/java/build/Important.kt", "changed")
        self.assertEqual(guard.check(self.root, before), ["app/src/main/java/build/Important.kt"])

    def test_snapshot_cannot_be_used_for_another_project(self):
        before = guard.snapshot(self.root)
        before["project_root"] = "/other/project"
        with self.assertRaises(ValueError):
            guard.check(self.root, before)

    def test_symlinked_source_directory_is_not_silently_omitted(self):
        real = self.root / "actual-source"
        real.mkdir()
        module = self.root / "app/src/main"
        module.mkdir(parents=True)
        (module / "java").symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "explicit resolved"):
            guard.snapshot(self.root)


if __name__ == "__main__":
    unittest.main()

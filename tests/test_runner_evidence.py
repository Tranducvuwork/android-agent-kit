"""Raw protocol and subprocess collector fixtures; no Android app is executed."""

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/android-automation-testing-setup/scripts"
spec = importlib.util.spec_from_file_location("runner_evidence", SCRIPTS / "runner_evidence.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerParserTests(unittest.TestCase):
    def test_junit_statuses_parameters_and_merged_retries(self):
        xml = b'''<testsuites><testsuite><testcase classname="C" name="test[1]"/>
        <testcase classname="C" name="test[2]"><failure/></testcase>
        <testcase classname="C" name="error"><error/></testcase>
        <testcase classname="C" name="skip"><skipped/></testcase>
        <testcase classname="C" name="flaky"><flakyFailure/><flakyFailure/></testcase>
        <testcase classname="C" name="retry"><failure/><rerunFailure/></testcase>
        </testsuite></testsuites>'''
        result = runner.parse_results("junit-xml", [("result.xml", xml)])
        self.assertEqual([r["status"] for r in result], ["PASS", "FAIL", "FAIL", "SKIPPED", "FAIL", "FAIL", "PASS", "FAIL", "FAIL"])
        self.assertEqual([r["ordinal"] for r in result if r["test_name"] == "flaky"], [1, 2, 3])
        self.assertEqual(result[1]["test_name"], "test[2]")

    def test_multiple_xml_files_keep_ordinal_and_full_names(self):
        xml = b'<testsuite><testcase classname="C" name="test[param]"/></testsuite>'
        result = runner.parse_results("junit-xml", [("a", xml), ("b", xml)])
        self.assertEqual([r["ordinal"] for r in result], [1, 2])
        self.assertEqual([r["raw"] for r in result], ["a", "b"])

    def test_missing_identity_and_malformed_xml_are_rejected(self):
        for xml in (b'<testsuite><testcase name="x"/></testsuite>', b'<html/>', b'not xml'):
            with self.subTest(xml=xml), self.assertRaises((ValueError, runner.ET.ParseError)):
                runner.junit_records(xml)

    def test_instrumentation_terminal_codes_and_unfinished_crash(self):
        lines = []
        for index, code in enumerate((0, -1, -2, -3, -4)):
            for terminal in (1, code):
                lines.extend(["INSTRUMENTATION_STATUS: class=C", "INSTRUMENTATION_STATUS: test=t[%d]" % index,
                              "INSTRUMENTATION_STATUS: stack=first line", "second line",
                              "INSTRUMENTATION_STATUS_CODE: %d" % terminal])
        lines.extend(["INSTRUMENTATION_STATUS: class=C", "INSTRUMENTATION_STATUS: test=crash",
                      "INSTRUMENTATION_STATUS_CODE: 1", "INSTRUMENTATION_RESULT: shortMsg=Process crashed.", "INSTRUMENTATION_CODE: 0"])
        result = runner.instrumentation_records("\n".join(lines).encode())
        self.assertEqual([r["status"] for r in result], ["PASS", "FAIL", "FAIL", "SKIPPED", "SKIPPED", "BLOCKED"])

    def test_terminal_without_start_does_not_prove_execution(self):
        raw = b'INSTRUMENTATION_STATUS: class=C\nINSTRUMENTATION_STATUS: test=t\nINSTRUMENTATION_STATUS_CODE: 0\n'
        self.assertEqual(runner.instrumentation_records(raw)[0]["status"], "BLOCKED")


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="collector-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run = self.root / "autotesting-reports/run-fixture"
        path = self.run / "test-evidence/inputs/coverage.json"
        path.parent.mkdir(parents=True)
        self.data = {"version": 2, "project": {"root": str(self.root), "source_ref": "fixture-source"},
                     "run": {"id": self.run.name, "started_at": runner.now()}}
        path.write_text(json.dumps(self.data))

    def collect(self, code, eid="command-1", extra=(), command=None):
        args = [sys.executable, str(SCRIPTS / "record-test-run.py"), str(self.run), "--execution-id", eid,
                "--module", "app", "--variant", "debug", "--format", "junit-xml", "--results", "build/*.xml", *extra,
                "--", *(command if command is not None else [sys.executable, "-c", code])]
        return subprocess.run(args, cwd=self.root.parent, capture_output=True, text=True)

    def manifest(self, eid="command-1"):
        return json.loads((self.run / "test-evidence/checks/executions" / eid / "manifest.json").read_text())

    def writer(self, tail=""):
        return "from pathlib import Path; p=Path('build'); p.mkdir(exist_ok=True); (p/'a.xml').write_text('<testsuite><testcase classname=\"C\" name=\"t\"/></testsuite>'); " + tail

    def test_fresh_xml_logs_command_and_validator_reparse(self):
        result = self.collect(self.writer("print('fixture stdout')"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        reference = json.loads(result.stdout)
        self.data["executions"] = [{"id": reference["execution_id"], "manifest": reference["manifest"], "sha256": reference["sha256"]}]
        errors = []
        executions = runner.load_executions(self.data, self.run, lambda ok, message: (errors.append(message) or False) if not ok else True)
        self.assertEqual(errors, [])
        self.assertEqual(executions["command-1"]["records"][0]["status"], "PASS")
        manifest = self.manifest()
        self.assertEqual(manifest["working_directory"], str(self.root))
        self.assertEqual(manifest["exit_code"], 0)

    def test_existing_execution_is_immutable(self):
        self.collect(self.writer())
        first = (self.run / "test-evidence/checks/executions/command-1/manifest.json").read_bytes()
        result = self.collect(self.writer("print('changed')"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(first, (self.run / "test-evidence/checks/executions/command-1/manifest.json").read_bytes())

    def test_old_output_is_not_evidence_but_identical_rewrite_is_fresh(self):
        self.collect(self.writer())
        result = self.collect("print('UP-TO-DATE')", "command-2")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.manifest("command-2")["results"], [])
        result = self.collect(self.writer(), "command-3")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.manifest("command-3")["results"]), 1)

    def test_failed_command_keeps_completed_results_and_exit_code(self):
        result = self.collect(self.writer("import sys; sys.exit(7)"))
        self.assertEqual(result.returncode, 7)
        manifest = self.manifest()
        self.assertEqual(manifest["exit_code"], 7)
        self.assertEqual(manifest["results"][0]["status"], "PASS")

    def test_multiple_xml_files_are_collected_once(self):
        result = self.collect(self.writer("(p/'b.xml').write_text('<testsuite><testcase classname=\"C\" name=\"other\"/></testsuite>')"), extra=("--results", "build/a.xml"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(len(self.manifest()["results"]), 2)

    def test_timeout_and_command_start_failure_preserve_logs(self):
        result = self.collect("import time; print('before timeout', flush=True); time.sleep(10)", extra=("--timeout", "0.1"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("timeout", self.manifest()["collector_errors"])
        result = self.collect("", eid="missing", command=[str(self.root / "not-a-command")])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(self.manifest("missing")["exit_code"])

    def test_shell_characters_stay_literal_arguments(self):
        payload = '$(touch unwanted); `touch unwanted2`'
        result = self.collect("", command=[sys.executable, "-c", self.writer("import sys; print(sys.argv[1])"), payload])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / "unwanted").exists())
        self.assertFalse((self.root / "unwanted2").exists())

    def test_gradle_requires_explicit_fresh_execution_flags(self):
        result = self.collect("", command=["./gradlew", ":app:testDebugUnitTest"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("--rerun-tasks --no-build-cache", result.stdout)

    def test_instrumentation_records_serial_and_reads_only_new_stdout(self):
        protocol = 'INSTRUMENTATION_STATUS: class=C\nINSTRUMENTATION_STATUS: test=t\nINSTRUMENTATION_STATUS_CODE: 1\nINSTRUMENTATION_STATUS: class=C\nINSTRUMENTATION_STATUS: test=t\nINSTRUMENTATION_STATUS_CODE: 0\nINSTRUMENTATION_CODE: -1\n'
        result = self.collect("", extra=("--format", "instrumentation"), command=[sys.executable, "-c", "print(%r)" % protocol, "-s", "fixture-serial", "shell", "am", "instrument", "-w", "-r", "fixture.runner"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.manifest()["serial"], "fixture-serial")
        self.assertEqual(self.manifest()["results"][0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

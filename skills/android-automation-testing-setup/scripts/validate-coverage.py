#!/usr/bin/env python3
"""Validate coverage v1/v2; execution v2 includes a live production check (read-only)."""

import argparse
from collections import Counter
from datetime import datetime
import json
import importlib.util
from pathlib import Path
import re
import sys


def sibling(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = sibling("runner_evidence")


ARTIFACT = "test-evidence/inputs/coverage.json"
STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_TESTED"}
LAYERS = {"unit", "database", "ui", "navigation", "e2e", "screenshot"}
DEFINITION_FIELDS = ("id", "name", "module", "variant", "owner", "related_packages", "workflow_ids", "screens", "layer", "preconditions", "steps", "expected", "checkpoints")


def validate(data, run_dir, phase, baseline=None, baseline_dir=None):
    errors = []
    run_dir = Path(run_dir).resolve()

    def require(condition, message):
        if not condition:
            errors.append(message)
        return bool(condition)

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    def strings(value):
        return isinstance(value, list) and bool(value) and all(nonempty(x) for x in value)

    def index(rows, label):
        if not require(isinstance(rows, list), label + " must be an array"):
            return {}
        result = {}
        for row in rows:
            if not isinstance(row, dict) or not nonempty(row.get("id")):
                errors.append(label + " contains an item without an id")
                continue
            identifier = row["id"]
            require(identifier not in result, label + ": duplicate id " + identifier)
            result[identifier] = row
        return result

    def evidence(path, label):
        if not require(nonempty(path), label + ": missing evidence path"):
            return None
        candidate = (run_dir / path).resolve()
        try:
            candidate.relative_to(run_dir)
        except ValueError:
            errors.append(label + ": evidence escapes run directory")
            return None
        if not require(not Path(path).is_absolute() and candidate.is_file(), label + ": evidence file missing or absolute: " + path):
            return None
        require(candidate.stat().st_size > 0, label + ": evidence file is empty: " + path)
        return candidate

    version = data.get("version")
    require(version in {1, 2}, "version must be 1 or 2")
    require(not (version == 1 and phase == "execution"), "v1 execution is historical; create a new coverage v2 run")
    project = data.get("project", {})
    run = data.get("run", {})
    scope = data.get("scope", {})
    if not all(isinstance(x, dict) for x in (project, run, scope)):
        return {"valid": False, "errors": ["project/run/scope must be objects"]}
    for key in ("root", "application_id", "module", "variant", "source_ref", "branch", "skill_ref"):
        require(nonempty(project.get(key)), "project." + key + " is required")
    require(nonempty(run.get("id")), "run.id is required")
    require(run.get("mode") in {"TEST", "RETEST"}, "run.mode must be TEST or RETEST")
    if version == 2:
        require(run.get("id") == run_dir.name, "run.id must match run directory name")
        require(Path(project.get("root", "")).is_absolute(), "project.root must be absolute")
        try:
            run_start = runner.timestamp(run["started_at"])
            if phase == "execution" or run.get("ended_at"):
                require(runner.timestamp(run["ended_at"]) >= run_start, "invalid run time range")
        except (KeyError, TypeError, ValueError, AttributeError):
            errors.append("run requires ISO timestamps with timezone")
    executions = runner.load_executions(data, run_dir, require) if version == 2 else {}
    used_results = set()
    mapped_results = set()
    require(scope.get("kind") in {"full_app", "focused"}, "scope.kind must be full_app or focused")
    require(nonempty(scope.get("description")), "scope.description is required")
    require(scope.get("discovery_complete") is True, "discovery is incomplete")
    require(strings(scope.get("discovery_sources")), "scope.discovery_sources must identify inspected inputs")
    exclusions = scope.get("exclusions", [])
    require(isinstance(exclusions, list), "scope.exclusions must be an array")
    if isinstance(exclusions, list):
        for exclusion in exclusions:
            require(isinstance(exclusion, dict) and nonempty(exclusion.get("source_ref")) and nonempty(exclusion.get("reason")), "every scope exclusion needs source_ref and reason")
    packages = index(data.get("packages"), "packages")
    workflows = index(data.get("workflows"), "workflows")
    obligations = index(data.get("obligations"), "obligations")
    cases = index(data.get("cases"), "cases")
    require(bool(packages) and bool(workflows) and bool(cases), "packages, workflows and cases must be nonempty")
    for p in packages.values():
        label = "package " + p["id"]
        require(strings(p.get("source_refs")), label + ": missing source_refs")
        require(p.get("disposition") in {"covered", "not_applicable", "out_of_scope", "gap"}, label + ": invalid disposition")
        if p.get("disposition") != "covered":
            require(nonempty(p.get("reason")), label + ": missing reason")
            require(p.get("disposition") != "gap", label + ": unresolved coverage gap")
            if scope.get("kind") == "full_app":
                require(p.get("disposition") != "out_of_scope", label + ": cannot exclude an applicable package from full_app")
    covered_cases = set()
    applicable_obligations = []
    for obligation in obligations.values():
        label = "obligation " + obligation["id"]
        require(obligation.get("package_id") in packages, label + ": unknown package")
        require(obligation.get("workflow_id") in workflows, label + ": unknown workflow")
        require(nonempty(obligation.get("description")), label + ": missing description")
        require(isinstance(obligation.get("applicable"), bool), label + ": applicable must be boolean")
        ids = obligation.get("case_ids", [])
        require(isinstance(ids, list) and all(isinstance(x, str) for x in ids), label + ": invalid case_ids")
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            ids = []
        require(len(ids) == len(set(ids)), label + ": duplicate case_ids")
        if obligation.get("applicable") is True:
            applicable_obligations.append(obligation)
            require(nonempty(obligation.get("expected")), label + ": missing expected")
            require(bool(ids), label + ": unmapped behavioral branch")
        else:
            require(nonempty(obligation.get("reason")), label + ": missing applicability reason")
            require(not ids, label + ": inapplicable obligation must not count cases")
        for case_id in ids:
            require(case_id in cases, label + ": unknown testcase " + case_id)
            if case_id in cases:
                covered_cases.add(case_id)
                case = cases[case_id]
                require(obligation.get("package_id") in case.get("related_packages", []), label + ": testcase missing package mapping")
                require(obligation.get("workflow_id") in case.get("workflow_ids", []), label + ": testcase missing workflow mapping")
    require(bool(applicable_obligations), "no applicable obligations")
    for p in packages.values():
        if p.get("disposition") == "covered":
            require(any(o.get("package_id") == p["id"] for o in applicable_obligations), "package " + p["id"] + ": no applicable obligations")
    for workflow in workflows.values():
        label = "workflow " + workflow["id"]
        require(nonempty(workflow.get("name")) and strings(workflow.get("source_refs")), label + ": missing name/source_refs")
        require(workflow.get("kind") in {"screen", "multi_screen", "cross_package", "long"}, label + ": invalid kind")
        require(isinstance(workflow.get("screens"), list), label + ": screens must be an array")
        related = workflow.get("related_packages", [])
        require(strings(related) and all(p in packages for p in related), label + ": invalid related_packages")
        active = [o for o in applicable_obligations if o.get("workflow_id") == workflow["id"]]
        require(bool(active), label + ": no applicable obligations (move inactive features to explained exclusions)")
        if workflow.get("kind") != "screen" or len(workflow.get("screens", [])) > 1:
            journey_ids = {cid for o in active for cid in o.get("case_ids", [])}
            require(any(cases.get(cid, {}).get("owner") == {"kind": "workflow", "id": workflow["id"]} for cid in journey_ids), label + ": missing independently runnable journey testcase")
    counts = Counter()
    implemented = executed = 0
    image_paths = set()
    image_files = set()
    for case in cases.values():
        label = "case " + case["id"]
        require(re.fullmatch(r"AT-\d{3,}", case["id"]) is not None, label + ": invalid AT id")
        require(case["id"] in covered_cases, label + ": testcase has no applicable obligation")
        for key in ("name", "module", "variant", "preconditions", "expected"):
            require(nonempty(case.get(key)), label + ": missing " + key)
        require(strings(case.get("steps")), label + ": missing steps")
        require(case.get("layer") in LAYERS, label + ": invalid layer")
        related = case.get("related_packages", [])
        wids = case.get("workflow_ids", [])
        require(strings(related) and all(x in packages for x in related), label + ": invalid related_packages")
        require(strings(wids) and all(x in workflows for x in wids), label + ": invalid workflow_ids")
        owner = case.get("owner", {})
        require(isinstance(owner, dict) and owner.get("kind") in {"package", "workflow"}, label + ": exactly one primary owner is required")
        if not isinstance(owner, dict):
            owner = {}
        require(owner.get("id") in (related if owner.get("kind") == "package" else wids), label + ": owner does not match related mappings")
        screens = case.get("screens", [])
        require(isinstance(screens, list), label + ": screens must be an array")
        if isinstance(screens, list) and len(screens) > 1:
            require(owner.get("kind") == "workflow", label + ": multi-screen test must have workflow ownership")
        checkpoints = index(case.get("checkpoints", []), label + " checkpoints")
        for checkpoint in checkpoints.values():
            require(nonempty(checkpoint.get("action")) and nonempty(checkpoint.get("expected")), label + ": checkpoint missing action/expected")
        if owner.get("kind") == "workflow":
            require(len(checkpoints) >= 2, label + ": journey needs at least two behavioral checkpoints")
        automation = case.get("automation", {})
        result = case.get("result", {})
        if not require(isinstance(automation, dict) and isinstance(result, dict), label + ": invalid automation/result"):
            continue
        ready = automation.get("implemented") is True and nonempty(automation.get("symbol")) and nonempty(automation.get("source"))
        if ready:
            source = Path(automation["source"])
            def is_test_path(path):
                return not path.is_absolute() and ".." not in path.parts and any(
                    part == "src" and i + 1 < len(path.parts) and re.fullmatch(r"(?:test|androidTest|testFixtures)(?:[A-Z].*)?", path.parts[i + 1])
                    for i, part in enumerate(path.parts)
                )
            safe_test_path = is_test_path(source)
            source_file = Path(project.get("root", "")).resolve() / source
            try:
                safe_test_path = safe_test_path and is_test_path(source_file.resolve().relative_to(Path(project.get("root", "")).resolve()))
            except ValueError:
                safe_test_path = False
            require(safe_test_path, label + ": automation source must belong to a test source set")
            exists = source_file.is_file()
            require(exists, label + ": implemented test source file is missing")
            if owner.get("kind") == "workflow":
                require("workflows" in source.parts, label + ": journey test must be stored under workflows package")
            elif owner.get("kind") == "package" and nonempty(owner.get("id")):
                require("/" + owner["id"].replace(".", "/") + "/" in "/" + source.as_posix(), label + ": component test must mirror its production package")
            ready = ready and safe_test_path and exists
        implemented += int(ready)
        if phase != "design":
            require(ready, label + ": automation is not implemented")
        status = result.get("status")
        require(status in STATUSES, label + ": invalid result status")
        counts[status] += 1
        attempts = result.get("attempts", [])
        if not require(isinstance(attempts, list), label + ": attempts must be an array"):
            continue
        if status in {"BLOCKED", "NOT_TESTED"}:
            require(nonempty(result.get("reason")), label + ": missing incomplete-run reason")
        if status in {"PASS", "FAIL"}:
            executed += 1
            require(ready and bool(attempts), label + ": PASS/FAIL requires implemented test and attempts")
        if phase == "execution":
            require(status in {"PASS", "FAIL"}, label + ": execution is incomplete")
        attempt_ids = set()
        for attempt in attempts:
            if not require(isinstance(attempt, dict), label + ": invalid attempt"):
                continue
            aid = attempt.get("id")
            require(nonempty(aid) and aid not in attempt_ids, label + ": missing/duplicate attempt id")
            if not isinstance(aid, str):
                aid = "invalid"
            attempt_ids.add(aid)
            require(attempt.get("run_id") == run.get("id") and attempt.get("source_ref") == project.get("source_ref"), label + ": stale run/source evidence")
            require(attempt.get("module") == case.get("module") and attempt.get("variant") == case.get("variant"), label + ": runner module/variant does not match testcase")
            require(attempt.get("symbol") == automation.get("symbol"), label + ": result symbol does not match automation")
            require(attempt.get("status") in {"PASS", "FAIL"}, label + ": attempts record only completed runner cases")
            require(nonempty(attempt.get("actual")), label + ": attempt missing actual")
            if version == 2:
                reference = attempt.get("runner_result", {})
                if require(isinstance(reference, dict), label + ": runner_result is required"):
                    require(isinstance(reference.get("ordinal"), int) and not isinstance(reference.get("ordinal"), bool) and reference["ordinal"] > 0, label + ": runner ordinal must be a positive integer")
                    eid = reference.get("execution_id")
                    execution = executions.get(eid) if isinstance(eid, str) else None
                    require(execution is not None, label + ": unknown runner execution")
                    if execution:
                        manifest = execution["manifest"]
                        require(manifest.get("module") == case.get("module") and manifest.get("variant") == case.get("variant"), label + ": execution module/variant mismatch")
                        matches = [r for r in execution["records"] if all(r.get(k) == reference.get(k) for k in ("class_name", "test_name", "ordinal"))]
                        if require(len(matches) == 1, label + ": runner result missing or ambiguous"):
                            record = matches[0]
                            identity = (eid, record["class_name"], record["test_name"], record["ordinal"])
                            require(identity not in used_results, label + ": runner result reused")
                            used_results.add(identity)
                            mapped_results.add(identity)
                            require(record["status"] == attempt.get("status"), label + ": runner status mismatch (skipped/incomplete is not PASS)")
                            require(record["class_name"] + "." + record["test_name"] == automation.get("symbol"), label + ": runner symbol mismatch")
            try:
                start = datetime.fromisoformat(attempt["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(attempt["ended_at"].replace("Z", "+00:00"))
                require(start.tzinfo is not None and end.tzinfo is not None and end >= start, label + ": invalid attempt time range")
                if version == 2 and isinstance(attempt.get("runner_result"), dict):
                    execution = executions.get(attempt["runner_result"].get("execution_id"))
                    if execution:
                        manifest = execution["manifest"]
                        require(runner.timestamp(manifest["started_at"]) <= start <= end <= runner.timestamp(manifest["ended_at"]), label + ": attempt outside execution time")
            except (KeyError, TypeError, ValueError, AttributeError):
                errors.append(label + ": attempt requires ISO timestamps with timezone")
            paths = attempt.get("evidence", [])
            require(strings(paths), label + ": attempt needs runner evidence")
            if isinstance(paths, list):
                for path in paths:
                    evidence(path, label)
            if attempt.get("status") != "FAIL":
                continue
            shot = attempt.get("screenshot", {})
            if not require(isinstance(shot, dict), label + ": screenshot must be an object"):
                continue
            shot_status = shot.get("status")
            require(shot_status in {"captured", "unavailable", "not_applicable"}, label + ": failure needs screenshot disposition")
            if shot_status != "captured":
                require(nonempty(shot.get("reason")), label + ": missing screenshot reason")
                if case.get("layer") in {"ui", "navigation", "e2e", "screenshot"}:
                    require(shot_status == "unavailable", label + ": UI failure needs capture or an unavailable reason")
            else:
                images = shot.get("files", [])
                require(isinstance(images, list) and bool(images), label + ": screenshot files missing")
                for img in images if isinstance(images, list) else []:
                    if not require(isinstance(img, dict), label + ": invalid screenshot record"):
                        continue
                    path = img.get("path")
                    image_file = evidence(path, label)
                    try:
                        if not runner.identifier(aid):
                            raise ValueError("invalid attempt id")
                        expected_dir = run_dir / "test-evidence/screenshots" / case["id"] / aid
                        resolved = runner.local_file(run_dir, path, expected_dir)
                        stat = resolved.stat()
                        identity = (stat.st_dev, stat.st_ino)
                        require(resolved not in image_paths and identity not in image_files, label + ": screenshot reused across records")
                        image_paths.add(resolved)
                        image_files.add(identity)
                    except (OSError, ValueError, TypeError) as exc:
                        require(False, label + ": screenshot belongs to wrong case/attempt or unsafe path: " + str(exc))
                    if image_file:
                        require(image_file.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", label + ": screenshot is not PNG")
                    require(img.get("checkpoint_id") in checkpoints, label + ": unknown screenshot checkpoint")
                    require(img.get("timing") in {"failure", "before_crash", "after_crash"}, label + ": invalid screenshot timing")
                    require(nonempty(img.get("captured_at")), label + ": screenshot missing captured_at")
        completed = [a.get("status") for a in attempts if isinstance(a, dict)]
        if "FAIL" in completed:
            require(status == "FAIL", label + ": retry must not hide an earlier failure in this run")
        elif completed:
            require(status == "PASS", label + ": completed successful attempts must be reported PASS")
    if phase == "execution":
        # Every completed retry of a selected runner identity must be represented.
        for eid, execution in executions.items():
            manifest = execution["manifest"]
            selected = {c.get("automation", {}).get("symbol") for c in cases.values()
                        if c.get("module") == manifest.get("module") and c.get("variant") == manifest.get("variant")}
            for record in execution["records"]:
                key = (eid, record["class_name"], record["test_name"], record["ordinal"])
                if record["class_name"] + "." + record["test_name"] in selected and record["status"] in {"PASS", "FAIL"}:
                    require(key in mapped_results, "runner retry omitted from attempts")
        protection = data.get("production_guard", {})
        require(isinstance(protection, dict) and protection.get("unchanged") is True, "production protection check is missing or failed")
        if isinstance(protection, dict):
            before_path = evidence(protection.get("before"), "production_guard")
            after_path = evidence(protection.get("after"), "production_guard")
            if before_path and after_path:
                before = json.loads(before_path.read_text())
                after = json.loads(after_path.read_text())
                require(before.get("version") == after.get("version") == 1 and isinstance(before.get("files"), dict) and before == after and before.get("project_root") == project.get("root"), "production snapshots differ or belong to another project")
                try:
                    root = Path(project["root"]).resolve(strict=True)
                    if not root.is_dir():
                        raise ValueError("project root is not a directory")
                    changed = sibling("production-guard").check(root, before)
                    live_guard = {"checked_at": runner.now(), "unchanged": not changed, "changed_paths": changed}
                    require(not changed, "live production source changed: " + ", ".join(changed))
                except (OSError, ValueError, TypeError) as exc:
                    live_guard = {"checked_at": runner.now(), "unchanged": False, "error": str(exc)}
                    require(False, "live production guard failed: " + str(exc))
        changes = data.get("test_config_changes", [])
        require(isinstance(changes, list), "test_config_changes must be an array")
        for change in changes if isinstance(changes, list) else []:
            require(isinstance(change, dict) and nonempty(change.get("path")) and nonempty(change.get("reason")) and change.get("test_only_reviewed") is True, "test configuration changes need path/reason and test-only diff review")
    if run.get("mode") == "RETEST":
        require(isinstance(baseline, dict), "structured RETEST requires --baseline run directory")
        if isinstance(baseline, dict):
            require(baseline.get("version") in {1, 2} and baseline.get("run", {}).get("mode") == "TEST", "baseline must be a v1/v2 TEST artifact")
            require(run.get("id") != baseline.get("run", {}).get("id"), "RETEST must have a different run id")
            if baseline_dir is not None:
                require(Path(baseline_dir).resolve() != run_dir, "RETEST must have a different run directory")
            if version == 2:
                reference = data.get("baseline", {})
                try:
                    if not isinstance(reference, dict):
                        raise ValueError("baseline reference must be an object")
                    target = (run_dir / reference["run_dir"]).resolve(strict=True)
                    require(target != run_dir, "RETEST must have a different run directory")
                    if baseline_dir is not None:
                        require(target == Path(baseline_dir).resolve(), "baseline directory reference mismatch")
                    original = target / ARTIFACT
                    require(runner.digest(original) == reference.get("sha256"), "baseline artifact hash mismatch")
                    require(json.loads(original.read_text()) == baseline, "baseline artifact changed since reading")
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    require(False, "invalid baseline reference: " + str(exc))
            for key in ("root", "application_id", "module", "variant"):
                require(project.get(key) == baseline.get("project", {}).get(key), "baseline project mismatch: " + key)
            for key in ("scope", "packages", "workflows", "obligations"):
                require(data.get(key) == baseline.get(key), "baseline definitions changed: " + key)
            original_cases = index(baseline.get("cases"), "baseline cases")
            require(cases.keys() == original_cases.keys(), "baseline testcase IDs changed")
            for cid in cases.keys() & original_cases.keys():
                require(all(cases[cid].get(k) == original_cases[cid].get(k) for k in DEFINITION_FIELDS), cid + ": baseline testcase definition changed")
    summary = {"cases": len(cases), "obligations": len(applicable_obligations), "implemented": implemented, "executed": executed, "statuses": {s: counts[s] for s in sorted(STATUSES)}}
    if "summary" in data:
        require(data["summary"] == summary, "declared summary does not match unique inventory")
    output = {"valid": not errors, "phase": phase, "scope": scope.get("kind"), "summary": summary, "errors": errors}
    if phase == "execution":
        output["production_guard"] = locals().get("live_guard", {"checked_at": runner.now(), "unchanged": False, "error": "snapshots missing"})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--phase", required=True, choices=("design", "implementation", "execution"))
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads((args.run_dir / ARTIFACT).read_text())
        baseline = json.loads((args.baseline / ARTIFACT).read_text()) if args.baseline else None
        result = validate(data, args.run_dir, args.phase, baseline, args.baseline)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

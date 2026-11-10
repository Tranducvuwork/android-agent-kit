#!/usr/bin/env python3
"""Run a test command and preserve evidence without changing coverage definitions."""

import argparse
import glob
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys


spec = importlib.util.spec_from_file_location("runner_evidence", Path(__file__).with_name("runner_evidence.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def fingerprint(path):
    stat = path.stat()
    return {"device": stat.st_dev, "inode": stat.st_ino, "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns, "sha256": runner.digest(path)}


def result_files(root, patterns):
    paths = set()
    for pattern in patterns:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            raise ValueError("result patterns must be relative to project root")
        for value in glob.glob(str(root / pattern), recursive=True):
            path = Path(value)
            if path.is_file():
                paths.add(runner.local_file(root, str(path.relative_to(root))))
    return sorted(paths)


def record(args, command):
    run_dir = args.run_dir.resolve(strict=True)
    data = json.loads((run_dir / "test-evidence/inputs/coverage.json").read_text())
    root = Path(data["project"]["root"]).resolve(strict=True)
    if data["version"] != 2 or data["run"]["id"] != run_dir.name or not root.is_dir():
        raise ValueError("collector requires coverage v2, matching run directory and project root")
    if not runner.identifier(args.execution_id) or not command:
        raise ValueError("path-safe execution ID and command after -- are required")
    runner.timestamp(data["run"]["started_at"])
    if args.format == "junit-xml" and not args.results:
        raise ValueError("JUnit XML requires --results")
    if args.format == "junit-xml" and any(Path(x).name in {"gradle", "gradlew", "gradle.bat", "gradlew.bat"} for x in command):
        if "--rerun-tasks" not in command or "--no-build-cache" not in command:
            raise ValueError("Gradle evidence requires --rerun-tasks --no-build-cache")
    if args.format == "instrumentation":
        # Require an explicit device and raw am instrument output, not a Gradle console.
        if "-s" not in command or command.count("-s") != 1:
            raise ValueError("instrumentation command requires adb -s SERIAL")
        offset = command.index("-s")
        if offset + 1 >= len(command) or not command[offset + 1] or "instrument" not in command or "-r" not in command:
            raise ValueError("use adb -s SERIAL shell am instrument -w -r ...")
        serial = command[offset + 1]
    else:
        serial = None
    before = {str(p): fingerprint(p) for p in result_files(root, args.results)}
    relative = Path("test-evidence/checks/executions") / args.execution_id
    directory = run_dir / relative
    directory.parent.mkdir(parents=True, exist_ok=True)
    if directory.parent.resolve() != directory.parent or directory.parent.is_symlink():
        raise ValueError("execution directory must not traverse symlinks")
    directory.mkdir()  # exclusive: never replace another execution
    manifest = {"version": 1, "id": args.execution_id, "run_id": data["run"]["id"],
                "source_ref": data["project"]["source_ref"], "project_root": str(root),
                "module": args.module, "variant": args.variant, "format": args.format,
                "command": command, "working_directory": str(root), "serial": serial,
                "started_at": runner.now(), "exit_code": None, "collector_errors": [], "files": []}
    process = None
    with (directory / "stdout.txt").open("wb") as out, (directory / "stderr.txt").open("wb") as err:
        try:
            process = subprocess.Popen(command, cwd=root, stdout=out, stderr=err, start_new_session=True)
            try:
                manifest["exit_code"] = process.wait(timeout=args.timeout)
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                manifest["exit_code"] = process.returncode
                manifest["collector_errors"].append("timeout" if isinstance(exc, subprocess.TimeoutExpired) else "interrupted")
        except OSError as exc:
            manifest["collector_errors"].append("command did not start: " + str(exc))
    manifest["ended_at"] = runner.now()
    for role in ("stdout", "stderr"):
        path = directory / (role + ".txt")
        manifest["files"].append({"path": str(path.relative_to(run_dir)), "role": role, "sha256": runner.digest(path)})
    try:
        for index, path in enumerate(result_files(root, args.results)):
            after = fingerprint(path)
            previous = before.get(str(path))
            if previous == after:
                continue
            target = directory / ("result-%04d.xml" % index)
            content = path.read_bytes()
            target.write_bytes(content)
            if runner.digest(target) != after["sha256"] or fingerprint(path) != after:
                raise ValueError("runner result changed while collecting: " + str(path))
            manifest["files"].append({"path": str(target.relative_to(run_dir)), "role": "result",
                                      "sha256": runner.digest(target), "original": str(path.relative_to(root)),
                                      "before": previous, "after": after})
        sources = [entry for entry in manifest["files"] if entry["role"] == ("result" if args.format == "junit-xml" else "stdout")]
        if not sources:
            manifest["collector_errors"].append("no fresh runner results; cached/up-to-date output is not execution evidence")
        manifest["results"] = runner.parse_results(args.format, [(e["path"], (run_dir / e["path"]).read_bytes()) for e in sources])
    except (OSError, ValueError, TypeError, runner.ET.ParseError) as exc:
        manifest["collector_errors"].append(str(exc))
    (directory / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"execution_id": args.execution_id, "manifest": str(relative / "manifest.json"),
                      "sha256": runner.digest(directory / "manifest.json"),
                      "exit_code": manifest["exit_code"], "collector_errors": manifest["collector_errors"]}, ensure_ascii=False))
    return 2 if manifest["collector_errors"] else (manifest["exit_code"] if manifest["exit_code"] >= 0 else 128 - manifest["exit_code"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--format", required=True, choices=("junit-xml", "instrumentation"))
    parser.add_argument("--results", action="append", default=[])
    parser.add_argument("--timeout", type=float)
    raw = sys.argv[1:]
    split = raw.index("--") if "--" in raw else len(raw)
    args = parser.parse_args(raw[:split])
    try:
        if args.timeout is not None and args.timeout <= 0:
            raise ValueError("timeout must be positive")
        return record(args, raw[split + 1:])
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({"collector_error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())

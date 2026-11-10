"""Shared runner protocol and evidence utilities (Python 3.9+, standard library)."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return parsed


def digest(path):
    with Path(path).open("rb") as stream:
        result = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]+", value) is not None


def local_file(root, value, within=None):
    """Resolve a relative file, rejecting traversal, symlinks and escaped parents."""
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError("unsafe evidence path")
    root = Path(root).resolve()
    candidate = root / value
    for parent in (candidate, *candidate.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("symlink in evidence path")
    resolved = candidate.resolve(strict=True)
    resolved.relative_to(root)
    if within is not None:
        resolved.relative_to(Path(within))
    if not resolved.is_file():
        raise ValueError("evidence is not a file")
    return resolved


def junit_records(content):
    root = ET.fromstring(content)
    tag = lambda element: element.tag.rsplit("}", 1)[-1]
    if tag(root) not in {"testsuite", "testsuites"}:
        raise ValueError("expected JUnit testsuite/testsuites")
    records = []
    for case in root.iter():
        if tag(case) != "testcase":
            continue
        class_name, name = case.get("classname"), case.get("name")
        if not class_name or not name:
            raise ValueError("JUnit testcase requires classname and full name")
        children = list(case)
        for child in children:
            if tag(child) in {"flakyFailure", "flakyError", "rerunFailure", "rerunError"}:
                records.append({"class_name": class_name, "test_name": name, "status": "FAIL"})
        status = "FAIL" if any(tag(c) in {"failure", "error"} for c in children) else (
            "SKIPPED" if any(tag(c) == "skipped" for c in children) else "PASS")
        records.append({"class_name": class_name, "test_name": name, "status": status})
    return records


def instrumentation_records(content):
    records, bundle, active = [], {}, None
    last_key = None
    for line in content.decode("utf-8", errors="replace").splitlines():
        if line.startswith("INSTRUMENTATION_STATUS: "):
            key, sep, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            if sep:
                bundle[key], last_key = value, key
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = int(line.partition(": ")[2])
            identity = (bundle.get("class"), bundle.get("test"))
            if not all(identity) and active:
                identity = active
            if code == 1 and all(identity):
                if active:
                    records.append({"class_name": active[0], "test_name": active[1], "status": "BLOCKED"})
                active = identity
            elif code in {0, -1, -2, -3, -4} and all(identity):
                if active and active != identity:
                    records.append({"class_name": active[0], "test_name": active[1], "status": "BLOCKED"})
                status = "SKIPPED" if code in {-3, -4} else ("PASS" if code == 0 else "FAIL")
                if code not in {-3, -4} and active != identity:
                    status = "BLOCKED"
                records.append({"class_name": identity[0], "test_name": identity[1], "status": status})
                active = None
            bundle, last_key = {}, None
        elif line.startswith("INSTRUMENTATION_"):
            last_key = None
        elif last_key:
            bundle[last_key] += "\n" + line
    if active:
        records.append({"class_name": active[0], "test_name": active[1], "status": "BLOCKED"})
    return records


def parse_results(format_name, files):
    """Files are ordered (relative path, raw bytes); ordinal includes retries."""
    counts, records = Counter(), []
    for path, content in files:
        parsed = junit_records(content) if format_name == "junit-xml" else instrumentation_records(content)
        for record in parsed:
            key = record["class_name"], record["test_name"]
            counts[key] += 1
            records.append(dict(record, ordinal=counts[key], raw=path))
    return records


def load_executions(data, run_dir, require):
    """Reparse hashed raw files; normalized results in manifests are never trusted."""
    executions, seen_files = {}, set()
    rows = data.get("executions", [])
    if not require(isinstance(rows, list), "executions must be an array"):
        return executions
    registered = {r.get("id") for r in rows if isinstance(r, dict) and identifier(r.get("id"))}
    directory = run_dir / "test-evidence/checks/executions"
    if directory.exists():
        for child in directory.iterdir():
            require(not child.is_dir() or child.name in registered, "unregistered execution: " + child.name)
    for row in rows:
        try:
            if not isinstance(row, dict) or not identifier(row.get("id")):
                raise ValueError("execution needs path-safe id")
            eid = row["id"]
            if eid in executions:
                raise ValueError("duplicate execution id")
            directory = run_dir / "test-evidence/checks/executions" / eid
            path = local_file(run_dir, row.get("manifest"), directory)
            if path != directory / "manifest.json" or digest(path) != row.get("sha256"):
                raise ValueError("execution manifest path/hash mismatch")
            manifest = json.loads(path.read_text())
            project, run = data["project"], data["run"]
            if not (manifest.get("version") == 1 and manifest.get("id") == eid
                    and manifest.get("run_id") == run.get("id")
                    and manifest.get("source_ref") == project.get("source_ref")
                    and manifest.get("project_root") == project.get("root")
                    and manifest.get("working_directory") == project.get("root")):
                raise ValueError("execution has stale run/source/project evidence")
            begin, end = timestamp(manifest["started_at"]), timestamp(manifest["ended_at"])
            if not (timestamp(run["started_at"]) <= begin <= end):
                raise ValueError("execution time outside run")
            if run.get("ended_at") and end > timestamp(run["ended_at"]):
                raise ValueError("execution time outside run")
            command, format_name = manifest.get("command"), manifest.get("format")
            if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
                raise ValueError("execution command is required")
            if any(Path(x).name in {"gradle", "gradlew", "gradle.bat", "gradlew.bat"} for x in command):
                if "--rerun-tasks" not in command or "--no-build-cache" not in command:
                    raise ValueError("Gradle evidence requires --rerun-tasks --no-build-cache")
            if format_name not in {"junit-xml", "instrumentation"}:
                raise ValueError("unsupported runner format")
            if format_name == "instrumentation":
                offset = command.index("-s")
                if not manifest.get("serial") or command[offset + 1] != manifest["serial"] or "-r" not in command or "instrument" not in command:
                    raise ValueError("instrumentation requires matching explicit serial and raw protocol")
            if manifest.get("exit_code") is not None and (not isinstance(manifest["exit_code"], int) or isinstance(manifest["exit_code"], bool)):
                raise ValueError("invalid command exit code")
            entries = manifest.get("files")
            if not isinstance(entries, list):
                raise ValueError("execution files must be an array")
            sources, roles = [], Counter()
            for entry in entries:
                raw = local_file(run_dir, entry["path"], directory)
                identity = raw.stat().st_dev, raw.stat().st_ino
                if identity in seen_files:
                    raise ValueError("execution raw file reused")
                seen_files.add(identity)
                if digest(raw) != entry.get("sha256"):
                    raise ValueError("runner evidence hash mismatch")
                role = entry.get("role")
                if role not in {"stdout", "stderr", "result"}:
                    raise ValueError("invalid execution file role")
                roles[role] += 1
                if role == "result":
                    before, after = entry.get("before"), entry.get("after")
                    if not isinstance(after, dict) or before == after or after.get("sha256") != entry["sha256"]:
                        raise ValueError("runner result is stale or lacks collection fingerprint")
                if role == ("result" if format_name == "junit-xml" else "stdout"):
                    sources.append((entry["path"], raw.read_bytes()))
            if roles["stdout"] != 1 or roles["stderr"] != 1:
                raise ValueError("execution requires one stdout and stderr")
            records = parse_results(format_name, sources)
            executions[eid] = {"manifest": manifest, "records": records}
        except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError, ET.ParseError) as exc:
            require(False, "execution: " + str(exc))
    return executions

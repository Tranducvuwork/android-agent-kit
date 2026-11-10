#!/usr/bin/env python3
"""Snapshot/check production inputs without editing the Android project (Python 3.9+)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys


SKIP_DIRS = {".git", ".gradle", ".idea", ".kotlin", "build", "autotesting-reports", "qa-reports", "node_modules", ".agents", ".claude", ".cursor"}
TEST_SETS = {"test", "androidTest", "testFixtures"}


def snapshot(root):
    """Hash production source sets, plus non-test code outside conventional source sets."""
    files = {}
    for directory, directories, filenames in os.walk(root):
        relative_directory = Path(directory).relative_to(root)
        if "src" not in relative_directory.parts:
            directories[:] = [name for name in directories if name not in SKIP_DIRS]
        if relative_directory.name == "src":
            directories[:] = [name for name in directories if name not in TEST_SETS and not re.fullmatch(r"(?:test|androidTest)[A-Z].*", name)]
        for name in directories:
            if (Path(directory) / name).is_symlink():
                raise ValueError("Symlinked directory needs an explicit resolved production snapshot: " + str(Path(directory) / name))
        for filename in filenames:
            path = Path(directory) / filename
            relative = path.relative_to(root)
            parts = relative.parts
            if "src" in parts:
                source_index = parts.index("src") + 1
                source_set = parts[source_index] if source_index < len(parts) else ""
                if source_set in TEST_SETS or re.fullmatch(r"(?:test|androidTest)[A-Z].*", source_set):
                    continue
                protected = True
            else:
                protected = path.suffix.lower() in {".kt", ".java", ".xml", ".aidl", ".c", ".cpp", ".h", ".so", ".jar", ".aar"}
            if not protected:
                continue
            # Hash bytes through symlinks as well; target changes must be detected.
            files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"version": 1, "project_root": str(root), "files": files}


def check(root, before):
    if before.get("version") != 1 or before.get("project_root") != str(root):
        raise ValueError("Snapshot version/project_root does not match")
    previous = before.get("files")
    if not isinstance(previous, dict):
        raise ValueError("Snapshot files must be an object")
    current = snapshot(root)["files"]
    return sorted(p for p in previous.keys() | current.keys() if previous.get(p) != current.get(p))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("snapshot", "check"))
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--snapshot", type=Path, help="required for check; snapshot prints JSON to stdout")
    args = parser.parse_args()
    try:
        root = args.project_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("project_root must be a directory")
        if args.action == "snapshot":
            result = snapshot(root)
            code = 0
        else:
            if args.snapshot is None:
                raise ValueError("check requires --snapshot")
            changed = check(root, json.loads(args.snapshot.read_text()))
            result = {"unchanged": not changed, "changed_paths": changed}
            code = 1 if changed else 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

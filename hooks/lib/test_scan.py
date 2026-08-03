#!/usr/bin/env python3
"""Self-check for hooks/lib/scan.py — shared changed-file scanning."""
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scan as _scan

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)

    # recent source file -> found
    (d / "mod.py").write_text("x=1\n")
    # old source file -> not found
    old = d / "old.py"
    old.write_text("x=1\n")
    past = time.time() - 6000
    os.utime(old, (past, past))
    # non-source -> never found
    (d / "notes.md").write_text("hi\n")
    # skipped dir -> not walked
    (d / "node_modules").mkdir()
    (d / "node_modules" / "dep.py").write_text("x=1\n")
    # skip_names -> skipped
    (d / "test_mod.py").write_text("x=1\n")

    found = _scan.changed_files(d)
    names = {p.name for _, p in found}
    check("recent source found", "mod.py" in names)
    check("old source skipped", "old.py" not in names)
    check("non-source skipped", "notes.md" not in names)
    check("skip-dir skipped", "dep.py" not in names)

    found = _scan.changed_files(d, skip_names=("test_",))
    names = {p.name for _, p in found}
    check("skip_names works", "test_mod.py" not in names)

    # bad cwd -> empty (fail-open)
    check("bad cwd fail-open", _scan.changed_files(d / "nope") == [])

print(f"OK: {PASS} assertions passed")

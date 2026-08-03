#!/usr/bin/env python3
"""Self-check for understand-guard.py — read-before-write nudge."""
import importlib.util
import json
import os
import tempfile
import time
from pathlib import Path

_spec = importlib.util.spec_from_file_location("ug", Path(__file__).parent / "understand-guard.py")
_ug = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ug)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def run(tool, target):
    """Run main() with a payload; capture stdout as the nudge."""
    import io
    from contextlib import redirect_stdout
    payload = {"tool_name": tool, "tool_input": {"file_path": str(target)}}
    os.environ["HOOK_INPUT"] = json.dumps(payload)
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            _ug.main()
        except SystemExit:
            pass
    return buf.getvalue()


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)

    # old file (stale mtime) -> nudge
    old = d / "old.py"
    old.write_text("x=1\n")
    past = time.time() - 6000  # 100 min old
    os.utime(old, (past, past))
    out = run("Edit", old)
    check("old file nudges", "Understand-floor" in out)

    # fresh file -> silent
    fresh = d / "fresh.py"
    fresh.write_text("x=1\n")
    out = run("Edit", fresh)
    check("fresh file silent", "Understand-floor" not in out)

    # new file -> silent (create-new is legit blind)
    new = d / "new.py"
    out = run("Write", new)
    check("new file silent", "Understand-floor" not in out)

    # non-Edit tool -> silent
    out = run("Bash", old)
    check("Bash tool silent", "Understand-floor" not in out)

print(f"OK: {PASS} assertions passed")

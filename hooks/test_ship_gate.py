#!/usr/bin/env python3
"""Self-check for ship-gate.py scanner."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("ship_gate", Path(__file__).parent / "ship-gate.py")
_sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sg)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def scan_content(content, suffix=".py"):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / f"file{suffix}"
        p.write_text(content, encoding="utf-8")
        return _sg.scan_file(p, Path(f"file{suffix}"))


# --- should FLAG ---
check("TODO flagged", len(scan_content("# TODO: implement this\nx=1")) > 0)
check("FIXME flagged", len(scan_content("# FIXME: remove this\nx=1")) > 0)
check("console.log flagged (js)", any("console.log" in f for f in scan_content("console.log('hi')\n", ".js")))
check("empty except flagged (py)", len(scan_content("try:\n    pass\nexcept:\n    pass\n")) > 0)
check("empty catch flagged (js)", any("empty catch" in f for f in scan_content("try {} catch (e) {}\n", ".js")))

# --- should NOT flag ---
check("clean py passes", scan_content("def add(a,b):\n    return a+b\n") == [])
check("comment-only passes", scan_content("# a normal comment\n# another\nx=1\n") == [])
check("no false TODO in url", scan_content("# see http://example.com/todo\nx=1\n") == [])

print(f"OK: {PASS} assertions passed")

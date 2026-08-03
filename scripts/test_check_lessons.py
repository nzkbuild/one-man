#!/usr/bin/env python3
"""Self-check for scripts/check-lessons.py — recurrence detection."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("cl", Path(__file__).parent / "check-lessons.py")
_cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cl)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def run_with(lessons_dir):
    """Point the module at a fixture ledger, run check(); return problems."""
    _cl.LESSONS_DIR = Path(lessons_dir)
    return _cl.check()


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)

    # empty -> clean
    check("empty ledger clean", run_with(d) == [])

    # at-risk untested -> detected
    (d / "a.json").write_text(
        '{"violation": "test isolation gap", "recurrence_risk": "high", '
        '"tested": false, "layer": "regression-test"}', encoding="utf-8")
    probs = run_with(d)
    check("high-risk untested detected", any("at-risk" in p for p in probs))

    # tested with broken test_ref -> detected
    (d / "b.json").write_text(
        '{"violation": "version bump", "recurrence_risk": "high", '
        '"tested": true, "test_ref": "nope_does_not_exist.py"}', encoding="utf-8")
    probs = run_with(d)
    check("broken prevention detected", any("prevention broken" in p for p in probs))

    # tested with valid test_ref -> silent (isolate: clear prior files)
    (d / "b.json").unlink()
    (d / "a.json").unlink()
    (d / "c.json").write_text(
        '{"violation": "ok", "recurrence_risk": "high", "tested": true, '
        '"test_ref": "scripts/test_check_lessons.py"}', encoding="utf-8")
    probs = run_with(d)
    check("valid test_ref silent", not any("prevention broken" in p for p in probs))

    # medium-risk untested -> NOT flagged (only high matters)
    (d / "d.json").write_text(
        '{"violation": "medium thing", "recurrence_risk": "medium", '
        '"tested": false}', encoding="utf-8")
    probs = run_with(d)
    check("medium untested not flagged", not any("medium thing" in p for p in probs))

# missing dir -> clean (fail-open)
check("missing dir clean", run_with("/nonexistent/path/xyz") == [])

print(f"OK: {PASS} assertions passed")

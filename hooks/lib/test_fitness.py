#!/usr/bin/env python3
"""Self-check for hooks/lib/fitness.py (v1.6.0 M2)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fitness as _ft

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _ft.FITNESS_DIR = Path(tmp)

    # record outcomes
    _ft.record("danger-guard", "applied")
    _ft.record("danger-guard", "applied")
    _ft.record("danger-guard", "success")
    d = _ft._read("danger-guard")
    check("applications counted", d["applications"] == 2)
    check("success counted", d["successes"] == 1)

    # healthy: low friction
    check("healthy verdict", _ft.verdict("danger-guard") == "healthy")

    # watch: high override/false-positive rate
    _ft.record("perf-guard", "applied")
    _ft.record("perf-guard", "override")
    check("watch verdict", _ft.verdict("perf-guard") == "watch")

    # zombie: never applied
    check("zombie verdict", _ft.verdict("unused-policy") == "zombie")

    # report shape
    rep = _ft.report()
    check("report has entries", len(rep) >= 2)
    check("report one-line each", all("\n" not in r for r in rep))

print(f"OK: {PASS} assertions passed")

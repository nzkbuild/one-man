#!/usr/bin/env python3
"""Self-check for hooks/lib/controls.py — control criticality declaration."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import controls as _ctl

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


# 1. reads the repo declaration (safety/quality/advisory present)
check("danger-guard is safety", _ctl.criticality("danger-guard") == "safety")
check("ship-gate is quality", _ctl.criticality("ship-gate") == "quality")
check("perf-guard is advisory", _ctl.criticality("perf-guard") == "advisory")

# 2. unknown control -> advisory default
check("unknown defaults advisory", _ctl.criticality("nope") == "advisory")

# 3. user override file wins
with tempfile.TemporaryDirectory() as tmp:
    _ctl.USER_CONTROLS = Path(tmp) / "one-man.controls.json"
    _ctl.USER_CONTROLS.write_text(
        '{"controls": {"danger-guard": {"criticality": "quality"}}}', encoding="utf-8")
    check("user override wins", _ctl.criticality("danger-guard") == "quality")

# 4. fail-closed toggle
os.environ.pop("ONE_MAN_FAIL_CLOSED", None)
check("fail-closed off by default", not _ctl.fail_closed_enabled())
os.environ["ONE_MAN_FAIL_CLOSED"] = "1"
check("fail-closed on with env", _ctl.fail_closed_enabled())

# 5. broken USER config -> falls through to valid repo declaration
with tempfile.TemporaryDirectory() as tmp:
    _ctl.USER_CONTROLS = Path(tmp) / "one-man.controls.json"
    _ctl.USER_CONTROLS.write_text("{broken json", encoding="utf-8")
    check("broken user config uses repo declaration", _ctl.criticality("danger-guard") == "safety")

print(f"OK: {PASS} assertions passed")

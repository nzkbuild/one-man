#!/usr/bin/env python3
"""Self-check for plan-validator.py (v1.7.0 M5).

A plan is rejected or repaired when policy provides a deterministic
correction: missing deps, wrong ordering, missing baseline repair,
missing rollback, unbounded scope, weak acceptance.
"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import assignment as _as
_spec = importlib.util.spec_from_file_location("plan_validator", Path(__file__).parent / "plan-validator.py")
_pv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pv)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


BASE_DIRTY = {"git": {"dirty": True}, "tests": {"passing": None},
              "unfinished": [], "debt_drift": {"debt": 0, "drift": 0}}
BASE_CLEAN = {"git": {"dirty": False}, "tests": {"passing": None},
              "unfinished": [], "debt_drift": {"debt": 0, "drift": 0}}

# valid plan: clean baseline brownfield -> no findings
b = _as.synthesize("brownfield", BASE_CLEAN, {"type": "feature"})
ok, findings, repairs = _pv.validate(b, BASE_CLEAN)
check("clean brownfield valid", ok is True)

# synthesized brownfield already has baseline-first -> VALID even when dirty
b_dirty = _as.synthesize("brownfield", BASE_DIRTY, {"type": "feature"})
ok, findings, repairs = _pv.validate(b_dirty, BASE_DIRTY)
check("synthesized brownfield valid (baseline-first built-in)", ok is True)

# a plan that LACKS baseline/repair on a dirty repo IS flagged + repaired
broken_plan = {"situation": "brownfield", "workstreams": ["extend", "verify"],
               "non_goals": ["no x"], "acceptance": ["suite green"],
               "scope": "x", "verified_state": {"dirty": True}}
ok, findings, repairs = _pv.validate(broken_plan, BASE_DIRTY)
check("dirty repo without repair flagged", not ok)
check("repair suggested", any("repair" in r for r in repairs))

# migration -> must have rollback
m = _as.synthesize("migration", BASE_CLEAN, {"type": "chore"})
ok, findings, repairs = _pv.validate(m, BASE_CLEAN)
check("migration needs rollback", any("rollback" in f for f in findings))
check("rollback repair offered", any("rollback" in r for r in repairs))

# refactor -> rollback + no-behavior-change preserved
r = _as.synthesize("refactor", BASE_CLEAN, {"type": "refactor"})
ok, findings, repairs = _pv.validate(r, BASE_CLEAN)
check("refactor has acceptance", any("behavior change" in a for a in r["acceptance"]))

# empty plan -> rejected
bad = {"situation": "brownfield", "workstreams": [], "non_goals": [],
       "acceptance": [], "scope": "x", "verified_state": {}}
ok, findings, _ = _pv.validate(bad, BASE_CLEAN)
check("empty plan rejected", not ok)

# weak acceptance -> flagged
weak = {"situation": "feature", "workstreams": ["core"], "non_goals": ["no x"],
        "acceptance": ["works end-to-end"], "scope": "x", "verified_state": {}}
ok, findings, _ = _pv.validate(weak, BASE_CLEAN)
check("weak acceptance flagged", not ok)

print(f"OK: {PASS} assertions passed")

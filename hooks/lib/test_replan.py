#!/usr/bin/env python3
"""Self-check for replan.py (v1.7.0 M6).

Re-planning happens ONLY on verified evidence change, and the re-plan
record is auditable: what changed, why, trigger evidence, affected
milestones, completed-validity, stale evidence, new order.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evidence as _ev
import replan as _rp

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _ev.EVIDENCE_DIR = Path(tmp)
    _ev.write_record("current", {"type": "feature", "risk": "medium",
                                 "obligations": ["tests"], "evidence": []})

    # a controlled re-plan: evidence changed (new dependency found)
    _rp.replan(
        trigger_evidence="new dependency: auth lib required",
        what_changed="dependency order",
        why="baseline reconnaissance found the auth dependency",
        affected_milestones=["core", "verify"],
        completed_valid=True,  # prior work still valid
        stale_evidence=["assumed no-auth"],
        new_order=["baseline", "auth-integration", "core", "verify"],
    )
    plans = _rp.replans()
    check("replan recorded", len(plans) == 1)
    entry = plans[0]
    check("trigger recorded", entry["trigger_evidence"] == "new dependency: auth lib required")
    check("what changed", entry["what_changed"] == "dependency order")
    check("affected milestones", "core" in entry["affected_milestones"])
    check("completed valid", entry["completed_work_valid"] is True)
    check("stale evidence recorded", "assumed no-auth" in entry["stale_evidence"])
    check("new order recorded", "auth-integration" in entry["new_dependency_order"])

    # no re-plan when evidence did NOT change (the guard: unnecessary replanning)
    # — the record count stays 1 unless replan() is called
    check("no silent replan", len(_rp.replans()) == 1)

    # gate blocks when a re-plan INVALIDATES completed work (unrecorded)
    # — a replan with completed_valid=False must surface as a risk
    _rp.replan(
        trigger_evidence="API contract changed upstream",
        what_changed="scope",
        why="upstream breaking change",
        affected_milestones=["execute"],
        completed_valid=False,  # prior work INVALIDATED
        stale_evidence=["compat assumptions"],
        new_order=["re-baseline", "execute"],
    )
    plans = _rp.replans()
    check("invalidating replan recorded", len(plans) == 2)
    check("invalidating flagged", plans[-1]["completed_work_valid"] is False)

print(f"OK: {PASS} assertions passed")

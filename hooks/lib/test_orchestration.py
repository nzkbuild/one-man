#!/usr/bin/env python3
"""Self-check for orchestration.py (v1.7.0 M4).

Proves the capability contract: selected with reason, executed, output
produced, output consumed, obligation satisfied, evidence current.
A capability that runs but produces no consumed value does NOT count.
"""
import io
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evidence as _ev
import orchestration as _or

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _ev.EVIDENCE_DIR = Path(tmp)
    _ev.write_record("current", {"type": "bug", "risk": "high",
                                 "obligations": ["regression test"], "evidence": []})

    # full contract: capability selected, executed, output consumed, satisfied
    f = Path(tmp) / "app.py"
    f.write_text("x=1\n")
    _or.record(capability="systematic-debugging", obligation="reproduce bug",
               reason="high-risk bug needs root-cause before fix",
               executed=True, output="stack trace captured", consumer="fix step",
               satisfied=True, files=[str(f)])
    rec = _ev.read_record("current")
    entry = rec["evidence"][-1]
    check("reason recorded", entry["reason_selected"] == "high-risk bug needs root-cause before fix")
    check("output recorded", entry["output"] == "stack trace captured")
    check("consumer recorded", entry["output_consumer"] == "fix step")
    check("satisfied recorded", entry["obligation_satisfied"] is True)
    check("evidence current", entry["evidence_current"] is True)

    # unsatisfied: no unsatisfied records yet
    check("no unsatisfied", _or.unsatisfied() == [])

    # a FAILED obligation surfaces
    _or.record(capability="verify-turn", obligation="suite passes",
               reason="done requires green suite", executed=True,
               output="3 failed tests", consumer="fix step",
               satisfied=False, files=[str(f)])
    unsat = _or.unsatisfied()
    check("unsatisfied detected", len(unsat) == 1)

    # unconsumed: a capability that ran but no consumer -> ceremony
    _or.record(capability="brandkit", obligation="design chain",
               reason="design task", executed=True,
               output="brand guidance", consumer=None,
               satisfied=True, files=[str(f)])
    uncon = _or.unconsumed()
    check("unconsumed (ceremony) detected", any("brandkit" in u.get("capability", "") for u in uncon))

    # the gate should block on unsatisfied obligations (M4 proof)
    import gate as _gate
    buf = io.StringIO()
    with redirect_stderr(buf):
        try:
            _gate.main()
            code = 0
        except SystemExit as e:
            code = e.code
    check("gate blocks on unsatisfied obligation", code == 2)

print(f"OK: {PASS} assertions passed")

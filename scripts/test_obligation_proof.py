#!/usr/bin/env python3
"""Self-check for v1.7.0 M2 — capability obligation proof.

The obligation is satisfied ONLY when a real capability produced passing
evidence for it. Untied evidence (no capability) must NOT satisfy.
"""
import io
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

# Import evidence ONCE so gate.py's internal `import evidence` resolves to the
# SAME instance — re-pointing EVIDENCE_DIR then affects both.
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "lib"))
import evidence as _ev  # noqa: E402

import importlib.util
_gate_spec = importlib.util.spec_from_file_location("gate", Path(__file__).parent.parent / "hooks" / "lib" / "gate.py")
_gate = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(_gate)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def gate_exit(evidence_dir):
    """Run the gate against the record in evidence_dir; return exit code."""
    _ev.EVIDENCE_DIR = evidence_dir
    buf = io.StringIO()
    with redirect_stderr(buf):
        try:
            _gate.main()
            return 0, buf.getvalue()
        except SystemExit as e:
            return e.code, buf.getvalue()


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    _ev.EVIDENCE_DIR = d

    # high-risk task, capability-tied passed evidence -> satisfied
    _ev.write_record("current", {"type": "bug", "risk": "high",
                                 "obligations": ["regression test"], "evidence": []})
    f = d / "app.py"
    f.write_text("x=1\n")
    _ev.append_evidence("current", "tests", "passed", exit_code=0, files=[str(f)],
                        capability="verify-turn", obligation="suite passes")
    code, _ = gate_exit(d)
    check("capability-tied evidence satisfies", code == 0)

    # high-risk, UNTIED passed evidence -> must FAIL (unproven provenance)
    d2 = Path(tmp) / "d2"
    d2.mkdir()
    _ev.EVIDENCE_DIR = d2
    _ev.write_record("current", {"type": "bug", "risk": "high",
                                 "obligations": ["regression test"], "evidence": []})
    f2 = d2 / "app.py"
    f2.write_text("x=1\n")
    _ev.append_evidence("current", "tests", "passed", exit_code=0, files=[str(f2)])  # NO capability
    code, out = gate_exit(d2)
    check("untied evidence does NOT satisfy", code == 2)
    check("reason names the gap", "capability-tied" in out)

    # stale capability-tied evidence -> blocked (existing staleness preserved)
    d3 = Path(tmp) / "d3"
    d3.mkdir()
    _ev.EVIDENCE_DIR = d3
    _ev.write_record("current", {"type": "bug", "risk": "high",
                                 "obligations": ["regression test"], "evidence": []})
    f3 = d3 / "app.py"
    f3.write_text("x=1\n")
    _ev.append_evidence("current", "tests", "passed", exit_code=0, files=[str(f3)],
                        capability="verify-turn", obligation="suite passes")
    f3.write_text("x=2\n")  # changed after evidence
    code, out = gate_exit(d3)
    check("stale capability evidence blocked", code == 2)
    check("staleness named", "stale" in out)

print(f"OK: {PASS} assertions passed")

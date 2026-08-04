#!/usr/bin/env python3
"""Self-check for hooks/lib/gate.py — the evidence-aware completion gate."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evidence as _ev
import gate as _gate

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def gate_result(rec):
    """Run gate main() against a record; return (exit_code, stderr)."""
    import io
    from contextlib import redirect_stderr
    with tempfile.TemporaryDirectory() as tmp:
        _ev.EVIDENCE_DIR = Path(tmp)
        if rec:
            _ev.write_record("current", rec)
        buf = io.StringIO()
        with redirect_stderr(buf):
            try:
                _gate.main()
                return 0, buf.getvalue()
            except SystemExit as e:
                return e.code, buf.getvalue()


def gate_result_in_place(evidence_dir):
    """Run gate against the record already in evidence_dir (built externally)."""
    import io
    from contextlib import redirect_stderr
    _ev.EVIDENCE_DIR = evidence_dir
    buf = io.StringIO()
    with redirect_stderr(buf):
        try:
            _gate.main()
            return 0, buf.getvalue()
        except SystemExit as e:
            return e.code, buf.getvalue()


# 1. high-risk, no evidence -> block
code, out = gate_result({"type": "bug", "risk": "high", "obligations": ["regression test"], "evidence": []})
check("high-risk no evidence blocks", code == 2)
check("block names the gap", "no capability-tied passed test evidence" in out)

# 2. high-risk, passed tests -> pass
with tempfile.TemporaryDirectory() as tmp:
    _ev.EVIDENCE_DIR = Path(tmp)
    f = Path(tmp) / "app.py"
    f.write_text("x=1\n")
    _ev.write_record("current", {"type": "bug", "risk": "high", "obligations": ["regression test"], "evidence": []})
    _ev.append_evidence("current", "tests", "passed", exit_code=0, files=[str(f)],
                        capability="verify-turn", obligation="suite passes")
    code, _ = gate_result_in_place(Path(tmp))
    check("high-risk with capability-tied passed tests passes", code == 0)

# 3. STALENESS: file changed after evidence -> block
with tempfile.TemporaryDirectory() as tmp:
    _ev.EVIDENCE_DIR = Path(tmp)
    f = Path(tmp) / "app.py"
    f.write_text("x=1\n")
    _ev.write_record("current", {"type": "bug", "risk": "high", "obligations": ["regression test"], "evidence": []})
    _ev.append_evidence("current", "tests", "passed", exit_code=0, files=[str(f)],
                        capability="verify-turn", obligation="suite passes")
    f.write_text("x=2\n")  # code changed AFTER verification
    code, out = gate_result_in_place(Path(tmp))
    check("stale evidence blocks", code == 2)
    check("staleness named", "stale evidence" in out)

# 4. low-risk, no evidence -> pass (no ceremony)
code, _ = gate_result({"type": "chore", "risk": "low", "obligations": [], "evidence": []})
check("low-risk passes without evidence", code == 0)

# 5. override recorded -> pass (auditable skip)
code, _ = gate_result({"type": "bug", "risk": "high", "obligations": ["regression test"], "evidence": [], "override": "manual QA done"})
check("explicit override passes", code == 0)

# 6. no record at all -> pass (nothing seeded)
code, _ = gate_result(None)
check("no record passes", code == 0)

print(f"OK: {PASS} assertions passed")

#!/usr/bin/env python3
"""Self-check for scripts/promote.py (v1.6.0 M7)."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("pm", Path(__file__).parent / "promote.py")
_pm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pm)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _pm.PROMO_DIR = Path(tmp)

    # full flow: propose -> validate -> fitness -> auto-approve (trust 5) -> promote
    _pm.propose("perf-policy", "add index hint", "reduces N+1", "fixture: 20% fewer", trust=5)
    check("propose", (_pm.PROMO_DIR / "perf-policy.json").exists())
    check("validate ok", _pm.validate("perf-policy", True) == "validated")
    check("fitness improves", _pm.fitness("perf-policy", True) == "fitness-checked")
    check("auto-approve trust5", _pm.approve("perf-policy", auto=True) == "approved-auto")
    out = _pm.promote("perf-policy", "1.6.1")
    check("promote traceable", "promoted" in out and "traceable" in out)
    check("trace written", (_pm.PROMO_DIR / "trace-perf-policy-1.6.1.json").exists())

    # evidence alone never promotes: propose but skip validate/fitness -> rejected
    _pm.propose("hasty", "x", "y", "some evidence", trust=3)
    check("unvalidated cannot promote",
          _pm.promote("hasty", "1.6.2") == "rejected: not approved")

    # regression failure rejects
    _pm.propose("risky", "x", "y", "ev", trust=5)
    _pm.validate("risky", False)
    check("regression fail rejects", _pm.approve("risky", auto=True) == "rejected: must validate + fitness-check first")

    # low trust (AI, 7) needs human even with evidence
    _pm.propose("ai-idea", "x", "y", "ev", trust=7)
    _pm.validate("ai-idea", True)
    _pm.fitness("ai-idea", True)
    check("AI trust needs human", _pm.approve("ai-idea", auto=True) == "needs-human: trust level below auto-approve")

    # human approval works for low trust
    check("human approves", _pm.approve("ai-idea") == "approved-by-human")
    check("then promotes", "promoted" in _pm.promote("ai-idea", "1.6.3"))

print(f"OK: {PASS} assertions passed")

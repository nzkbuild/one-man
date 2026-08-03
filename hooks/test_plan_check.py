#!/usr/bin/env python3
"""Self-check for plan-check.py — the plan-vs-reality gate."""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("plan_check", Path(__file__).parent.parent / "scripts" / "plan-check.py")
_pc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pc)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def run(plan_text, release=False):
    import sys
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "PLAN.md"
        p.write_text(plan_text, encoding="utf-8")
        old = sys.argv
        sys.argv = ["plan-check.py"] + (["--release"] if release else []) + [str(p)]
        try:
            _pc.main()
            return 0
        except SystemExit as e:
            return e.code
        finally:
            sys.argv = old


# open item blocks release
check("open item blocks --release", run("- [ ] do the thing\n- [x] done\n", release=True) == 2)
# deferral exempt from release-block
check("deferral exempt", run("- [ ] later (v1.1 defer)\n- [x] done\n", release=True) == 0)
# deferral with status words ("not built") is still exempt — status ≠ blocker
check("deferred-with-status exempt", run("- [ ] task-triage NOT built (v1.1 defer)\n", release=True) == 0)
# blocking qualifier overrides deferral
check("blocking overrides deferral", run("- [ ] task-triage (v1.1 defer, required before release)\n", release=True) == 2)
# all done passes
check("all done passes", run("- [x] a\n- [x] b\n", release=True) == 0)
# plain mode informational (exit 0 even with open)
check("plain mode informational", run("- [ ] open\n", release=False) == 0)

print(f"OK: {PASS} assertions passed")

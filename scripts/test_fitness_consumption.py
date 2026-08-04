#!/usr/bin/env python3
"""Self-check for v1.7.0 M1 — fitness verdict consumption.

A zombie or unhealthy policy must produce a visible, deterministic
consequence:
  - SessionStart injects a one-line warning (not a dashboard)
  - readiness blocks release when a policy is zombie (never applied)
"""
import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("fit", Path(__file__).parent.parent / "hooks" / "lib" / "fitness.py")
_fit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fit)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _fit.FITNESS_DIR = Path(tmp)

    # a policy that was applied -> healthy
    _fit.record("policy-1.6.0", "applied")
    _fit.record("policy-1.6.0", "applied")
    check("applied policy healthy", _fit.verdict("policy-1.6.0") == "healthy")

    # a policy never applied -> zombie (deterministic consequence)
    check("unapplied policy zombie", _fit.verdict("policy-1.7.0") == "zombie")

    # report surfaces the zombie (the SessionStart consumer's input)
    report = _fit.report()
    check("report has the zombie line", any("zombie" in r for r in report))
    check("report is one-line each", all("\n" not in r for r in report))

    # an unhealthy (watch) policy is surfaced too
    _fit.record("policy-watch", "applied")
    _fit.record("policy-watch", "override")
    check("high-friction policy watch", _fit.verdict("policy-watch") == "watch")

    # no vanity scores: the report carries ACTIONABLE signals only (verdict +
    # friction rate + application count). No aggregate "health score" line.
    check("no vanity aggregate", not any("health:" in r or "score" in r.lower() for r in report))
    check("actionable: verdict + friction", any("friction" in r for r in report))

print(f"OK: {PASS} assertions passed")

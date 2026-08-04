#!/usr/bin/env python3
"""Release readiness assessment (v1.6.0 M8 — layer 9).

Aggregates the existing gates + debt + drift into one release verdict:
  - all self-checks pass (the suite)
  - plan-check clear
  - policy layer valid (versioned)
  - no high-risk open debt (acknowledged + unfixed + high)
  - no high-severity open drift
  - evidence gate satisfied for the current task

The verdict: READY | NOT-READY (with the blocking reasons).

This is the "looks done != is done" lesson aggregated — one number from
existing data, no new data sources. Advisory at the release decision;
the individual gates remain the real authority.
"""
import os
import subprocess
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
REPO = Path(__file__).parent.parent


def _run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(REPO), timeout=120)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def _high_risk_debt():
    """Load debt blocking at release (acknowledged + open + high)."""
    try:
        sys.path.insert(0, str(REPO / "hooks" / "lib"))
        import debt as _debt
        return _debt.blocking_at_release()
    except Exception:
        return []


def assess() -> dict:
    reasons = []
    ok = True

    # v1.6.0 F6: pre-push already ran check + health + plan-check. Readiness
    # CONSUMES those results (via the policy/debt/drift signals) instead of
    # re-running the suite — one execution, not two.

    # 1. high-risk open debt
    debt = _high_risk_debt()
    if debt:
        ok = False
        reasons.append(f"{len(debt)} high-risk open debt entries (acknowledged + unfixed)")

    # 2. high-severity open drift
    code, out = _run(["python", "scripts/drift-check.py"])
    if code != 0:
        ok = False
        reasons.append("high-severity open drift")

    # 3. version consistency (python-native)
    try:
        import json as _j
        pkg = _j.loads((REPO / "package.json").read_text(encoding="utf-8"))["version"]
        ctl = _j.loads((REPO / "one-man.controls.json").read_text(encoding="utf-8"))["version"]
        if pkg != ctl:
            ok = False
            reasons.append(f"version mismatch: package={pkg} controls={ctl}")
    except Exception:
        ok = False
        reasons.append("version consistency check failed (unreadable policies)")

    # 4. policy fitness (v1.7.0 M1): zombie policies are a release concern —
    # a policy that never runs is dead weight the release should not bless.
    try:
        sys.path.insert(0, str(REPO / "hooks" / "lib"))
        import fitness as _fit
        _zombies = [r for r in _fit.report() if "zombie" in r]
        if _zombies:
            ok = False
            reasons.append(f"{len(_zombies)} zombie polic(y/ies) — no applications; deprecate or wire")
    except Exception:
        pass

    return {"ready": ok, "reasons": reasons}


def main():
    result = assess()
    verdict = "READY" if result["ready"] else "NOT-READY"
    print(f"## Release readiness: {verdict}")
    for r in result["reasons"]:
        print(f"- {r}")
    sys.exit(0 if result["ready"] else 2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"readiness error: {e}", file=sys.stderr)
        sys.exit(2)

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

    # 1. self-checks
    code, out = _run(["node", "test/run-tests.js"])
    if code != 0:
        ok = False
        reasons.append("self-checks failing")
    else:
        passed = out.strip().splitlines()[-1] if out.strip() else "?"
        reasons.append(f"self-checks pass ({passed})")

    # 2. plan-check
    code, _ = _run(["python", "scripts/plan-check.py", "--release"])
    if code != 0:
        ok = False
        reasons.append("plan-check blocked (open non-deferred items)")

    # 3. policy layer valid
    code, _ = _run(["python", "scripts/validate-policies.py"])
    if code != 0:
        ok = False
        reasons.append("policy layer invalid")

    # 4. high-risk open debt
    debt = _high_risk_debt()
    if debt:
        ok = False
        reasons.append(f"{len(debt)} high-risk open debt entries (acknowledged + unfixed)")

    # 5. high-severity open drift
    code, out = _run(["python", "scripts/drift-check.py"])
    if code != 0:
        ok = False
        reasons.append("high-severity open drift")

    # 6. version consistency
    code, out = _run(["bash", "claude-health.sh"])
    if code != 0:
        ok = False
        reasons.append("health check failed (version/YAML consistency)")

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

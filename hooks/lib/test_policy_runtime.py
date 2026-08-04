#!/usr/bin/env python3
"""Self-check for hooks/lib/policy-runtime.py (v1.6.0 M3).

The PARITY contract: for the same task record, the runtime must produce the
same verdicts the v1.5.x hooks produce. This test asserts that parity —
the migration safety net.
"""
from pathlib import Path

import importlib.util
_spec = importlib.util.spec_from_file_location("policy_runtime", Path(__file__).parent / "policy-runtime.py")
_pr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pr)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def plan(ttype, risk):
    return _pr.evaluate({"type": ttype, "risk": risk})


# --- parity with v1.5.x hooks ---

# high-risk bug -> isolated review + evidence required (review-gate + evidence-gate)
p = plan("bug", "high")
check("high bug: isolated review", p["review_required"] == "isolated")
check("high bug: evidence required", p["evidence_required"] is True)
check("high bug: workflow has isolated-review", "isolated-review" in p["workflow"])

# medium feature -> evidence required, standard review
p = plan("feature", "medium")
check("medium: evidence required", p["evidence_required"] is True)
check("medium: standard review", p["review_required"] == "standard")

# low chore -> no evidence, no review, basic verification
p = plan("chore", "low")
check("low: no evidence", p["evidence_required"] is False)
check("low: no review", p["review_required"] is None)
check("low: basic verification", p["workflow"] == ["basic-verification"])

# --- obligations map (the v1.5.x seed) ---
p = plan("refactor", "medium")
check("refactor obligations", "behavior unchanged" in p["obligations"])

# --- policy version carried (the versioning layer) ---
check("policy version present", p["policy_version"] == "1.6.0")

# --- skills from flow (design chain unwrapped) ---
p = plan("design", "medium")
check("design skills chain", "brandkit" in p["skills"])

# --- deterministic: same input -> same plan ---
p1 = plan("bug", "high")
p2 = plan("bug", "high")
check("deterministic", p1 == p2)

print(f"OK: {PASS} assertions passed")

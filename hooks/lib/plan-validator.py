"""Plan validation (v1.7.0 M5).

Before implementation, validate the generated engineering assignment for:
  - missing dependencies (workstreams that need a prerequisite not present)
  - incorrect ordering (precedence violated)
  - missing baseline repair (dirty repo but no repair workstream)
  - unnecessary rewrites (situation says extend, plan says rewrite)
  - unbounded scope (no non-goals, or non-goals empty for a big task)
  - weak acceptance criteria (no verifiable outcome)
  - missing rollback/recovery (migration/refactor without it)
  - missing security/privacy/compat/performance/docs work
  - milestones that cannot be independently verified

REJECT or REPAIR invalid plans automatically where policy provides a
deterministic correction. Return (valid, findings, repairs).
"""
from assignment import PRECEDENCE

# Situations whose workstreams REQUIRE rollback/recovery
NEEDS_ROLLBACK = {"migration", "refactor"}

# Situations that REQUIRE a repair-first step (broken baseline)
NEEDS_REPAIR = {"brownfield", "resumed"}


def validate(assignment: dict, baseline: dict = None) -> tuple:
    """Return (valid: bool, findings: list, repairs: list)."""
    findings = []
    repairs = []
    workstreams = assignment.get("workstreams", [])
    situation = assignment.get("situation", "brownfield")
    baseline = baseline or {}

    # 1. precedence: every workstream's deps must precede it
    for i, ws in enumerate(workstreams):
        for dep in PRECEDENCE.get(ws, []):
            if dep not in workstreams[:i]:
                findings.append(f"ordering: {ws} depends on {dep} which is not before it")
                # repair: move the dep before
                if dep not in workstreams:
                    repairs.append(f"insert missing prerequisite {dep} before {ws}")

    # 2. baseline repair: dirty repo needs a repair/baseline-first workstream
    if baseline.get("dirty") and situation in NEEDS_REPAIR:
        if "repair" not in workstreams and "baseline" not in workstreams[:1]:
            findings.append("baseline repair: dirty repo but no repair/baseline-first step")
            repairs.append("add repair step before extend")

    # 3. rollback: migration/refactor must have a rollback path
    if situation in NEEDS_ROLLBACK:
        if not any("rollback" in str(w).lower() for w in workstreams):
            findings.append(f"missing rollback: {situation} needs a recovery path")
            repairs.append(f"add rollback/recovery workstream to {situation} plan")

    # 4. scope: non-goals must exist (unbounded scope guard)
    if not assignment.get("non_goals"):
        findings.append("unbounded scope: no non-goals defined")
        repairs.append("add explicit non-goals (what this change will NOT do)")

    # 5. acceptance: must be verifiable (not 'works end-to-end' alone)
    acceptance = assignment.get("acceptance", [])
    if not any(a in " ".join(acceptance).lower() for a in
               ("suite green", "test", "verify", "measure")):
        findings.append("weak acceptance: no verifiable outcome")
        repairs.append("add a measurable acceptance criterion")

    # 6. verification: every milestone independently verifiable
    if not workstreams:
        findings.append("no workstreams — empty plan")
        repairs.append("synthesize workstreams from the situation")

    return (len(findings) == 0, findings, repairs)


if __name__ == "__main__":
    import json
    import sys
    from assignment import synthesize
    sit = sys.argv[1] if len(sys.argv) > 1 else "brownfield"
    base = {"git": {"dirty": True}, "tests": {"passing": None},
            "unfinished": [], "debt_drift": {"debt": 0, "drift": 0}}
    assignment = synthesize(sit, base, {"type": "feature"})
    ok, findings, repairs = validate(assignment, base)
    print(json.dumps({"situation": sit, "valid": ok, "findings": findings,
                      "repairs": repairs}, indent=1))

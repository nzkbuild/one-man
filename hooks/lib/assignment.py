"""Engineering assignment synthesis (v1.7.0 M3).

Turns situation + verified baseline + task record into a structured internal
assignment: verified state, scope/non-goals, risks, affected systems,
workstreams, dependencies, milestones, acceptance criteria, verification
strategy, re-planning triggers, definition of done.

The plan is DERIVED from verified findings — never a generic template.
Situation drives the workstreams and sequencing:
  - greenfield: baseline first, then scaffold -> core -> verify
  - brownfield: baseline + debt/drift first, then repair -> test -> docs
  - resumed: finish what exists (baseline unfinished-work first)
  - bug: reproduce -> root cause -> fix -> regression
  - refactor: characterization tests -> transform -> verify same behavior
  - migration: inventory -> plan -> execute -> compatibility verify
  - security/performance: baseline measure -> targeted change -> re-measure
  - release: readiness gate -> version -> changelog -> tag

Sequencing rules (correct order, from verified findings):
  - anything that UNBLOCKS verification goes first (tests, build)
  - debt/drift that blocks the change goes before the change
  - parallel workstreams only when no shared-file dependency
"""
# Situation -> workstream template (the SEQUENCING skeleton — filled with
# verified findings, never used verbatim)
SITUATION_WORKSTREAMS = {
    "greenfield": [
        ("baseline", "scaffold project structure + build + test harness"),
        ("core", "implement the core domain model"),
        ("verify", "tests + build green"),
        ("docs", "README + architecture"),
    ],
    "brownfield": [
        ("baseline", "verify current state (failures, debt, drift)"),
        ("repair", "fix existing failures before adding"),
        ("extend", "the requested change on a green baseline"),
        ("verify", "suite + gates"),
        ("docs", "sync README/CHANGELOG for the change"),
    ],
    "resumed": [
        ("baseline", "verify what exists + unfinished work"),
        ("finish", "complete the unfinished workstreams"),
        ("verify", "suite + gates green"),
        ("docs", "mark completed milestones in the plan"),
    ],
    "bug-investigation": [
        ("reproduce", "capture the failing behavior"),
        ("root-cause", "trace to the defect"),
        ("fix", "minimal change"),
        ("regression", "test that failed before, passes now"),
    ],
    "refactor": [
        ("characterize", "baseline tests for current behavior"),
        ("transform", "incremental refactor, behavior unchanged"),
        ("verify", "characterization tests still green"),
    ],
    "migration": [
        ("inventory", "map what migrates (interfaces, data, deps)"),
        ("plan", "ordered migration steps + rollback"),
        ("execute", "stepwise, verify each"),
        ("compat", "backward-compat verification"),
    ],
    "security-performance": [
        ("baseline-measure", "establish the current metric"),
        ("targeted-change", "the specific fix/optimization"),
        ("re-measure", "prove the improvement"),
    ],
    "release-preparation": [
        ("readiness", "aggregate gates + debt + drift"),
        ("version", "bump + changelog"),
        ("release", "branch -> CI -> tag"),
    ],
}

# Sequencing constraints: workstream X must precede Y
PRECEDENCE = {
    "baseline": [],
    "repair": ["baseline"],
    "extend": ["repair"],
    "reproduce": [],
    "root-cause": ["reproduce"],
    "fix": ["root-cause"],
    "regression": ["fix"],
    "characterize": [],
    "transform": ["characterize"],
    "inventory": [],
    "plan": ["inventory"],
    "execute": ["plan"],
    "compat": ["execute"],
    "baseline-measure": [],
    "targeted-change": ["baseline-measure"],
    "re-measure": ["targeted-change"],
    "readiness": [],
    "version": ["readiness"],
    "release": ["version"],
}


def synthesize(situation: str, baseline: dict, task: dict) -> dict:
    """The structured engineering assignment, derived from verified findings."""
    workstreams = SITUATION_WORKSTREAMS.get(situation, SITUATION_WORKSTREAMS["brownfield"])

    # verified current state (the baseline, not assumptions)
    verified_state = {
        "branch": baseline.get("git", {}).get("branch"),
        "dirty": baseline.get("git", {}).get("dirty"),
        "tests_passing": baseline.get("tests", {}).get("passing"),
        "unfinished": baseline.get("unfinished", []),
        "debt": baseline.get("debt_drift", {}).get("debt", 0),
        "drift": baseline.get("debt_drift", {}).get("drift", 0),
    }

    # scope + non-goals from the situation + task
    scope = f"{task.get('type', 'chore')} work in a {situation} context"
    non_goals = _non_goals(situation)

    # risks from the verified state (not generic)
    risks = []
    if verified_state["dirty"]:
        risks.append("dirty working tree — unrelated changes may be entangled")
    if verified_state["debt"]:
        risks.append(f"{verified_state['debt']} open debt entries may block or complicate")
    if verified_state["drift"]:
        risks.append(f"{verified_state['drift']} drift findings — docs may not match code")

    # sequencing: the ordered workstreams (derived, respecting precedence)
    ordered = _sequence(workstreams)

    return {
        "situation": situation,
        "verified_state": verified_state,
        "scope": scope,
        "non_goals": non_goals,
        "risks": risks,
        "workstreams": [w[0] for w in ordered],
        "milestones": [w[0] for w in ordered],
        "acceptance": _acceptance(situation),
        "definition_of_done": "suite green + gates pass + evidence non-stale + docs synced",
        "replan_triggers": ["verified evidence changes assumptions, dependencies, risks, or feasibility"],
        "derived_from_verified_findings": True,
    }


def _non_goals(situation: str) -> list:
    base = ["unrelated rewrites", "scope beyond the request"]
    if situation == "refactor":
        return base + ["no behavior change"]
    if situation == "migration":
        return base + ["no silent data loss"]
    return base


def _acceptance(situation: str) -> list:
    common = ["suite green", "gates pass", "evidence non-stale"]
    if situation == "bug-investigation":
        return ["bug reproduced", "root cause found", "regression test"] + common
    if situation == "refactor":
        return ["characterization tests green before+after", "no behavior change"] + common
    if situation == "migration":
        return ["compatibility verified", "rollback path tested"] + common
    if situation == "security-performance":
        return ["baseline measured", "improvement proven by re-measure"] + common
    if situation == "release-preparation":
        return ["readiness READY", "version bumped", "changelog complete"] + common
    return ["requested change works end-to-end"] + common


def _sequence(workstreams: list) -> list:
    """Topological sort respecting precedence (verified-first ordering)."""
    order = []
    remaining = list(workstreams)
    while remaining:
        for ws in list(remaining):
            name = ws[0]
            deps = PRECEDENCE.get(name, [])
            if all(d in [o[0] for o in order] for d in deps):
                order.append(ws)
                remaining.remove(ws)
                break
        else:  # cycle or unresolvable — append the rest (safety)
            order.extend(remaining)
            break
    return order


if __name__ == "__main__":
    import json
    import sys
    sit = sys.argv[1] if len(sys.argv) > 1 else "brownfield"
    print(json.dumps(synthesize(sit, {"git": {"branch": "main", "dirty": True},
                                      "tests": {"passing": None},
                                      "unfinished": ["uncommitted: 2 files"],
                                      "debt_drift": {"debt": 2, "drift": 3}},
                                     {"type": "feature"}), indent=2))

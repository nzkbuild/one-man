#!/usr/bin/env python3
"""Self-check for assignment.py (v1.7.0 M3).

The assignment must be DERIVED from verified findings and situation —
different situations produce different workstreams, sequencing, acceptance.
Not a generic template.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import assignment as _as

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


BASE = {"git": {"branch": "main", "dirty": True}, "tests": {"passing": None},
        "unfinished": ["uncommitted: 2"], "debt_drift": {"debt": 2, "drift": 3}}

# greenfield: baseline-first sequencing
g = _as.synthesize("greenfield", BASE, {"type": "feature"})
check("greenfield starts with baseline", g["workstreams"][0] == "baseline")
check("greenfield workstreams", "core" in g["workstreams"] and "verify" in g["workstreams"])

# brownfield: repair BEFORE extend (verified-first)
b = _as.synthesize("brownfield", BASE, {"type": "feature"})
check("brownfield repairs first", b["workstreams"].index("repair") < b["workstreams"].index("extend"))
check("brownfield baseline first", b["workstreams"][0] == "baseline")

# bug: reproduce -> root-cause -> fix -> regression
bug = _as.synthesize("bug-investigation", BASE, {"type": "bug"})
check("bug sequencing", bug["workstreams"] == ["reproduce", "root-cause", "fix", "regression"])
check("bug acceptance has regression", any("regression" in a for a in bug["acceptance"]))

# refactor: characterize before transform
ref = _as.synthesize("refactor", BASE, {"type": "refactor"})
check("refactor characterizes first", ref["workstreams"].index("characterize") < ref["workstreams"].index("transform"))
check("refactor non-goal no behavior change", any("behavior change" in n for n in ref["non_goals"]))

# security: baseline-measure -> targeted-change -> re-measure
sec = _as.synthesize("security-performance", BASE, {"type": "feature"})
check("security measures first", sec["workstreams"] == ["baseline-measure", "targeted-change", "re-measure"])

# release: readiness -> version -> release
rel = _as.synthesize("release-preparation", BASE, {"type": "chore"})
check("release sequencing", rel["workstreams"] == ["readiness", "version", "release"])

# risks from verified state (dirty + debt + drift — not generic)
check("risk: dirty", any("dirty" in r for r in b["risks"]))
check("risk: debt", any("debt" in r for r in b["risks"]))

# the contract: derived, not template
check("derived flag", g["derived_from_verified_findings"] is True)
check("verified state present", g["verified_state"]["branch"] == "main")

print(f"OK: {PASS} assertions passed")

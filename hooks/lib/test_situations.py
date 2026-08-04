#!/usr/bin/env python3
"""Self-check for situations.py (v1.7.0 M1).

The core requirement: deliberately weak prompts produce DIFFERENT,
situation-appropriate recognition — not a generic default.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import situations as _st

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


# weak prompts -> distinct situations
check("build this -> greenfield", _st.classify_situation("Build this idea properly") == "greenfield")
check("continue -> resumed", _st.classify_situation("Continue this unfinished project") == "resumed")
check("fix wrong -> bug-investigation", _st.classify_situation("Fix what is wrong here") == "bug-investigation")
check("refactor -> refactor", _st.classify_situation("Refactor this without breaking anything") == "refactor")
check("secure -> security-performance", _st.classify_situation("Make this secure and production-ready") == "security-performance")
check("release -> release-preparation", _st.classify_situation("Prepare this for release") == "release-preparation")
check("migrate -> migration", _st.classify_situation("Migrate this to the new framework") == "migration")

# repo-state override: greenfield prompt on a dirty repo with tests -> brownfield
check("greenfield prompt + dirty repo -> brownfield",
      _st.classify_situation("Build this idea properly",
                             {"dirty": True, "has_tests": True}) == "brownfield")

# repo_state detects branch/dirty/tests (fixture)
with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    (d / "test").mkdir()
    state = _st.repo_state(d)
    check("fixture has tests", state["has_tests"] is True)
    check("fixture not a git repo -> branch None", state["branch"] is None or state["dirty"] is False)

# default: unknown prompt on clean repo with no tests -> brownfield (safe)
check("no signal defaults brownfield", _st.classify_situation("something vague here") == "brownfield")

print(f"OK: {PASS} assertions passed")

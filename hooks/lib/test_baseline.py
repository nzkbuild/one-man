#!/usr/bin/env python3
"""Self-check for baseline.py (v1.7.0 M2).

The baseline must be VERIFIED, not assumed: every field checked against
reality. A plan built on an unverified baseline is a guess.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import baseline as _bl

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


# git state on the real repo (it IS a git repo).
# Class fix: CI checks out with a DETACHED HEAD (no branch) — so branch may
# legitimately be None. The invariant is: is_git True + dirty is a bool.
git = _bl.git_state()
check("repo is git", git["is_git"] is True)
check("branch is str or None (detached HEAD valid)", git["branch"] is None or isinstance(git["branch"], str))
check("dirty is a bool", isinstance(git["dirty"], bool))

# non-git dir -> is_git False, no crash
with tempfile.TemporaryDirectory() as tmp:
    state = _bl.git_state(Path(tmp))
    check("non-git -> is_git False", state["is_git"] is False)

# test state: bounded probe — runner exists, passing deferred to Stop-time
tests = _bl.test_state()
check("has runner", tests["has_runner"] is True)
check("passing deferred to Stop", tests["passing"] is None)
check("bounded (no full suite at prompt)", tests["summary"] == "not probed (Stop-time verify)")

# unfinished work: the repo has uncommitted changes (dirty)
unfinished = _bl.unfinished_work()
check("unfinished is a list", isinstance(unfinished, list))

# debt_and_drift returns the policy outputs
dd = _bl.debt_and_drift()
check("debt count int", isinstance(dd["debt"], int))
check("drift count int", isinstance(dd["drift"], int))

# full baseline is verified (the contract)
b = _bl.baseline()
check("baseline verified flag", b["verified"] is True)
check("baseline has all sections", {"git", "tests", "unfinished", "debt_drift"} <= set(b.keys()))

print(f"OK: {PASS} assertions passed")

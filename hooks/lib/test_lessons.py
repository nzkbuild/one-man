#!/usr/bin/env python3
"""Self-check for hooks/lib/lessons.py — the lesson ledger."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lessons as _ls

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _ls.LESSONS_DIR = Path(tmp)

    # 1. add + read back
    lid = _ls.add("test isolation gap", "hook test scanned real repo",
                  "point gate at empty temp cwd", layer="regression-test",
                  recurrence_risk="high", tested=True, test_ref="test_review_gate.py")
    check("add returns id", lid is not None)
    lessons = _ls.all_lessons()
    check("one lesson stored", len(lessons) == 1)
    check("fields present", lessons[0]["layer"] == "regression-test"
          and lessons[0]["recurrence_risk"] == "high" and lessons[0]["tested"])

    # 2. high-risk untested detection
    _ls.add("version bump miss", "no consistency check", "add health check",
            layer="hook", recurrence_risk="high", tested=False)
    risky = _ls.high_risk_untested()
    check("high-risk untested detected", len(risky) == 1)
    check("tested lesson excluded", risky[0]["violation"] == "version bump miss")

    # 3. relevance filter (token discipline)
    _ls.add("lint class E741", "ambiguous variable names", "use descriptive names",
            layer="hook", recurrence_risk="medium", category="lint")
    rel = _ls.relevant("python lint test")
    check("relevant matches", any("E741" in r["violation"] for r in rel))
    check("capped at 5", len(rel) <= 5)
    check("empty signals -> empty", _ls.relevant("") == [])

    # 4. bounded: > MAX prunes oldest
    for i in range(_ls.MAX_LESSONS + 5):
        _ls.add(f"bulk lesson {i}", "bulk", "bulk", layer="none")
    check("bounded at MAX", len(_ls.all_lessons()) <= _ls.MAX_LESSONS)

print(f"OK: {PASS} assertions passed")

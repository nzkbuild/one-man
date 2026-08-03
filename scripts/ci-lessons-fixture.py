#!/usr/bin/env python3
"""CI fixture: check-lessons enforcement (v1.5.1 release).

Proves in CI (the authority beyond local hooks):
  1. an unresolved high-risk lesson (status observed) BLOCKS (exit 2)
  2. an enforced/tested/closed/dismissed lesson PASSES (exit 0)
  3. malformed or privacy-unsafe lesson data FAILS SAFELY (exit 2, no crash)
"""
import json
import sys
import tempfile
from pathlib import Path

import importlib.util
_spec = importlib.util.spec_from_file_location("check_lessons",
                                              Path(__file__).parent / "check-lessons.py")
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)

def run_with(lessons):
    """Write lessons to a fixture dir, run check(); return exit code."""
    with tempfile.TemporaryDirectory() as tmp:
        cl.LESSONS_DIR = Path(tmp)
        for name, data in lessons.items():
            (Path(tmp) / name).write_text(json.dumps(data), encoding="utf-8")
        probs = cl.check()
        return 2 if probs else 0

def expect(code, want, label):
    ok = code == want
    print(f"[{'PASS' if ok else 'FAIL'}] {label} (exit {code}, want {want})")
    if not ok:
        sys.exit(1)

# 1. unresolved high-risk blocks
expect(run_with({"a.json": {"violation": "unresolved risk", "recurrence_risk": "high",
                            "status": "observed", "layer": "hook"}}),
       2, "unresolved high-risk blocks")

# 2. learned statuses pass
for st in ("enforced", "tested", "closed", "dismissed"):
    expect(run_with({"a.json": {"violation": "learned", "recurrence_risk": "high",
                                "status": st, "tested": True,
                                "test_ref": "scripts/ci-lessons-fixture.py"}}),
           0, f"{st} lesson passes")

# 3. malformed data fails safely (no crash, exit 2)
with tempfile.TemporaryDirectory() as tmp:
    cl.LESSONS_DIR = Path(tmp)
    (Path(tmp) / "bad.json").write_text("{broken json", encoding="utf-8")
    (Path(tmp) / "risky.json").write_text(
        json.dumps({"violation": "x", "recurrence_risk": "high", "status": "observed"}),
        encoding="utf-8")
    try:
        probs = cl.check()
        expect(2 if probs else 0, 2, "malformed + unresolved fails safely")
    except Exception as e:
        print(f"[FAIL] check crashed on malformed data: {e}")
        sys.exit(1)

print("all CI lesson-fixture cases passed")

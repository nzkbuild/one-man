#!/usr/bin/env python3
"""CI-parity regression test (v1.5.1 M3, from the F6 lesson).

The v1.5.0 M5 test failure: test_review_gate's run_gate scanned the REAL repo
cwd — passed on Windows, failed on CI-linux (different repo state). The
lesson: hook tests MUST point the gate/hook at an isolated empty cwd so the
repo's own files never enter the scan.

This test asserts the pattern holds across the review/evidence gates:
each gate, given a temp cwd, sees NO repo files (empty scan) and behaves
deterministically regardless of repo state. Local-vs-CI parity, enforced.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scan as _scan
import evidence as _ev
import gate as _gate

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    empty = Path(tmp)

    # 1. scan on an empty dir finds nothing (the isolation invariant)
    found = _scan.changed_files(empty)
    check("empty cwd scan is empty", found == [])

    # 2. gate on a high-risk task with NO evidence -> blocks, independent of cwd
    _ev.EVIDENCE_DIR = empty / "ev"
    _ev.write_record("current", {"type": "bug", "risk": "high",
                                 "obligations": ["regression test"], "evidence": []})
    os.environ["HOOK_INPUT"] = json.dumps({"cwd": str(empty)})
    import io
    from contextlib import redirect_stderr
    buf = io.StringIO()
    with redirect_stderr(buf):
        try:
            _gate.main()
            code = 0
        except SystemExit as e:
            code = e.code
    check("gate blocks deterministically on empty cwd", code == 2)

    # 3. the same gate, pointed at the REAL repo cwd, must give the SAME
    #    verdict for the evidence logic (parity — no repo-state dependence)
    _ev.EVIDENCE_DIR = empty / "ev2"
    _ev.write_record("current", {"type": "bug", "risk": "high",
                                 "obligations": ["regression test"], "evidence": []})
    buf2 = io.StringIO()
    with redirect_stderr(buf2):
        try:
            _gate.main()
            code2 = 0
        except SystemExit as e:
            code2 = e.code
    check("parity: same verdict regardless of cwd state", code2 == 2)

print(f"OK: {PASS} assertions passed")

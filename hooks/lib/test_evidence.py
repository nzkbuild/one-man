#!/usr/bin/env python3
"""Self-check for hooks/lib/evidence.py — the per-task evidence store."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evidence as _ev

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    # point the store at the temp dir
    _ev.EVIDENCE_DIR = Path(tmp)
    task = "t-123"

    # 1. write_record + read back
    _ev.write_record(task, {"type": "bug", "risk": "high", "obligations": ["regression test"]})
    rec = _ev.read_record(task)
    check("record written", rec is not None)
    check("record fields", rec["type"] == "bug" and rec["risk"] == "high")
    check("obligations stored", "regression test" in rec["obligations"])

    # 2. append_evidence with state hash
    f = Path(tmp) / "app.py"
    f.write_text("def f(): return 1\n")
    _ev.append_evidence(task, "tests", "passed", exit_code=0, files=[str(f)])
    rec = _ev.read_record(task)
    check("evidence appended", len(rec["evidence"]) == 1)
    check("exit_code stored", rec["evidence"][0]["exit_code"] == 0)
    check("state hash stored", len(rec["evidence"][0]["state_hash"]) == 16)

    # 3. staleness: file changes -> hash differs
    h1 = rec["evidence"][0]["state_hash"]
    f.write_text("def f(): return 2\n")  # code changed
    h2 = _ev.state_hash([str(f)])
    check("staleness detected (hash differs)", h1 != h2)

    # 4. bounded: > MAX_RECORDS prunes oldest
    for i in range(_ev.MAX_RECORDS + 10):
        _ev.write_record(f"task-{i}", {"type": "chore"})
    count = len(list(_ev.EVIDENCE_DIR.glob("*.json")))
    check("store bounded", count <= _ev.MAX_RECORDS)

print(f"OK: {PASS} assertions passed")

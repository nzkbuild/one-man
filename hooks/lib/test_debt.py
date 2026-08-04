#!/usr/bin/env python3
"""Self-check for hooks/lib/debt.py (v1.6.0 M4)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import debt as _dt

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    _dt.DEBT_DIR = Path(tmp)

    # create + classify
    did = _dt.create("app.py", "bare except at line 4", severity="high", source="review-gate")
    check("create returns id", did is not None)
    d = _dt._read(did) if hasattr(_dt, "_read") else None
    # read via the file
    import json as _j
    d = _j.loads((Path(tmp) / f"{did}.json").read_text(encoding="utf-8"))
    check("status open", d["status"] == "open")
    check("classified tech", d["classification"] == "tech")
    check("severity stored", d["severity"] == "high")

    # recurrence: same finding -> bump, not dup
    did2 = _dt.create("app.py", "bare except at line 4", severity="high", source="review-gate")
    check("stable id dedupes", did2 == did)
    d = _j.loads((Path(tmp) / f"{did}.json").read_text(encoding="utf-8"))
    check("recurrences bumped", d["recurrences"] == 2)

    # classify
    check("TODO -> process", _dt.classify("TODO left in changed code") == "process")
    check("N+1 -> design", _dt.classify("N+1 query in loop") == "design")

    # lifecycle
    check("acknowledge", _dt.acknowledge(did))
    check("fix", _dt.fix(did))
    d = _j.loads((Path(tmp) / f"{did}.json").read_text(encoding="utf-8"))
    check("status fixed", d["status"] == "fixed")

    # blocking at release: acknowledged + open + high
    did3 = _dt.create("pay.py", "TODO left in payment module", severity="high", source="ship-gate")
    _dt.acknowledge(did3)
    blockers = _dt.blocking_at_release()
    check("ack+open+high blocks release", any(b["id"] == did3 for b in blockers))
    check("fixed debt not blocking", not any(b["id"] == did for b in blockers))

    # expiry: 2 releases without action
    did4 = _dt.create("stale.py", "magic number in loop", severity="low", source="review-gate")
    _dt.expire_all("1.6.0")
    _dt.expire_all("1.6.1")
    d = _j.loads((Path(tmp) / f"{did4}.json").read_text(encoding="utf-8"))
    check("stale debt expires", d["status"] == "expired")

print(f"OK: {PASS} assertions passed")

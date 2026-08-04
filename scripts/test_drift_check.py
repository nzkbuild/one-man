#!/usr/bin/env python3
"""Self-check for scripts/drift-check.py (v1.6.0 M5)."""
import importlib.util
import os
import tempfile
import time
from pathlib import Path

_spec = importlib.util.spec_from_file_location("dc", Path(__file__).parent / "drift-check.py")
_dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dc)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    now = time.time()

    # recent .py change -> flags README/CHANGELOG sync
    f = d / "app.py"
    f.write_text("x=1\n")
    os.utime(f, (now, now))
    findings = _dc.detect(d)
    check("py change flags README sync", any("README.md" in x["affected"] for x in findings))
    check("severity medium for py", any(x["severity"] == "medium" for x in findings))

    # package.json change -> high severity
    (d / "package.json").write_text("{}")
    findings = _dc.detect(d)
    check("package.json flags high", any(x["severity"] == "high" for x in findings))

    # verify_and_close: artifact synced after owner -> closed
    owner = findings[0]
    readme = d / "README.md"
    readme.write_text("# synced\n")
    os.utime(readme, (now + 1, now + 1))  # after the owner change
    check("sync verified closes", _dc.verify_and_close(d, owner))

    # not synced -> stays open
    owner2 = {"owner": "app.py", "affected": ["CHANGELOG.md"]}
    (d / "CHANGELOG.md").write_text("# old\n")
    os.utime(d / "CHANGELOG.md", (now - 10, now - 10))  # before the owner
    check("unsynced stays open", not _dc.verify_and_close(d, owner2))

print(f"OK: {PASS} assertions passed")

#!/usr/bin/env python3
"""Self-check for validate-policies.py (v1.6.0 M1)."""
import json
import tempfile
from pathlib import Path

import importlib.util
_spec = importlib.util.spec_from_file_location("vp", Path(__file__).parent / "validate-policies.py")
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    # valid policy
    (d / "ok.json").write_text(json.dumps(
        {"policy_version": "1.6.0", "controls": {}}), encoding="utf-8")
    # missing version
    (d / "noversion.json").write_text(json.dumps({"controls": {}}), encoding="utf-8")
    # bad semver
    (d / "badsemver.json").write_text(json.dumps(
        {"policy_version": "abc", "controls": {}}), encoding="utf-8")
    # unparsable
    (d / "broken.json").write_text("{broken", encoding="utf-8")

    check("valid passes", vp.check_policy(d / "ok.json"))
    check("missing version fails", not vp.check_policy(d / "noversion.json"))
    check("bad semver fails", not vp.check_policy(d / "badsemver.json"))
    check("unparsable fails", not vp.check_policy(d / "broken.json"))

print(f"OK: {PASS} assertions passed")

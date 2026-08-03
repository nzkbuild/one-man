#!/usr/bin/env python3
"""Self-check for lessons/seed.json (v1.5.1 M4).

Asserts the seed is: valid JSON, generic (zero personal data), every entry has
the required fields, and every tested:true entry's test_ref resolves.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
seed = json.loads((ROOT / "lessons" / "seed.json").read_text(encoding="utf-8"))

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


lessons = seed.get("lessons", [])
check("has lessons", len(lessons) >= 3)

REQUIRED = {"id", "violation", "root_cause", "correction", "layer",
            "recurrence_risk", "tested", "test_ref"}
for les in lessons:
    check(f"fields: {les['id']}", REQUIRED <= set(les.keys()))
    check(f"layer valid: {les['id']}", les["layer"] in
          {"local-memory", "claude-md", "skill", "hook", "regression-test", "ci-gate", "none"})
    check(f"risk valid: {les['id']}", les["recurrence_risk"] in {"high", "medium", "low"})
    if les["tested"]:
        check(f"test_ref resolves: {les['id']}", (ROOT / les["test_ref"]).exists())

# privacy: no personal data in the seed
raw = json.dumps(seed)
check("no api keys", not re.search(r"sk-[A-Za-z0-9]{20}", raw))
check("no email", "gmail" not in raw and "@" not in raw.replace('"@', ''))
check("no local paths", "/Users/" not in raw and "C:\\Users" not in raw and "nbzkr" not in raw)

print(f"OK: {PASS} assertions passed")

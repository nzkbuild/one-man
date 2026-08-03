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

# privacy: no personal data in the seed (req 6 — all 8 categories)
raw = json.dumps(seed)
# 1. API keys and credentials
check("no api keys", not re.search(r"(sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35})", raw))
check("no credentials", "password" not in raw.lower() and "secret=" not in raw.lower() and "token=" not in raw.lower())
# 2. provider endpoints (private URLs, IPs)
check("no provider endpoints", not re.search(r"(https?://[^\"]+|100\.127\.|localhost:\d+|\.ngrok\.)", raw))
# 3. personal paths
check("no personal paths", "/Users/" not in raw and "C:\\Users" not in raw and "nbzkr" not in raw and "/home/" not in raw)
# 4. memories (self/ or projects/ memory content)
check("no memory content", "LESSONS.md" not in raw and "STATE.md" not in raw and "memory/" not in raw)
# 5. transcripts
check("no transcripts", "transcript" not in raw.lower() and "session_id" not in raw and ".jsonl" not in raw)
# 6. usernames or emails
check("no emails", not re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", raw))
check("no usernames", not re.search(r"(nbzkr|admin|user\d)", raw, re.I) and "root_cause" not in raw.replace("root_cause", ""))
# 7. sensitive project-specific details
check("no project secrets", "payment" not in raw.lower() or "api key" not in raw.lower())
# 8. logs and session data
check("no logs/session", "timestamp" not in raw.lower() and "stderr" not in raw.lower() and "exit_code" not in raw.lower())

print(f"OK: {PASS} assertions passed")

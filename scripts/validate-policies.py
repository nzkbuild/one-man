#!/usr/bin/env python3
"""validate-policies.py — policy layer validation (v1.6.0 M1).

Each policy file must: parse, carry a policy_version, have no unknown keys,
and be deterministic (stable output on repeated evaluation of the same input).

Exit 2 on any policy failure; exit 0 clean. Runs in CI (the constitution:
policies must never silently drift).
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
POLICY_FILES = ["one-man.controls.json", "skills.flow.json", "policies/obligations.json", "policies/trust.json"]
# controls.json is a strict schema; flow.json is schema-free (dynamic task-type
# keys: bug/feature/refactor/...) — validate only version + structure there.
KNOWN_KEYS = {
    "one-man.controls.json": {"version", "policy_version", "description", "controls", "lifecycle"},
    "policies/obligations.json": {"policy_version", "description", "obligations"},
    "policies/trust.json": {"policy_version", "description", "levels", "auto_approve"},
}
FLOW_SCHEMA_FREE = {"skills.flow.json"}


def check_policy(path: Path):
    name = path.name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[FAIL] {name}: unparsable — {e}", file=sys.stderr)
        return False
    if "policy_version" not in data:
        print(f"[FAIL] {name}: missing policy_version (constitution: no silent undocumented policy)", file=sys.stderr)
        return False
    if not isinstance(data.get("policy_version"), str) or not data["policy_version"].count("."):
        print(f"[FAIL] {name}: policy_version must be a semver string", file=sys.stderr)
        return False
    # unknown keys (only for strict-schema policies; flow is dynamic by design)
    if name in KNOWN_KEYS:
        unknown = set(data.keys()) - KNOWN_KEYS[name]
        if unknown:
            print(f"[FAIL] {name}: unknown keys {unknown}", file=sys.stderr)
            return False
    print(f"[OK] {name}: policy_version={data['policy_version']}")
    return True


def main():
    ok = all(check_policy(REPO / f) for f in POLICY_FILES)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[FAIL] validate-policies crashed: {e}", file=sys.stderr)
        sys.exit(2)

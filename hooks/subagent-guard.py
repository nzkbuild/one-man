#!/usr/bin/env python3
"""SubagentStop hook — verifies subagent output is non-trivial and logs execution stats.

Checks: (a) agent completed without error, (b) output file exists and is non-trivial,
(c) agent did not produce empty garbage. Logs execution stats to ~/.claude/agent-log.jsonl
for later auditing.

READ-ONLY (except log append). Exit 2 + stderr on anomaly so model sees the flag.
Any crash → exit 0.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
LOG_FILE = HOME / ".claude" / "agent-log.jsonl"


def log_stats(entry):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    agent_id = payload.get("agent_id", "unknown")
    status = payload.get("status", "unknown")
    output_file = payload.get("output_file", "")

    ts = datetime.now(timezone.utc).isoformat()

    # Check output file size for non-triviality
    output_size = 0
    has_output = False
    if output_file:
        try:
            op = Path(output_file)
            if op.exists():
                output_size = op.stat().st_size
                has_output = True
        except Exception:
            pass

    log_stats({
        "ts": ts,
        "agent_id": agent_id,
        "status": status,
        "output_size": output_size,
    })

    # Flag anomalies
    issues = []
    if status == "error" or status == "failed":
        issues.append(f"Subagent {agent_id} terminated with status: {status}")
    elif has_output and output_size < 50:
        issues.append(f"Subagent {agent_id} produced trivial output ({output_size} bytes) — verify it actually completed the task")
    elif not has_output and status != "completed":
        issues.append(f"Subagent {agent_id} produced no output file — check if it ran at all")

    if not issues:
        sys.exit(0)

    for line in issues:
        print(line, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

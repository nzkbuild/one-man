#!/usr/bin/env python3
"""Hook latency monitor — logs per-hook execution duration to ~/.claude/hook-latency.jsonl.

Run this as a wrapper: instead of hook.sh, use `python hook-latency.py hook.sh`.
The wrapper records start/end timestamps and writes a JSON line with duration.

Not wired into settings.json directly — use it as a diagnostic wrapper when
investigating slow session startups. Example:
  bash latency-wrap.sh verify-edit.sh "$HOOK_INPUT"

READ-ONLY (except log append). Exit 0 always.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
LOG_FILE = HOME / ".claude" / "hook-latency.jsonl"


def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    hook_script = sys.argv[1]
    hook_input = os.environ.get("HOOK_INPUT", "")

    start = time.time()
    ts = datetime.now(timezone.utc).isoformat()

    exit_code = -1
    try:
        import subprocess
        result = subprocess.run(
            ["bash", hook_script],
            input=hook_input,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "HOOK_INPUT": hook_input},
        )
        exit_code = result.returncode
    except Exception:
        pass

    elapsed_ms = int((time.time() - start) * 1000)

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": ts,
                "hook": os.path.basename(hook_script),
                "exit_code": exit_code,
                "elapsed_ms": elapsed_ms,
            }) + "\n")
    except Exception:
        pass

    # Report if slow (>2s)
    if elapsed_ms > 2000:
        print(f"SLOW HOOK: {os.path.basename(hook_script)} took {elapsed_ms}ms", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

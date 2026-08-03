#!/usr/bin/env python3
"""Notification hook — alerts user on background task completion.

Detects task/agent completion notifications and pushes a desktop alert.
Uses the simplest mechanism available: writes to a marker file that
tools like PushNotification can read, or prints a terminal bell.

READ-ONLY. Exit 0 always — notifications are best-effort.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
ALERT_FILE = HOME / ".claude" / ".last-notification"


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    notification_type = payload.get("type", "")
    summary = payload.get("summary", "")

    if not summary:
        sys.exit(0)

    ts = datetime.now(timezone.utc).isoformat()

    try:
        ALERT_FILE.write_text(
            json.dumps({"ts": ts, "type": notification_type, "summary": summary}) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    # Terminal bell + summary — the simplest cross-platform notification
    # The model can read this marker file to surface pending alerts
    print(f"\a[Notification] {summary}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

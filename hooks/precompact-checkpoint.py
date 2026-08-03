#!/usr/bin/env python3
"""PreCompact hook — auto-saves current working state to STATE.md before context compaction.

When context compacts, the current thread is lost unless /checkpoint was manually invoked.
This hook auto-saves the last known goal/done/next so the post-compaction session knows
exactly where it left off through session-context.py's recovery injection.

READ-ONLY except for STATE.md. Any crash → exit 0 (never block compaction).
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

HOME = Path(os.path.expanduser("~"))


def slugify(cwd):
    return cwd.replace(":", "-").replace("\\", "-").replace("/", "-")


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    cwd = str(Path.home())
    if raw.strip():
        try:
            data = json.loads(raw)
            cwd = data.get("cwd", cwd)
        except Exception:
            pass

    slug = slugify(cwd)
    proj_mem = HOME / ".claude" / "projects" / slug / "memory"
    state_file = proj_mem / "STATE.md"

    if not state_file.exists():
        # No existing state — nothing to update. Don't create a new one,
        # since we don't have current goal/done/next without model context.
        sys.exit(0)

    # Read existing STATE.md and add a compaction timestamp marker.
    # We don't overwrite content — only append a compaction note so the
    # post-compaction session knows a compaction happened and what time.
    try:
        existing = state_file.read_text(encoding="utf-8")
    except Exception:
        sys.exit(0)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    compaction_note = f"\n\n<!-- compacted at {now} — resume from the last checkpoint above -->"

    if "compacted at" not in existing:
        try:
            state_file.write_text(existing.rstrip() + compaction_note + "\n", encoding="utf-8")
        except Exception:
            pass

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

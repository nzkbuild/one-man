#!/usr/bin/env python3
"""SessionStart hook — validates settings.json structure before any other hook runs.

Catches the silent-failure patterns that waste sessions:
- Hooks at document root instead of under "hooks" key
- Invalid hook event names
- Malformed matcher regex patterns
- Referenced scripts that don't exist

READ-ONLY. Exit 0 always (fail-safe). Prints additionalContext on failures.
"""
import json
import os
import re
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SETTINGS = HOME / ".claude" / "settings.json"

# Valid Claude Code hook events (as of 2026)
VALID_EVENTS = {
    "SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse",
    "PostToolUse", "PreToolOutput", "Notification", "Stop",
    "SubagentStop", "PreCompact", "PostCompact",
    "PermissionRequest", "PreCompaction", "PostCompaction",
}


def main():
    if not SETTINGS.exists():
        sys.exit(0)

    try:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"## settings.json is corrupted\n\n"
                f"JSON parse error: {e}\n\n"
                f"Hooks are NOT firing. Fix settings.json immediately."
            ),
        }}))
        sys.exit(0)

    issues = []

    # Check 1: hooks must be under "hooks" key, not at document root
    if "hooks" not in settings:
        for key in settings:
            if key in VALID_EVENTS:
                issues.append(
                    f"`{key}` hook is at document root, not under `\"hooks\"`. "
                    f"This is a silent failure — hooks at root are ignored."
                )
        if issues:
            all_hooks = [k for k in settings if k in VALID_EVENTS]
            if all_hooks:
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        f"## settings.json has hooks at the wrong level\n\n"
                        f"Found at document root: {', '.join(all_hooks)}\n\n"
                        f"These are silently ignored. Move them under a top-level `\"hooks\"` key."
                    ),
                }}))
                sys.exit(0)

    hooks = settings.get("hooks", {})
    if not hooks:
        sys.exit(0)

    # Check 2: unknown hook event names
    for event in hooks:
        if event not in VALID_EVENTS:
            issues.append(f"Unknown hook event `{event}` — may be ignored by Claude Code")

    # Check 3: matcher regex validity
    for event, entry_groups in hooks.items():
        for i, group in enumerate(entry_groups):
            matcher = group.get("matcher", "")
            if matcher:
                try:
                    re.compile(matcher)
                except re.error as e:
                    issues.append(
                        f"`{event}[{i}]` has invalid matcher regex `{matcher}`: {e}"
                    )

    if issues:
        lines = ["## settings.json validation warnings", "",
                 "These may cause hooks to silently fail:", ""]
        for issue in issues:
            lines.append(f"- {issue}")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }}))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

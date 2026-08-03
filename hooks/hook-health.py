#!/usr/bin/env python3
"""SessionStart hook — verifies all wired hook scripts exist and are functional.

Silent hook failures (wrong key, missing file, broken path) are the most common
cause of discipline drift. This check runs at every SessionStart so a broken
hook is caught immediately, not silently ignored for weeks.

READ-ONLY. Never writes, never runs the hooks it checks. Exit 0 always (fail-safe).
Prints additionalContext on failures so the model sees the gap on prompt one.
"""
import json
import os
import sys
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
SETTINGS = HOME / ".claude" / "settings.json"


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def main():
    settings_text = read_text(SETTINGS)
    if not settings_text:
        sys.exit(0)

    try:
        settings = json.loads(settings_text)
    except Exception:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "## Hook health: settings.json is not valid JSON\n"
                "Hooks are NOT firing. Fix the JSON syntax in settings.json immediately."
            ),
        }}))
        sys.exit(0)

    hooks_config = settings.get("hooks", {})
    if not hooks_config:
        sys.exit(0)

    issues = []

    for event_name, entry_groups in hooks_config.items():
        for group in entry_groups:
            for hook in group.get("hooks", []):
                cmd = hook.get("command", "")
                if not cmd:
                    continue

                # Extract script path from command. Handles:
                #   bash "C:\path\to\script.sh"
                #   "C:/Program Files/nodejs/node.exe" "C:/path/to/script.mjs"
                #   python script.py (unquoted — unusual but valid)
                import re
                paths = re.findall(r'"([^"]+)"', cmd)
                # Filter to paths ending in .sh/.py/.mjs/.js — the actual script
                script_paths = [p for p in paths if p.endswith(('.sh', '.py', '.mjs', '.js'))]
                if not script_paths:
                    continue
                script = script_paths[-1]  # last path is usually the script

                if not Path(script).exists():
                    issues.append(f"`{event_name}` hook script NOT FOUND: `{script}`")
                    continue

                # Quick parse check for Python scripts
                if script.endswith('.py'):
                    try:
                        import py_compile
                        py_compile.compile(script, doraise=True)
                    except Exception as e:
                        issues.append(f"`{event_name}` Python script has syntax error: `{script}` — {e}")

    if not issues:
        sys.exit(0)

    lines = ["## Hook health: issues detected", "",
             "These hook scripts are wired but broken. Fix them — the harness is "
             "currently running without these protections:", ""]
    for issue in issues:
        lines.append(f"- {issue}")

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n".join(lines),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

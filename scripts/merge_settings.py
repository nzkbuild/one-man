#!/usr/bin/env python3
"""merge_settings.py — deep-merge one-man hooks + permissions into a user's
existing ~/.claude/settings.json WITHOUT clobbering their env/model/permissions.

Usage:
  python merge_settings.py <settings_path_or_home> <claude_home>
  python merge_settings.py <claude_home> <claude_home> --init   # no existing file

Rules (ponytail: smallest correct merge):
- hooks: REPLACE with the one-man hook map (absolute paths resolved to claude_home).
- permissions: MERGE — union new deny/allow/ask, keep the user's existing entries.
- env/model/baseURL/plugins/everything else: PRESERVE verbatim (user ownership).
"""
import json
import os
import sys

HOOK_EVENTS = [
    "SessionStart", "PreCompact", "UserPromptSubmit", "PreToolUse",
    "PostToolUse", "SubagentStop", "Notification", "Stop",
]


def basename_cmd(script):
    """Build the hook command with an absolute path into claude_home."""
    return f'bash "{os.path.join(CLAUDE_HOME, "hooks", script)}"'


def build_hooks(scripts):
    """Construct the one-man hooks map from ordered (event, matcher, scripts)."""
    hooks = {}
    for event, matcher, names in scripts:
        hooks.setdefault(event, []).append({
            "matcher": matcher,
            "hooks": [{"type": "command", "command": basename_cmd(n)} for n in names],
        })
    return hooks


def main():
    global CLAUDE_HOME
    init = "--init" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--init"]
    if not args:
        print("usage: merge_settings.py <settings.json | --init> <claude_home>", file=sys.stderr)
        sys.exit(1)

    if init:
        CLAUDE_HOME = args[0]
        existing = {}
    else:
        settings_path, CLAUDE_HOME = args
        try:
            existing = json.load(open(settings_path))
        except (OSError, json.JSONDecodeError) as e:
            print(f"could not read {settings_path}: {e}", file=sys.stderr)
            sys.exit(1)

    # Order matters: matcher specificity. One-man hook map.
    SCRIPTS = [
        # SessionStart: memory context
        ("SessionStart", "startup", ["session-context.sh"]),
        ("SessionStart", "resume", ["session-context.sh"]),
        ("SessionStart", "compact", ["session-context.sh"]),
        # SessionStart: health + audit
        ("SessionStart", "startup", ["settings-validate.sh", "project-audit.sh", "hook-health.sh"]),
        ("SessionStart", "resume", ["settings-validate.sh", "project-audit.sh", "hook-health.sh"]),
        # SessionStart: cache heal (node)
        ("SessionStart", "startup|resume", ["context-mode-cache-heal.mjs"]),
        # Mid-turn
        ("PreCompact", "*", ["precompact-checkpoint.sh"]),
        ("UserPromptSubmit", "*", ["task-triage.sh", "prompt-guard.sh", "phase-gate.sh"]),
        ("PreToolUse", "Bash|PowerShell|Write|Edit|NotebookEdit", ["danger-guard.sh", "discipline-guard.sh"]),
        ("PostToolUse", "Write|Edit|NotebookEdit", ["verify-edit.sh"]),
        ("PostToolUse", "Bash|PowerShell", ["dep-guard.sh"]),
        ("SubagentStop", "*", ["subagent-guard.sh"]),
        ("Notification", "*", ["notify-alert.sh"]),
        ("Stop", "*", ["verify-turn.sh"]),
        ("SessionEnd", "*", ["retrospective.sh"]),
    ]

    new = dict(existing)
    # 1. hooks: replace wholesale with one-man's.
    new["hooks"] = build_hooks(SCRIPTS)

    # 2. permissions: union, preserving user's.
    up = (existing.get("permissions") or {}).copy()
    one_man = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "..", "templates", "settings.json.template"))).get("permissions", {})
    for key in ("allow", "deny", "ask"):
        merged = list(dict.fromkeys((one_man.get(key) or []) + (up.get(key) or [])))
        up[key] = merged
    new["permissions"] = up

    # 3. everything else (env, model, baseURL, plugins) preserved automatically.

    out = os.path.join(CLAUDE_HOME, "settings.json")
    json.dump(new, open(out, "w"), indent=2)
    print(f"merged settings written to {out}")
    print(f"  hooks: {len(new.get('hooks', {}))} events wired")
    print("  permissions: preserved user rules + one-man defaults merged")
    print("  env/model/baseURL: PRESERVED (user-owned)")


if __name__ == "__main__":
    main()

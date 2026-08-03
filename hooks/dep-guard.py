#!/usr/bin/env python3
"""PostToolUse hook — detects dependency installs and reminds the model to audit them.

Warns when npm/pnpm/yarn/pip install/add commands are detected in Bash/PowerShell
tool calls. The reminder asks: is this dep already installed? Is it maintained?
Could stdlib or an existing dep cover this?

TOKEN-AWARE (same fix as danger-guard): quoted strings, heredocs, and comments
are redacted before matching so a *mention* of `npm install` in config text,
docs, or grep patterns does not trigger a false positive. An actual
`pnpm add lodash` still fires.

READ-ONLY. Exit 2 + stderr on detection so the model sees the nudge.
Any crash → exit 0 (fail-safe).
"""
import json
import os
import re
import sys

# `add` is the unambiguous "install a NEW dependency" verb; `install`/`i`
# appear in prose constantly ("run pnpm install to set up") and fire falsely.
# So detect only `add <pkg>` (which grabs lodash, @scope/pkg, any real name)
# plus `pip install <pkg>`. This keeps the nudge useful with zero prose noise.
DEP_PATTERNS = [
    (re.compile(r"\b(pnpm|npm|yarn)\s+add\s+(\S+)", re.IGNORECASE), "package"),
    (re.compile(r"\b(pip3?)\s+install\s+(\S+)", re.IGNORECASE), "pip"),
]


def strip_inactive(command):
    """Redact quoted strings, heredocs, and comments so pattern matching only
    sees executable tokens. A literal `npm install` in a doc string, heredoc,
    or config file text is inspection — not a real install."""
    out = command

    # Heredocs: <<'EOF' ... EOF — blank the body.
    out = re.sub(
        r"(<<['\"]?\w+['\"]?.*?\n)(.*?)^\s*\w+\s*$",
        lambda m: m.group(1) + (" " * len(m.group(2))) + "\n",
        out,
        flags=re.M | re.S,
    )

    # Quoted strings '' " " ` ` — blank the content.
    out = re.sub(r"('[^']*'|\"[^\"]*\"|`[^`]*`)", lambda m: " " * len(m.group(1)), out)

    # Comments # ... — blank to end of line, unless # is mid-word (URLs, #!/bin).
    out = re.sub(r"(?<!\w)#[^\n]*", lambda m: " " * len(m.group(0)), out)

    return out


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Bash", "PowerShell"):
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        sys.exit(0)

    detections = []
    active = strip_inactive(command)
    for pattern, kind in DEP_PATTERNS:
        m = pattern.search(active)
        if m:
            if kind == "package":
                pkg_name = m.group(2) if m.lastindex and m.lastindex >= 2 else "?"
                detections.append(f"package `{pkg_name}`")
            elif kind == "pip":
                pkg_name = m.group(2) if m.lastindex and m.lastindex >= 2 else "?"
                detections.append(f"pip package `{pkg_name}`")

    if not detections:
        sys.exit(0)

    names = ", ".join(detections)
    print(
        f"New dependency detected: {names}. Before adding: (1) check if already in "
        f"package.json, (2) verify last commit date + maintainer count, (3) ask: can "
        f"stdlib or an existing dep cover this? 3 lines of code > 3 kilobytes of dependency.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

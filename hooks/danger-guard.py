#!/usr/bin/env python3
"""PreToolUse hook — blocks dangerous commands before they execute.

Catches destructive shell invocations, secret-file writes, and force-push
patterns that a careless model or a truncated prompt might produce.

READ-ONLY. Never writes files, never runs commands. Exit 2 on stderr to
surface the block to the model; exit 0 to allow the tool call through.
Any crash → exit 0 (fail-open, never block the user).

TOKEN-AWARE: before matching, the command is redacted of quoted strings,
heredocs, and comments. A literal `rm -rf` inside `grep 'rm -rf'`, a doc
string, or a heredoc is INSPECTION, not execution — it must not block.
An actual `rm -rf` (unquoted, outside quotes/heredoc/comment) still blocks.

Reads the hook payload JSON from HOOK_INPUT env var.
"""
import json
import os
import re
import sys

# ---- Danger patterns ----
# Each entry: (re.compile(...), severity, human message)
# Severity: "block" = exit 2 (hard block), "warn" = exit 2 but with warning language

BLOCK_PATTERNS = [
    # rm -rf variants — require `rm` at a command boundary so a bare word
    # "rm" mid-sentence (`echo looks like rm -rf`) is not treated as a command.
    (
        re.compile(r"(?:^|[;&|(\n])\s*rm\s.*-(r[^a-z]*f|f[^a-z]*r)\b", re.IGNORECASE),
        "block",
        "Dangerous command blocked: `rm -rf` detected. Use a reversible approach or confirm with the user first.",
    ),
    # Force push
    (
        re.compile(r"git\s+push\s+.*(--force|--force-with-lease)", re.IGNORECASE),
        "block",
        "Blocked: `git push --force`. Never force-push to shared branches. If this is intentional, the user will tell you explicitly.",
    ),
    # Hard reset
    (
        re.compile(r"git\s+reset\s+--hard", re.IGNORECASE),
        "block",
        "Blocked: `git reset --hard`. This destroys uncommitted work. Use `git stash` or confirm with the user.",
    ),
    # Curl-pipe-bash
    (
        re.compile(r"curl\s.*\|\s*(ba)?sh", re.IGNORECASE),
        "block",
        "Blocked: `curl | bash`. Never pipe remote content directly into a shell. Download, inspect, then run.",
    ),
    # Chmod 777
    (
        re.compile(r"chmod\s.*777", re.IGNORECASE),
        "block",
        "Blocked: `chmod 777`. World-writable permissions are a security risk. Use more restrictive permissions.",
    ),
    # git clean -fdx (destructive, removes untracked+ignored files)
    (
        re.compile(r"git\s+clean\s+.*(-f|--force)", re.IGNORECASE),
        "block",
        "Blocked: `git clean -f`. Irreversibly deletes untracked and ignored files. Use `git clean -n` to preview first.",
    ),
]

WRITE_PATTERNS = [
    # Writing to .env or credentials files
    (
        re.compile(r"(\.env|credentials\.json|secrets\.json|id_rsa|\.pem|service-account\.json)$", re.IGNORECASE),
        "block",
        "Blocked: writing to a secrets file. Never write credentials or environment files. Reference secrets by key name only.",
    ),
]

SHELL_COMMAND_PATTERNS = [
    # npm install -g (global install — usually wrong)
    (
        re.compile(r"(npm|pnpm|yarn)\s+(install|add|i)\s+-g\b", re.IGNORECASE),
        "warn",
        "Warning: global package install detected. Prefer local installs. If intentional, the user will override.",
    ),
    # pip install without --user or in a venv context
    (
        re.compile(r"pip\d?\s+install\s+(?!.*(--user|-e|\.))", re.IGNORECASE),
        "warn",
        "Warning: `pip install` without `--user`. Prefer virtual environments. If intentional, proceed.",
    ),
]


def strip_inactive(command):
    """Redact quoted strings, heredocs, and comments so pattern matching
    only sees executable tokens, not string literals / inspection text.

    Returns a version of `command` where the *content inside* quotes,
    heredocs, and comments is replaced with spaces. Executable structure
    (`rm -rf /tmp`) survives; `grep 'rm -rf'` does not match.

    Deliberately conservative: a quoted string is assumed to be data, not
    code. This is the correct bias for a guard — blocking inspection is
    worse than a rare missed in-string match, and the harness's
    acceptEdits prompt remains a second layer.
    """
    out = command

    # 1. Heredocs: <<'EOF' ... EOF  or  <<EOF ... EOF  — redact the body.
    def _drop_heredoc(m):
        return m.group(1) + (" " * len(m.group(2))) + "\n"

    # Simple delimiter heredocs (<<'X', <<X)
    out = re.sub(
        r"(<<['\"]?\w+['\"]?.*?\n)(.*?)^\s*\w+\s*$",
        _drop_heredoc,
        out,
        flags=re.M | re.S,
    )

    # 2. Quoted strings: '', "", backticks — redact the content.
    #    Keep the quotes themselves as markers (they rarely appear in executable
    #    positions, and keeping them preserves line structure).
    out = re.sub(r"('[^']*'|\"[^\"]*\"|`[^`]*`)", lambda m: " " * len(m.group(1)), out)

    # 3. Comments # ... — redact to end of line.
    #    Crude but safe for shell: a # mid-command is rare and a false
    #    negative here (blocking) is the safe direction.
    #    Do NOT treat `#` as a comment if preceded by a word char (URLs, #!/bin).
    out = re.sub(r"(?<!\w)#[^\n]*", lambda m: " " * len(m.group(0)), out)

    return out


def scan_command(command):
    """Return list of (severity, message) findings for a shell command."""
    active = strip_inactive(command)
    issues = []
    for pattern, severity, msg in BLOCK_PATTERNS + SHELL_COMMAND_PATTERNS:
        if pattern.search(active):
            issues.append((severity, msg))
    return issues


def main():
    raw = os.environ.get("HOOK_INPUT", "")
    if not raw.strip():
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    issues = []

    # Check Bash/PowerShell commands
    if tool_name in ("Bash", "PowerShell"):
        command = tool_input.get("command", "")
        if command:
            issues.extend(scan_command(command))

    # Check Write tool paths
    if tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        if file_path:
            for pattern, severity, msg in WRITE_PATTERNS:
                if pattern.search(file_path):
                    issues.append((severity, msg))
                if ".env" in file_path.lower() and "example" not in file_path.lower():
                    if not file_path.lower().endswith(".env.example"):
                        issues.append(("block", f"Blocked: writing to `{os.path.basename(file_path)}`. Never create .env files with real values. Use .env.example with placeholder keys only."))

    if not issues:
        sys.exit(0)

    blocks = [m for s, m in issues if s == "block"]
    warns = [m for s, m in issues if s == "warn"]

    lines = []
    if blocks:
        lines.append("## BLOCKED — dangerous operation prevented\n")
        for m in blocks:
            lines.append(f"- {m}")
    if warns:
        if lines:
            lines.append("")
        lines.append("## Warnings\n")
        for m in warns:
            lines.append(f"- {m}")

    lines.append("\nTo override: the user must explicitly tell you to proceed with this specific command.")

    for line in lines:
        print(line, file=sys.stderr)

    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

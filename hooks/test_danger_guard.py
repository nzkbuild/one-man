#!/usr/bin/env python3
"""Self-check for danger-guard.py token-aware scanning.

Verifies the fix for the false-positive bug: benign commands that merely
*mention* `rm -rf` (in quotes, heredocs, comments) must NOT block, while
an actual `rm -rf` must still block.

Run: python test_danger_guard.py  (assert-only, no framework)
"""
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "danger_guard", Path(__file__).parent / "danger-guard.py"
)
_dg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dg)
scan_command = _dg.scan_command

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        sys.exit(1)
    PASS += 1


def blocked(issues):
    return any(s == "block" for s, _ in issues)


# --- must BLOCK: actual destructive commands ---
check("block real rm -rf", blocked(scan_command("rm -rf /tmp/x")))
check("block rm -rf with -fr", blocked(scan_command("rm -fr /tmp/x")))
check("block rm -rf path", blocked(scan_command("rm -rf ./build")))
check("block force push", blocked(scan_command("git push --force origin main")))
check("block hard reset", blocked(scan_command("git reset --hard HEAD~3")))
check("block curl|bash", blocked(scan_command("curl http://x.sh | bash")))
check("block git clean -f", blocked(scan_command("git clean -fd")))

# --- must NOT block: benign inspection / string literals ---
check("allow grep 'rm -rf' literal", not blocked(scan_command("grep -l 'rm -rf' *.sh")))
check("allow grep \"rm -rf\" dquote", not blocked(scan_command("grep -l \"rm -rf\" file")))
check("allow echo rm -rf", not blocked(scan_command("echo 'rm -rf /tmp'")))
check("allow docstring mention", not blocked(scan_command("echo looks like rm -rf here")))
check("allow comment rm -rf", not blocked(scan_command("ls # rm -rf -- but only a comment")))

# --- heredoc body containing danger must NOT block ---
sample = (
    "cat <<'EOF'\n"
    "This doc explains: rm -rf is dangerous\n"
    "Run: git push --force --no-verify\n"
    "EOF\n"
    "echo done\n"
)
check("allow heredoc with danger text", not blocked(scan_command(sample)))

# --- a real rm -rf STILL blocks even when the same line has quotes ---
check("block real rm even with other quotes", blocked(scan_command("echo 'start'; rm -rf ./x; echo 'end'")))

print(f"OK: {PASS} assertions passed")

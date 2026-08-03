#!/usr/bin/env python3
"""Self-check for dep-guard.py token-aware dependency detection."""
import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("dep_guard", Path(__file__).parent / "dep-guard.py")
_dg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dg)
strip_inactive = _dg.strip_inactive
DEP_PATTERNS = _dg.DEP_PATTERNS


def detect(cmd):
    active = strip_inactive(cmd)
    for pattern, kind in DEP_PATTERNS:
        if pattern.search(active):
            return kind
    return None


PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        sys.exit(1)
    PASS += 1


# must DETECT: actual NEW-dep installs
check("real pnpm add", detect("pnpm add lodash") == "package")
check("real npm add", detect("npm add express") == "package")
check("real pip install", detect("pip install requests") == "pip")
check("pnpm add -D typescript", detect("pnpm add -D typescript") == "package")
check("scoped add", detect("pnpm add @scope/pkg") == "package")

# must NOT detect: prose / config / heredoc / comment / bare installs
check("quoted mention", detect('echo "npm install express"') is None)
check("config text mention", detect('deny: "Bash(npm install -g:*)"') is None)
check("heredoc mention", detect("cat <<'EOF'\nnpm install foo\nEOF\necho done") is None)
check("comment mention", detect("ls  # npm add foo") is None)
check("doc prose rely on npm install", detect("run pnpm install to set up") is None)
check("bare install --dev", detect("pnpm install --dev") is None)
check("bare i -D", detect("pnpm i -D") is None)
check("bare install no arg", detect("pnpm install") is None)
# install (without add) even with a name is prose-ish for pnpm/npm/yarn
check("npm install express alone", detect("npm install express") is None)

print(f"OK: {PASS} assertions passed")

#!/usr/bin/env python3
"""Mechanical drift audit — finds problems that live BETWEEN files.

Per-file linters (ruff/mypy) catch defects inside one file. They are structurally
blind to the failure modes that accumulate as a project evolves:

  - code that is unreachable from the entry point (abandoned layers)
  - the same concept implemented two or three times (which one is real?)
  - infrastructure that is fully built but wired to nothing
  - security controls that exist in config but are never enforced in code
  - money/auth paths with no test covering them

Those are the ones that make a project quietly stop matching its own intent. This
script reports them; it NEVER modifies or deletes anything. Deleting "dead" code is
a judgment call that needs a human, because a file can be reachable in ways static
analysis cannot see (entry points in Docker, cron, CI, dynamic import).

Usage:  python audit.py [project_dir]
Exit:   0 always (a report is not a failure)
"""
# subprocess args below are hardcoded literal lists; no user input reaches them.
# ruff: noqa: S603

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SKIP_DIRS = {
    "node_modules", "venv", ".venv", "env", "__pycache__", ".git", "dist", "build",
    ".pytest_cache", ".codegraph", ".mypy_cache", ".ruff_cache", "migrations",
    "site-packages", ".next", "target", ".akar",
}

# Words that mark a code path where a silent bug is expensive.
CRITICAL_WORDS = (
    "payment", "refund", "settle", "price", "amount", "balance", "wallet", "invoice",
    "charge", "auth", "password", "secret", "permission", "webhook",
    "financial", "ledger", "transaction", "credential", "encrypt", "decrypt",
)

# Words above are too broad on their own: "session" matches session *plumbing*
# (listSessions, setSessionPid) as often as real auth, and "token" matches an API
# token budget as often as a credential. Flagging those as CRITICAL is the noise
# that trains a user to ignore the audit, so they only count with a verb that
# implies a security decision.
AMBIGUOUS_WORDS = ("session", "token", "admin", "login", "access")
SECURITY_VERBS = ("valid", "verify", "check", "authorize", "authenticate", "grant",
                  "deny", "sign", "revoke", "require", "guard", "protect", "reset")


def is_critical(name: str, path_hint: str) -> bool:
    hay = f"{name} {path_hint}".lower()
    if any(w in hay for w in CRITICAL_WORDS):
        return True
    if any(w in hay for w in AMBIGUOUS_WORDS):
        return any(v in hay for v in SECURITY_VERBS)
    return False

findings: list[tuple[int, str, str]] = []   # (severity 0=critical, title, detail)


def add(sev: int, title: str, detail: str) -> None:
    findings.append((sev, title, detail))


def py_files() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.py"):
        if not any(part in SKIP_DIRS for part in p.parts):
            out.append(p)
    return out


def mod_name(p: Path) -> str:
    """Dotted module name relative to the project root."""
    rel = p.relative_to(ROOT).with_suffix("")
    parts = [x for x in rel.parts if x != "__init__"]
    return ".".join(parts)


def imports_of(p: Path) -> set[str]:
    """Module names imported by this file. Best-effort; unparseable files yield none."""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, ValueError, OSError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                found.add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            for a in node.names:                      # `from pkg import module`
                found.add(f"{node.module}.{a.name}")
    return found


# ---------------------------------------------------------------------------------
# 1. Reachability — what is orphaned?
# ---------------------------------------------------------------------------------
def _declared_entry_modules() -> set[str]:
    """Module names launched by containers/CI/scripts.

    Containers declare their own entry points (e.g. `CMD ["python", "-m",
    "app.api.health"]`). Missing these produces false "unreachable" findings for
    files that are in fact a service's main module.
    """
    found: set[str] = set()
    for pat in ("docker/*", "Dockerfile*", "docker-compose*.yml", "Procfile",
                ".github/workflows/*.yml", "scripts/*.sh", "Makefile"):
        for cfg in ROOT.glob(pat):
            if not cfg.is_file():
                continue
            text = cfg.read_text(encoding="utf-8", errors="ignore")
            # Separator must tolerate Docker's JSON-array form, where tokens are
            # split by quotes and commas: CMD ["python", "-m", "app.api.health"]
            sep = r"[\s,\"']+"
            found.update(re.findall(rf"python\d?{sep}-m{sep}([\w.]+)", text))
            for hit in re.findall(rf"python\d?{sep}([\w/\\.]+\.py)", text):
                found.add(hit.replace("/", ".").replace("\\", ".")[:-3])
    # Tool modules launched via -m are not application entry points.
    found -= {"pytest", "flake8", "alembic", "pip", "mypy", "ruff", "black", "uvicorn",
              "gunicorn", "venv", "http.server", "coverage", "unittest"}
    return found


def check_reachability(files: list[Path]) -> set[Path]:
    by_mod = {mod_name(p): p for p in files}
    entries = [p for p in files
               if p.name in ("main.py", "app.py", "manage.py", "__main__.py", "wsgi.py",
                             "asgi.py", "server.py", "bot.py", "cli.py")
               and len(p.relative_to(ROOT).parts) <= 2]

    declared = _declared_entry_modules()
    entries += [p for m, p in by_mod.items() if m in declared and p not in entries]

    if not entries:
        return set()

    reached: set[Path] = set()
    queue = list(entries)
    while queue:
        cur = queue.pop()
        if cur in reached:
            continue
        reached.add(cur)
        for imp in imports_of(cur):
            for cand in (imp, imp.rsplit(".", 1)[0] if "." in imp else imp):
                tgt = by_mod.get(cand)
                if tgt and tgt not in reached:
                    queue.append(tgt)

    # Tests legitimately are not reachable from main; they are their own entry points.
    orphans = [p for p in files
               if p not in reached
               and "test" not in p.name
               and "tests" not in p.parts
               and p.name != "__init__.py"
               and not p.name.startswith("conftest")]
    if orphans:
        loc = sum(len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
                  for p in orphans)
        names = ", ".join(sorted(str(p.relative_to(ROOT)) for p in orphans)[:12])
        add(1, f"{len(orphans)} file(s) unreachable from the entry point ({loc} LOC)",
            f"Not imported, directly or transitively, from {entries[0].name}: {names}. "
            "Either an abandoned layer to delete, or something that SHOULD be wired and "
            "isn't. Confirm against Docker/CI/cron entry points before deleting.")
    return reached


# ---------------------------------------------------------------------------------
# 2. Duplicate concepts — which implementation is real?
# ---------------------------------------------------------------------------------
def check_duplicate_concepts(files: list[Path]) -> None:
    classes: dict[str, list[str]] = {}
    for p in files:
        if "test" in p.name or "tests" in p.parts:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, ValueError, OSError):
            continue
        for node in tree.body:                       # top-level definitions only
            if isinstance(node, ast.ClassDef):
                classes.setdefault(node.name, []).append(str(p.relative_to(ROOT)))
    dupes = {k: v for k, v in classes.items() if len(v) > 1}
    if dupes:
        detail = "; ".join(f"`{k}` in {' + '.join(v)}" for k, v in list(dupes.items())[:8])
        add(1, f"{len(dupes)} concept(s) defined in more than one place",
            f"{detail}. Two classes with one name means callers may use different "
            "shapes for the same idea — a common source of silent field mismatches.")


# ---------------------------------------------------------------------------------
# 3. Config promises vs code reality — the 'looks secured but isn't' class
# ---------------------------------------------------------------------------------
def _env_keys() -> set[str]:
    """Uppercase KEY= names declared in .env / .env.example."""
    keys: set[str] = set()
    for ef in (ROOT / ".env.example", ROOT / ".env"):
        if not ef.is_file():
            continue
        for line in ef.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"^([A-Z][A-Z0-9_]{2,})=", line.strip())
            if m:
                keys.add(m.group(1))
    return keys


def _classify_keys(keys: set[str], corpus: dict[str, str]) -> tuple[list[str], list[str]]:
    """Split keys into (never referenced, referenced only in config/settings)."""
    blob = "\n".join(corpus.values())
    never, config_only = [], []
    for k in sorted(keys):
        lower = k.lower()
        if k not in blob and lower not in blob:
            never.append(k)
            continue
        # Referenced only where config is loaded => declared but never enforced.
        users = [f for f, t in corpus.items()
                 if (k in t or lower in t)
                 and "config" not in f and "settings" not in f]
        if not users:
            config_only.append(k)
    return never, config_only


def check_config_vs_code(files: list[Path]) -> None:
    keys = _env_keys()
    if not keys:
        return

    corpus: dict[str, str] = {}
    for p in files:
        if "test" not in p.name and "tests" not in p.parts:
            corpus[str(p.relative_to(ROOT))] = p.read_text(encoding="utf-8", errors="ignore")

    never, config_only = _classify_keys(keys, corpus)

    # Match the control itself, not merely the feature it belongs to: WEBHOOK_SECRET
    # is a security control, WEBHOOK_URL and WEBHOOK_PORT are plain configuration.
    security = ("SECRET", "TOKEN", "PASSWORD", "_KEY", "APIKEY", "CREDENTIAL",
                "RATE_LIMIT", "ADMIN", "AUTH", "ENCRYPT", "SIGNATURE", "SALT")
    benign = ("_URL", "_PORT", "_HOST", "_NAME", "_ENABLED", "_TIMEOUT", "_PATH")

    def is_security(k: str) -> bool:
        if any(b in k for b in benign):
            return False
        return any(s in k for s in security)

    sec_never = [k for k in never if is_security(k)]
    sec_cfg = [k for k in config_only if is_security(k)]

    if sec_never:
        add(0, f"{len(sec_never)} security setting(s) declared in config but NEVER read",
            f"{', '.join(sec_never)}. The config implies a protection that does not "
            "exist in code — the most dangerous kind of drift, because the project "
            "looks configured correctly.")
    if sec_cfg:
        add(0, f"{len(sec_cfg)} security setting(s) loaded but never enforced",
            f"{', '.join(sec_cfg)}. Read into settings and then unused — nothing "
            "validates against them at runtime.")
    other = [k for k in never if k not in sec_never]
    if other:
        add(2, f"{len(other)} config key(s) unused in code", ", ".join(other[:12]))


# ---------------------------------------------------------------------------------
# 4. Critical paths with no test covering them
# ---------------------------------------------------------------------------------
def check_critical_coverage(files: list[Path]) -> None:
    test_blob = ""
    for p in files:
        if "test" in p.name or "tests" in p.parts:
            test_blob += p.read_text(encoding="utf-8", errors="ignore")
    if not test_blob:
        add(0, "No tests exist at all",
            "Nothing verifies behavior. Linting proves syntax, not correctness.")
        return

    uncovered: list[str] = []
    for p in files:
        if "test" in p.name or "tests" in p.parts:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, ValueError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            name = node.name
            if name.startswith("_") or len(name) < 4:
                continue
            if is_critical(name, p.stem) and name not in test_blob:
                uncovered.append(f"{p.relative_to(ROOT)}::{name}")
    if uncovered:
        add(0, f"{len(uncovered)} critical function(s) with no test naming them",
            "; ".join(uncovered[:14]) + ". These touch money, auth, or secrets — "
            "exactly where an untested edge case is expensive.")


# ---------------------------------------------------------------------------------
# 5. Existing tool debt (summarized, not re-listed line by line)
# ---------------------------------------------------------------------------------
def check_tool_debt() -> None:
    def run(cmd: list[str]) -> str:
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
            return r.stdout + r.stderr
        except (OSError, subprocess.SubprocessError):
            return ""

    out = run(["ruff", "check", "--output-format", "concise", "."])
    if out:
        m = re.search(r"Found (\d+) error", out)
        sec = len(re.findall(r": S\d{3}", out))
        if m and int(m.group(1)) > 0:
            add(2 if sec == 0 else 1, f"ruff: {m.group(1)} finding(s), {sec} security-tagged",
                "Run `ruff check .` for the list.")

    out = run(["python", "-m", "mypy", ".", "--no-error-summary", "--no-pretty"])
    errs = [ln for ln in out.splitlines() if ": error:" in ln]
    if errs:
        none_bugs = [e for e in errs if "None" in e]
        add(1, f"mypy: {len(errs)} type error(s), {len(none_bugs)} involving None",
            "None-related errors are latent crashes: a value that can be absent is "
            "used as if it never is. Run `mypy .` for the list.")


def ts_files() -> list[Path]:
    out = []
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for p in ROOT.rglob(ext):
            if not any(part in SKIP_DIRS for part in p.parts) and ".d.ts" not in p.name:
                out.append(p)
    return out


def check_ts_project(files: list[Path]) -> None:
    """Drift checks for TS/JS. Regex-based: no AST parser is available offline, so
    this is deliberately conservative — it reports only high-confidence signals."""
    corpus = {str(p.relative_to(ROOT)): p.read_text(encoding="utf-8", errors="ignore")
              for p in files}
    blob = "\n".join(corpus.values())

    # Config promises vs code reality — same dangerous class as the Python check.
    keys = _env_keys()
    if keys:
        never = [k for k in sorted(keys) if k not in blob]
        security = ("SECRET", "TOKEN", "PASSWORD", "_KEY", "APIKEY", "CREDENTIAL",
                    "RATE_LIMIT", "ADMIN", "AUTH", "ENCRYPT", "SIGNATURE", "SALT")
        benign = ("_URL", "_PORT", "_HOST", "_NAME", "_ENABLED", "_TIMEOUT", "_PATH",
                  "PUBLIC_")
        sec = [k for k in never
               if any(s in k for s in security) and not any(b in k for b in benign)]
        if sec:
            add(0, f"{len(sec)} security setting(s) declared in config but never read",
                f"{', '.join(sec)}. The config implies a protection that does not exist "
                "in code.")
        other = [k for k in never if k not in sec]
        if other:
            add(2, f"{len(other)} config key(s) unused in code", ", ".join(other[:12]))

    # Untested critical paths — exported functions whose names touch money/auth.
    test_blob = "".join(t for f, t in corpus.items()
                        if ".test." in f or ".spec." in f or "__tests__" in f)
    if not test_blob:
        add(0, "No test files found",
            f"{len(files)} source files and no .test./.spec. files. Nothing verifies "
            "behavior.")
    else:
        uncovered = []
        for f, t in corpus.items():
            if ".test." in f or ".spec." in f or "__tests__" in f:
                continue
            for m in re.finditer(r"export\s+(?:async\s+)?function\s+(\w+)", t):
                name = m.group(1)
                if is_critical(name, f) and name not in test_blob:
                    uncovered.append(f"{f}::{name}")
        if uncovered:
            add(0, f"{len(uncovered)} critical exported function(s) with no test",
                "; ".join(uncovered[:14]) + ". These touch money, auth, or secrets.")

    # Dangerous patterns that are cheap to detect and expensive to miss.
    risky = {
        r"dangerouslySetInnerHTML": ("XSS risk: raw HTML injection", 1),
        r"eval\s*\(": ("eval() executes arbitrary code", 0),
        r"process\.env\.\w+\s*\|\|\s*[\"'][^\"']{8,}": (
            "Hardcoded fallback for an env var — a secret default that ships", 0),
        r"//\s*@ts-ignore": ("@ts-ignore suppresses a real type error", 2),
        r":\s*any\b": ("`any` disables type checking at that boundary", 2),
    }
    for pat, (desc, sev) in risky.items():
        hits = [f for f, t in corpus.items()
                if re.search(pat, t) and ".test." not in f and ".spec." not in f]
        if hits:
            noun = "occurrence" if len(hits) == 1 else "files"
            add(sev, f"{desc} ({len(hits)} {noun})", ", ".join(sorted(hits)[:8]))


def main() -> int:
    files = py_files()
    tsf = ts_files()

    if not files and not tsf:
        print("No Python or TypeScript/JavaScript files found to audit.")
        return 0

    if files:
        check_reachability(files)
        check_duplicate_concepts(files)
        check_config_vs_code(files)
        check_critical_coverage(files)
        check_tool_debt()
    if tsf:
        check_ts_project(tsf)

    label = {0: "CRITICAL", 1: "HIGH", 2: "MEDIUM"}
    print(f"# Drift audit — {ROOT.name}")
    counts = []
    if files:
        counts.append(f"{len(files)} Python")
    if tsf:
        counts.append(f"{len(tsf)} TS/JS")
    print(f"\nScanned {' + '.join(counts)} files.\n")
    if not findings:
        print("No drift detected: everything is reachable, nothing is duplicated, "
              "config matches code, and critical paths have tests.")
        return 0

    findings.sort(key=lambda f: f[0])
    for sev, title, detail in findings:
        print(f"## [{label.get(sev, 'LOW')}] {title}\n")
        print(f"{detail}\n")
    print(f"---\n{len(findings)} finding(s). "
          "Nothing was modified — these are reports, not fixes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

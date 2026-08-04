#!/usr/bin/env python3
"""SessionStart audit — reports missing engineering safety nets for the current project.

Exists because the user is a self-described vibe coder: the harness should notice
missing discipline (no version control, unprotected secrets, no tests, no CI, no hooks)
and surface it on the FIRST prompt, rather than relying on the user knowing to ask.

READ-ONLY. Never writes, never runs git/package commands that mutate. Silent when a
project is healthy, so a well-set-up repo costs ~0 tokens.

Reads {cwd} JSON from HOOK_INPUT env var. Prints an additionalContext JSON block, or
nothing at all when there is nothing worth saying.

Lint suppressions below are deliberate, not laziness:
  S603 — subprocess args are hardcoded literal lists in this file; no user input
         ever reaches them, and shell=False throughout.
  S110 — bare `except: pass` is the required behavior for a hook: any failure must
         degrade to silence rather than block the user's session.
"""
# ruff: noqa: S603, S110
import json
import os
import subprocess
import sys
from pathlib import Path

# Only ever look at the project we were invoked in.
try:
    payload = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    cwd = Path(payload.get("cwd") or os.getcwd())
except Exception:
    sys.exit(0)

if not cwd.is_dir():
    sys.exit(0)

# Per-project short TTL cache (v1.7.1 perf): git subprocess spawns are the
# whole cost (~700ms cold on Windows). A SessionStart audit seconds after the
# previous one (rapid restart) can reuse the result — repo state doesn't move
# in 10s. ponytail: naive TTL cache; fine until multi-instance racing matters.
import tempfile
import time

CACHE = Path(tempfile.gettempdir()) / "one-man-project-audit.json"
CACHE_TTL = 10  # seconds


def _cached():
    try:
        if CACHE.is_file() and time.time() - CACHE.stat().st_mtime < CACHE_TTL:
            d = json.loads(CACHE.read_text(encoding="utf-8"))
            if d.get("cwd") == str(cwd):
                return d
    except Exception:
        pass
    return None


_GIT_KEY = {"rev-parse": "is-inside-work-tree", "status": "status", "ls-files": "ls-files"}


def run(args):
    """Read-only command; returns stdout or None. Never raises."""
    cached = _cached()
    if cached and args[0] == "git":
        key = _GIT_KEY.get(args[1])
        if key in cached.get("git", {}):
            return cached["git"][key]
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


findings = []       # (severity, message) — severity orders the output
SECRET_NAMES = (".env", ".env.local", ".env.production", "credentials.json", "secrets.json")

# --- Version control: the user's only real undo for AI-made changes ----------------
in_git = run(["git", "rev-parse", "--is-inside-work-tree"])
secrets = [n for n in SECRET_NAMES if (cwd / n).is_file()]

if not in_git:
    msg = ("**No git repository.** There is no way to undo a bad change here. "
           "Raise this with the user and offer to set it up.")
    if secrets:
        msg += (f" IMPORTANT: {', '.join(secrets)} present — write .gitignore FIRST, "
                "then `git init`, or credentials get committed.")
    findings.append((0, msg))
else:
    # Secrets tracked by git is worse than no git at all.
    for name in secrets:
        tracked = run(["git", "ls-files", "--error-unmatch", name])
        if tracked:
            findings.append((0, f"**`{name}` is tracked by git** — secrets are in "
                                "history. Tell the user; it needs removing from the index."))
    dirty = run(["git", "status", "--porcelain"])
    if dirty:
        n = len([ln for ln in dirty.splitlines() if ln.strip()])
        if n >= 10:
            findings.append((2, f"{n} uncommitted files — unprotected work. Suggest a "
                                "commit before starting new changes."))

# --- Tests: the only thing that catches logic slop, which linting cannot -----------
has_py = any(cwd.glob("*.py")) or (cwd / "app").is_dir() or (cwd / "src").is_dir()
pkg = cwd / "package.json"
test_files = []
if pkg.is_file() or has_py:
    # Pruned walk (v1.7.1 perf): rglob over the whole tree walks node_modules
    # and .git — seconds on a real repo. os.walk with skips finds a test file
    # in the first few dirs. Existence check only.
    _PAT = ("test_", "_test.", ".test.", ".spec.")
    for _dirpath, _dirs, _files in os.walk(cwd):
        _dirs[:] = [d for d in _dirs if d not in ("node_modules", ".git", "dist", "build", "venv", ".venv", "__pycache__")]
        if any(any(p.startswith(("test_",)) or "_test" in p or ".test." in p or ".spec." in p for p in _files)
               for _ in (0,)):
            test_files = [True]
            break
        if any(any(pat in f for pat in _PAT) for f in _files):
            test_files = [True]
            break

if not test_files and (has_py or pkg.is_file()):
    findings.append((1, "**No tests found.** Linting catches syntax, not wrong logic. "
                        "For any behavioral change here, write a test with it."))

# --- Mechanical enforcement: the part that survives a weaker model ------------------
pyproject = cwd / "pyproject.toml"
pytext = pyproject.read_text(encoding="utf-8", errors="ignore") if pyproject.is_file() else ""

if has_py:
    has_lint_cfg = "[tool.ruff" in pytext or (cwd / "ruff.toml").is_file() \
                   or (cwd / ".ruff.toml").is_file() or (cwd / ".flake8").is_file()
    has_type_cfg = "[tool.mypy" in pytext or (cwd / "mypy.ini").is_file() \
                   or "[tool.pyright" in pytext
    if not has_lint_cfg:
        findings.append((1, "**No linter config.** Default rulesets are minimal (unused "
                            "imports only) and miss SQL injection, hardcoded secrets, and "
                            "over-complex functions. Propose a tuned config."))
    if not has_type_cfg:
        findings.append((1, "**No type-checker config.** Type checking is the main "
                            "mechanical defense against logic slop — it catches 'this can "
                            "be None here' bugs that linting and green tests both miss."))

alldeps = {}
if pkg.is_file():
    try:
        pj = json.loads(pkg.read_text(encoding="utf-8"))
    except Exception:
        pj = {}
    alldeps = {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}
    has_ts = "typescript" in alldeps or (cwd / "tsconfig.json").is_file()
    has_lint = any(k.startswith(("eslint", "@biomejs", "oxlint")) for k in alldeps)
    if not has_lint:
        findings.append((1, "**No JS/TS linter installed.** Nothing mechanically checks "
                            "this code. Propose eslint or biome."))
    if has_ts:
        ts = cwd / "tsconfig.json"
        try:
            if ts.is_file() and '"strict": true' not in ts.read_text(encoding="utf-8",
                                                                     errors="ignore"):
                findings.append((1, "TypeScript without `strict: true` — most type safety "
                                    "is off, so the compiler catches far less."))
        except Exception:
            pass

# --- Design consistency: the only real defense against generic-looking UI ----------
if pkg.is_file():
    try:
        deps = json.loads(pkg.read_text(encoding="utf-8"))
        allofthem = {**deps.get("dependencies", {}), **deps.get("devDependencies", {})}
    except Exception:
        allofthem = {}
    is_frontend = any(k in allofthem for k in
                      ("react", "vue", "svelte", "next", "@angular/core", "astro"))
    if is_frontend:
        has_tokens = any((cwd / p).exists() for p in
                         ("tailwind.config.js", "tailwind.config.ts", "theme.json",
                          "src/styles/tokens.css", "app/globals.css", "src/index.css"))
        if not has_tokens:
            findings.append((2, "Frontend project with no design-token file. Invoke a "
                                "design skill before building UI, and define tokens "
                                "(color/spacing/type) so styling stays consistent."))

# --- Production discipline: gates a million-dollar team would have ------------------
# Every check here is cheap (filesystem existence only) — no commands run, no network.

# .gitignore — prevents secrets, build artifacts, and node_modules from being committed
if in_git:
    gitignore = cwd / ".gitignore"
    if not gitignore.is_file():
        findings.append((0, "**No `.gitignore`.** Without it, node_modules, .env, and "
                            "build artifacts WILL be committed eventually. Create one now."))
    else:
        try:
            gi_content = gitignore.read_text(encoding="utf-8", errors="ignore")
            for check in (".env", "node_modules", "dist/"):
                if check not in gi_content:
                    findings.append((0, f"`.gitignore` missing `{check}`. Add it."))
                    break
        except Exception:
            pass

# CI — the final gate that catches what local checks miss
ci_paths = [
    ".github/workflows", ".gitlab-ci.yml", "Jenkinsfile",
    ".circleci", ".buildkite",
]
has_ci = any((cwd / p).exists() for p in ci_paths)
if not has_ci and pkg.is_file():
    findings.append((0, "**No CI detected.** Local verification is not a substitute — "
                        "OS and dependency differences can break builds that pass locally. "
                        "Set up GitHub Actions (or equivalent)."))

# Build script — without it, there's no way to know the project compiles
if pkg.is_file():
    try:
        scripts = pj.get("scripts", {})
        has_build = any(k in scripts for k in ("build", "compile", "dist"))
    except Exception:
        has_build = False
    if not has_build and (cwd / "src").is_dir():
        findings.append((1, "**No build script.** A project with source code and no "
                            "`build` script in package.json can't be verified to compile. "
                            "Add one."))

# Git hooks — mechanical enforcement independent of model quality
has_hooks = ((cwd / ".husky").is_dir()
             or (cwd / "lefthook.yml").is_file()
             or (cwd / ".pre-commit-config.yaml").is_file())
if in_git and not has_hooks and pkg.is_file():
    findings.append((0, "**No git hooks.** Pre-commit hooks enforce lint/format gates "
                        "regardless of which model drives. Install husky + lint-staged."))

# Commitlint — enforces conventional commits
has_commitlint = any((cwd / p).is_file() for p in (
    "commitlint.config.mjs", "commitlint.config.js", "commitlint.config.ts",
    ".commitlintrc.json", ".commitlintrc.yaml",
))
if in_git and not has_commitlint and pkg.is_file():
    findings.append((1, "**No commitlint.** Conventional commits (`feat:`, `fix:`) make "
                        "changelogs and semantic versioning automatic. Add it."))

# README — the first thing a new team member sees
readme = any((cwd / p).is_file() for p in ("README.md", "README.txt", "README"))
if not readme:
    findings.append((2, "**No README.** Every project needs one: what it does, how to "
                        "start, how to test, how to deploy. Write one."))

# Secret scanning — catches what .gitignore misses
if in_git:
    all_dep_str = str(alldeps).lower()
    has_secret_scan = ((cwd / ".husky" / "pre-commit-secrets.sh").is_file()
                       or "detect-secrets" in all_dep_str
                       or "talisman" in all_dep_str)
    if not has_secret_scan:
        findings.append((1, "**No secret scanning in pre-commit.** Add a grep-based "
                            "secret scanner (~50 lines of bash) to `.husky/`."))

# CODEOWNERS — ensures every PR has the right reviewer
if in_git and (cwd / ".github").is_dir():
    if not (cwd / ".github" / "CODEOWNERS").is_file():
        findings.append((2, "**No CODEOWNERS.** Create .github/CODEOWNERS so every PR "
                            "gets the right reviewer."))

# persist the git-state snapshot for the TTL cache (never findings — those
# must always be fresh; only the git subprocess results are reused)
try:
    CACHE.write_text(json.dumps({
        "cwd": str(cwd),
        "git": {
            "is-inside-work-tree": in_git,
            "status": locals().get("dirty", ""),
            "ls-files": locals().get("tracked", "") or "",
        },
    }), encoding="utf-8")
except Exception:
    pass

if not findings:
    sys.exit(0)

findings.sort(key=lambda f: f[0])
lines = ["# Project safety audit (automatic)", "",
         "Gaps found in this project. Raise the blocking ones with the user early —"
         " do not silently proceed as if they are fine.", ""]
lines += [f"- {m}" for _, m in findings]

print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "\n".join(lines),
}}))

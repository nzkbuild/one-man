"""Situation recognition (v1.7.0 M1).

Recognizes the engineering SITUATION from the prompt + repo state:
  greenfield | brownfield | resumed | bug-investigation | refactor |
  migration | security-performance | release-preparation

Situation is distinct from task TYPE (bug/feature/...) — it captures the
*context*: is this a new repo? an existing one? resuming abandoned work?
A raw "Build this idea properly" is greenfield; "Continue this unfinished
project" is resumed; "Fix what is wrong here" is bug-investigation.

Repo state (branch/dirty/tests) augments the situation — a greenfield repo
that already has failures is really "brownfield repair".
"""
import re
import subprocess
from pathlib import Path

# Prompt signals per situation — ORDERED BY SPECIFICITY (deliberately
# weak-prompt tolerant). The generic greenfield "make this" must NOT steal
# "make this secure" (security) or "make this faster" (performance), so the
# more specific situations are checked first.
SITUATION_SIGNALS = [
    ("security-performance", [r"\b(secure this|make this secure|security|vulnerab|performance|slow|optimize|speed up|production-ready)\b"]),
    ("refactor", [r"\b(refactor|restructure|clean up|simplify|dedupe|rewrite|rename|without breaking)\b"]),
    ("bug-investigation", [r"\b(bug|broken|crash|error|fails|wrong|not working|regression|500|fix what)\b"]),
    ("migration", [r"\b(migrate|migration|upgrade|port|convert from|move to)\b"]),
    ("release-preparation", [r"\b(release|ship|deploy|prepare for|version|tag)\b"]),
    ("resumed", [r"\b(continue|resume|finish|unfinished|incomplete|pick up|left off)\b"]),
    ("greenfield", [r"\b(build|create|start|from scratch|idea|greenfield)\b",
                    r"\b(build this|create this|implement this)\b"]),
    ("brownfield", [r"\b(existing|current|add to|extend|in the codebase|brownfield)\b"]),
]

# Repo-state signals (verified from the actual repo, not assumed)
DIRTY_SIGNAL = re.compile(r"(?:^|\n)\s*[MADRCU?]")  # git status porcelain


def classify_situation(prompt: str, repo_state: dict = None) -> str:
    """Return the situation from prompt signals + repo state."""
    p = (prompt or "").lower()
    for sit, patterns in SITUATION_SIGNALS:
        for pat in patterns:
            if re.search(pat, p):
                # repo state overrides: "build this" on a DIRTY repo with
                # existing work is brownfield (there's a codebase to respect)
                if sit == "greenfield" and repo_state and repo_state.get("dirty") is True:
                    return "brownfield"
                return sit
    # no strong signal: derive from repo state
    if repo_state:
        if repo_state.get("dirty"):
            return "brownfield"
        if repo_state.get("has_tests"):
            return "resumed"
    return "brownfield"  # safe default for a repo with unknown context


def repo_state(cwd: Path = None) -> dict:
    """Verified repo state: branch, dirty, has_tests, has_build."""
    cwd = cwd or Path.cwd()
    state = {"branch": None, "dirty": False, "has_tests": False, "has_build": False}
    try:
        r = subprocess.run(["git", "-C", str(cwd), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=5,
                           stdin=subprocess.DEVNULL)
        if r.returncode == 0:
            state["dirty"] = bool(r.stdout.strip())
            br = subprocess.run(["git", "-C", str(cwd), "branch", "--show-current"],
                                capture_output=True, text=True, timeout=5,
                                stdin=subprocess.DEVNULL)
            state["branch"] = br.stdout.strip() if br.returncode == 0 else None
    except Exception:
        pass
    state["has_tests"] = (cwd / "test").exists() or (cwd / "tests").exists() or \
        bool(list(cwd.glob("test_*.py"))) or (cwd / "package.json").exists()
    state["has_build"] = (cwd / "package.json").exists() or (cwd / "pyproject.toml").exists() or \
        (cwd / "Cargo.toml").exists()
    return state


if __name__ == "__main__":
    import sys
    prompt = sys.argv[1] if len(sys.argv) > 1 else ""
    rs = repo_state()
    print(f"situation: {classify_situation(prompt, rs)}")
    print(f"repo: branch={rs['branch']} dirty={rs['dirty']} tests={rs['has_tests']} build={rs['has_build']}")

# one-man

The complete Claude Code discipline system — packed into a portable, installable repo. Installs a professional-grade engineering guardrail stack (hooks, skills, templates, memory) onto a fresh Claude Code, so AI consistently delivers pro-level work: no slop, no over-engineering, no skipped steps, no gaps.

One-person engineering discipline, **mechanically enforced** — not prose.

## What it does

| Layer | What you get |
|---|---|
| **14 hooks** | Danger guard (token-aware, blocks real `rm -rf`/force-push/curl-pipe, ignores benign mentions), dep guard, verify-edit lint/type gate, **ship-gate** (blocks "done" over TODO/FIXME/dead code), session context injector (memory digest), hook-lifecycle health checks |
| **8 discipline skills** | pro-workflow, self-evolve, recall, memory-maintain, checkpoint, dep-audit, audit, ctx-agent-history-search |
| **Memory templates** | global PRINCIPLES + PREFERENCES baselines, project-scoped LESSONS + STATE.md convention |
| **Global CLAUDE.md** | protocol (10 principles), triage process, standards, anti-patterns — the discipline teeth |
| **Installers** | `install.sh` (POSIX/Mac/Linux) + `install.ps1` (Windows), idempotent, backup-before-write, deep-merges settings **preserving your env/model/permissions** |

## Install

```bash
git clone https://github.com/nzkbuild/one-man.git
cd one-man
bash scripts/install.sh          # POSIX/Mac/Linux
# or
powershell -ExecutionPolicy Bypass -File scripts/install.ps1   # Windows
```

Dry-run first if you want to preview:
```bash
bash scripts/install.sh --dry-run
powershell -ExecutionPolicy Bypass -File scripts/install.ps1 -DryRun
```

The installer:
1. Checks prereqs (node ≥22, git, python3, claude CLI)
2. **Backs up** your `settings.json` and `CLAUDE.md`
3. Merges hooks + permissions into your settings (**never clobbers** your env/model/baseURL/key)
4. Installs the 8 discipline skills
5. Writes self/ templates (preserves your existing PREFERENCES)
6. Overwrites global CLAUDE.md (backup made)
7. Validates + runs hook self-checks

**Autonomy note:** `skipDangerousModePermissionPrompt` and the deny rules mean Claude works unattended on local projects — it never prompts for routine work, but secrets (`.env`, keys) are hard-denied. The deny rules bind at **session start**; restart `claude` after install.

## Update

```bash
git pull && bash scripts/install.sh     # idempotent; safe to re-run 100×
```

## What never ships

Your personal data stays out of this repo: no API keys, no baseURL, no model aliases, no LESSONS.md, no STATE.md, no session transcripts. See `.gitignore`.

## Test

```bash
pnpm install
pnpm test     # drives hooks/test_*.py self-checks
pnpm check    # lint + typecheck + test
```

CI validates install on `ubuntu-latest` + `windows-latest` (`.github/workflows/validate.yml`).

## Platform notes

- Hooks resolve script paths **self-relatively** (from install location), so they work under any `CLAUDE_CONFIG_DIR`, not just `~/.claude`.
- Windows: wrappers are bash; install.ps1 handles the Windows path/merge flow. The `.env`/`.` glob deny rules use `*` wildcards (glob, not regex).
- Cross-platform side effects: `danger-guard` and `dep-guard` are token-aware to avoid blocking legitimate inspection commands (grep for `rm -rf`, doc mentions of `npm install`).

## Architecture

Policy-driven, evidence-backed, knowledge-adaptive:
`policies/` (versioned behavior) → Policy Runtime (single evaluator) → gates
→ evidence → lessons → promotion. Debt and drift are policy outputs with
lifecycles; release readiness aggregates everything into one verdict.
See `docs/ASSESSMENT-1.6.0-final.md` + `docs/REVIEW-1.6.0-rc.md`.

## Layout

```
one-man/
  hooks/                # .sh wrappers + .py/.mjs brains (self-contained)
  skills/               # 8 discipline skills (real dirs)
  self/                 # PRINCIPLES + PREFERENCES templates (no personal data)
  templates/            # settings.json.template, CLAUDE.md.global
  scripts/              # install.sh, install.ps1, merge_settings.py
  test/                 # assert-based runner over hooks/test_*.py
  .github/workflows/    # CI: validate install on linux + windows
  PLAN-1.0.0.md         # the v1.0.0 consolidated plan
```

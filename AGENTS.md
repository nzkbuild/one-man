# AGENTS.md — working in this repo (for humans and AI agents)

## What this repo is

A portable Claude Code discipline system: hooks, skills, templates, installers.
It is a **modular monorepo** — one product, one repo, one CI, one version line.
Do not split into multiple repos: hooks/skills/templates ship and version together.

## Architecture map

```
hooks/          # .sh wrappers + .py/.mjs brains. Self-relative paths (resolve
                # from the script's own dir — portable under any CLAUDE_CONFIG_DIR).
skills/         # 8 discipline skills (real dirs). Design skills are NOT here —
                # they're symlinked per-machine from ~/.agents/skills via manifest.
self/           # PRINCIPLES + PREFERENCES templates. NEVER personal data.
templates/      # settings.json.template (baseline config), CLAUDE.md.global.
scripts/        # install.sh/.ps1, merge_settings.py, backup.sh/.ps1, plan-check.py.
test/           # node runner driving hooks/test_*.py assert self-checks.
docs/           # plans + versioning discipline.
.github/        # CI: validate on linux + windows.
install.manifest.json  # the 6 plugins + 13 design skills to reproduce per machine.
```

## Conventions

- **Hooks**: wrapper `.sh` captures stdin → `HOOK_INPUT`, calls the `.py` brain.
  Fail-open: any error → exit 0, never block a session. Gate = exit 2 + stderr.
- **Guards are token-aware**: strip quotes/heredocs/comments before matching —
  a benign command mentioning `rm -rf` must NOT block.
- **No personal data in repo**: no keys, no baseURL, no `C:\Users\...`, no memory.
  The pre-commit secret scanner + CI enforce this.
- **Release**: semver (`docs/versioning.md`), CHANGELOG entry, plan-check passes,
  annotated tag on a green commit, rollback drill documented.
- **ADRs**: every architectural decision gets a doc in `docs/architecture/` —
  `ADR-001-<topic>.md` (what chosen, alternatives, why) in the same commit.
  The 5-line lightweight template lives at `templates/ADR-template.md`.
- **Plan discipline**: update plan checkboxes in the SAME commit as the work.
  Never mark a partial item `[x]` — leave `[ ]` with a deferral note.

## Commands

```
pnpm install          # deps (eslint, typescript, husky, commitlint, lint-staged)
pnpm test             # node test/run-tests.js → all hooks/test_*.py self-checks
pnpm run check        # lint + typecheck + test
python3 scripts/plan-check.py            # show open plan items
python3 scripts/plan-check.py --release  # gate: block release over open items
bash scripts/install.sh --dry-run        # preview install
bash scripts/backup.sh                   # back up ~/.claude
```

## Before committing

- `pnpm run check` green
- plan-check (if plan touched)
- pre-commit enforces: lint-staged + secret scan + tests + commitlint
- Conventional commits only (`feat:`, `fix:`, `chore:`, `docs:`...)

# Changelog

All notable changes to one-man. Format: Keep a Changelog
(https://keepachangelog.com/en/1.1.0/). Semver: `vMAJOR.MINOR.PATCH`.

## [Unreleased]

## [1.1.0] - 2026-08-04

### Added
- `scripts/backup.sh` + `backup.ps1`: timestamped backup of `~/.claude` (config +
  memory), one-command `--restore`, `--list`. Tested with round-trip fixture.
- `docs/versioning.md`: semver policy, tag policy, rollback drill (code + data layers).
- `LICENSE` (MIT), `SECURITY.md`, `AGENTS.md`, `CHANGELOG.md` (this file).
- `install.manifest.json`: captures the 6 plugins + 13 design skills this repo was
  built from; installers reproduce them per machine.

### Fixed
- `verify-turn.sh`: removed hard-coded personal path (was leaking `C:\Users\...`);
  ship-gate probe now self-relative.
- `.husky/pre-commit` secret scanner: skip doc files (paths in docs are intentional).
- `dep-guard.py`: `pnpm add -D x` captured the flag as the package; now captures `x`.

## [1.0.0] - 2026-08-03

### Added
- 14 hooks: danger-guard (token-aware), dep-guard, verify-edit, ship-gate (merged
  into verify-turn), session-context, hook-health, settings-validate, project-audit,
  precompact-checkpoint, prompt-guard, phase-gate, subagent-guard, notify-alert,
  context-mode-cache-heal.
- 8 discipline skills: audit, checkpoint, ctx-agent-history-search, dep-audit,
  memory-maintain, pro-workflow, recall, self-evolve.
- `self/` PRINCIPLES + PREFERENCES templates (no personal data).
- `templates/settings.json.template` + `CLAUDE.md.global`.
- `scripts/install.sh` + `install.ps1`: idempotent, deep-merge preserving user config,
  `--dry-run`.
- `test/run-tests.js` + assert-based guard self-checks.
- `claude-health.sh` one-shot diagnostic (20 checks).
- CI: validate on ubuntu-latest + windows-latest (lint, typecheck, tests, install
  dry-run, plan-check).
- `scripts/plan-check.py`: release gate over open plan items.

### Fixed
- danger-guard false-positives on benign commands (token-aware: strings/heredocs/
  comments ignored; command-boundary `rm` match).
- dep-guard false-positives on config text / prose (token-aware + add-only).
- Invalid `Read:*` allow rules (removed; Read is default-enabled for explicit paths).
- `.env*` deny broadened to `Read(**/.env*)`.
- NotebookEdit added to PreToolUse matcher.
- CI `ERR_PNPM_BAD_PM_VERSION` (pnpm/action-setup `version:` conflict).
- install.ps1 dry-run executed python brains (now skipped in dry-run).

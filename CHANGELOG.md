# Changelog

All notable changes to one-man. Format: Keep a Changelog
(https://keepachangelog.com/en/1.1.0/). Semver: `vMAJOR.MINOR.PATCH`.

## [Unreleased]

## [1.4.0] - 2026-08-04

### Added
- `hotspot-report` (SessionStart): behavioral feedback from stats.json — flags
  correction clusters, scope drift, test-discipline slip. Guide only; the human
  tunes, nothing auto-weakens.
- `scripts/release.sh`: automates the release checklist (check, plan-check,
  CHANGELOG gate, tag, push, CI wait) — the repo's own deploy stage.
- `scripts/loop-report.sh`: monthly synthesis (what fired, what to tune) — the
  system's post-mortem.
- CI observe job: claude-health against a fixture HOME after each push.
- docs/PLAN-1.4.0.md: the iterative-leap spec (tracked by plan-check).

### Fixed
- loop-report used python3 (Windows alias); now python.


## [1.3.1] - 2026-08-04

### Fixed
- Hook wrappers merged stderr into stdout, hiding findings from the harness
  ("No stderr output" on every clean run). stderr now passes through.
- design-review TODO pattern self-matched review-gate; removed (real TODOs
  caught by review-gate/ship-gate).


## [1.3.0] - 2026-08-04

### Added
- `review-gate` (Stop): automated code review of changed files — bare except,
  TODO left (blocking); magic numbers, duplicated blocks (guide). The solo
  developer's second pair of eyes.
- `understand-guard` (PreToolUse): read-before-write nudge on stale-target edits.
- `perf-guard` (PostToolUse): N+1, O(n²) nested-same-scan, unbounded fetch-all
  nudges (DB-signal only — no regex-loop false positives).
- `design-review` (Stop): a11y (no-alt, no-label) blocks; placeholder/AI-slop guides.
- `scripts/security-audit.sh`: continuous pnpm/npm audit -> dated report in
  ~/.claude/reports/.
- `scripts/restore-drill.sh`: backup -> restore to scratch -> verify every archive
  entry present. Proves backup works.
- `docs/architecture/ADR-001-one-man-architecture.md` + AGENTS.md ADR rule.
- docs/PLAN-1.3.0.md: the linear-axis completion spec (tracked by plan-check).

### Fixed
- perf-guard/review-gate self-referential false positives (skip test + hook files).
- security-audit false alarm on "No known vulnerabilities found".


## [1.2.0] - 2026-08-04

### Added
- `retrospective` (SessionEnd): session stats recorder -> ~/.claude/self/stats.json
  (bounded at 500). The measurement half of the feedback loop.
- `task-triage` (UserPromptSubmit): prompt classifier (bug/feature/refactor/question/
  chore/design) + skill router via skills.flow.json. Pre-mortem + exit criteria injected.
- `discipline-guard` (PreToolUse): anti-slop nudges — wide-blast-radius-without-design,
  reuse-first on mkdir, tests-missing-after-edits.
- `skills.flow.json`: the systematic-reuse routing table (design -> brandkit/
  design-taste/minimalist-ui chain; bug -> systematic-debugging; etc). Copied by
  installers; consumed by task-triage.
- CLAUDE.md.global: anti-slop principle — idle skills are the gap; mistakes repeated
  are process failures.

### Fixed
- discipline-guard no longer flags git add/commit (VCS bookkeeping is not a design
  decision).


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

# Changelog

All notable changes to one-man. Format: Keep a Changelog
(https://keepachangelog.com/en/1.1.0/). Semver: `vMAJOR.MINOR.PATCH`.

## [Unreleased]

## [1.7.0] - 2026-08-04

### Added — Autonomous Discovery & Sequencing
- **Situation recognition** (situations.py): 8 situations from weak prompts +
  repo state, specificity-ordered, repo-state override.
- **Trustworthy baseline** (baseline.py): verified git state, bounded test
  probe (latency discipline), unfinished work, debt + drift.
- **Engineering assignment synthesis** (assignment.py): situation + verified
  baseline -> structured assignment (sequenced workstreams, risks-from-findings,
  acceptance, DoD, replan triggers).
- **Capability orchestration** (orchestration.py): full contract per capability
  (reason, obligation, executed, output, consumer, satisfied, current); gate
  blocks on unsatisfied obligations; unconsumed (ceremony) detected.
- **Plan validation + auto-repair** (plan-validator.py): missing deps, wrong
  ordering, missing baseline repair, missing rollback, unbounded scope, weak
  acceptance — auto-repaired where deterministic.
- **Controlled re-planning** (replan.py): re-plan only on verified evidence
  change; auditable record (what/why/trigger/affected/stale/new-order).
- **Anti-slop outcome review** (anti-slop.py): stubs, placeholders, generic AI
  doc, meaningless tests, hardcoded secrets, eval, broad swallow — token-aware
  (strings are data; secrets scan raw).
- **Autonomous lifecycle** (test_lifecycle.py): the complete flow proven end to
  end for 6 situations; different situations -> different workflows.
- **Debt revalidation** (debt.py): closes stale debt whose finding no longer
  matches the source (the dogfood class fix).

### Fixed
- Anti-slop + review-gate token-aware class fixes (string literals are data;
  secrets scan raw).
- Debt register revalidates stale false-positive entries.


## [1.6.0] - 2026-08-04

### Added — Policy-Driven Engineering Operating System
- **Policy layer** (M1): policy_version on all policies; validate-policies.py
  (parse + version + strict-schema) enforced in CI — the constitution's
  "no silent undocumented policy".
- **Policy Fitness** (M2): per-policy outcomes (applications/successes/
  regressions/overrides/false-positives/maintenance) + healthy/watch/zombie.
- **Policy Runtime** (M3): the single engineering evaluation path — consumes
  policies + evidence + lessons, produces the deterministic execution plan.
  Parity-tested against v1.5.x hooks.
- **Technical debt governance** (M4): debt as a policy output — auto-created
  from findings, classified, lifecycle (open->acknowledged->fixed->expired),
  blocks release only when acknowledged+unfixed+high-risk.
- **Anti-drift** (M5): drift detection across implementation/docs/plans/
  config/policies — classified, severity, owner, sync action, verified closure.
- **Progressive docs + lightweight ADR** (M6): change->artifact sync decision;
  5-line ADR template. (docs-sync merged into drift-check in review.)
- **Promotion gate** (M7): knowledge->evidence->validation->fitness->approval
  ->versioned policy, traceable; trust hierarchy (policies/trust.json).
- **Release readiness** (M8): aggregates debt + drift + version into
  READY/NOT-READY; wired into pre-push.

### Changed
- Policies now drive behavior from `policies/` (obligations.json, trust.json) —
  not code.
- Task-triage feeds the Policy Runtime (single evaluation path).
- Review-gate magic-number class fix (named constants excluded).


## [1.5.1] - 2026-08-04

### Added
- **Lesson ledger** (hooks/lib/lessons.py): structured record of violations,
  root causes, corrections, layer, recurrence risk — with a full lifecycle
  (observed -> confirmed -> generalized -> enforced/tested -> closed | dismissed).
  A recorded note alone is NOT learned; only enforced/tested/closed count.
- **Stable lesson IDs**: sha1 fingerprint of the normalized violation, not free-text.
- **Recurrence detection** (scripts/check-lessons.py): high-risk lessons not yet
  learned block (exit 2); broken prevention (missing test_ref) detected. Wired
  into CI with a focused fixture (unresolved blocks, learned passes, malformed
  fails safely).
- **Filtered SessionStart digest**: one-line, bounded, repo-signal-relevant lessons.
- **Skill & plugin audit** (docs/SKILL-AUDIT-1.5.1.md): all 27 items classified
  (useful/deferred/obsolete); no ceremonial invocation forced.
- **Privacy-safe seed** (lessons/seed.json): 5 generic lessons; seed test rejects
  all 8 personal-data categories (31 assertions).
- **pre-push hook**: runs check + health + plan-check before ANY push — the
  push-before-locally-catchable-checks regression, closed locally.

### Fixed
- dismissed lessons now pass the recurrence gate (closed-by-decision, not at-risk).
- Assessment doc fully redacted of private-IP patterns.


## [1.5.0] - 2026-08-04

### Added
- **Risk classifier** (task-triage): every prompt gets risk high/medium/low from
  signals (auth, payment, security, migration, concurrency -> high; api/refactor ->
  medium; docs/typo -> low). Drives the gates, advisory by itself.
- **Per-task evidence store** (hooks/lib/evidence.py): `~/.claude/evidence/current.json`
  seeded by task-triage (type/risk/obligations), appended by verify-turn (test
  result, exit code, changed files, state hash). Bounded JSONL, local-only.
- **Evidence-aware completion gate** (hooks/lib/gate.py): medium/high-risk tasks
  block "done" without non-stale evidence backing their obligations. Staleness =
  file changed after verification (state-hash re-check). Auditable override recorded.
- **Context-isolated review** (review-gate): high-risk tasks require isolated_review
  evidence — a fresh-context subagent with only diff+task+conventions. Blocks without it.
- **Control criticality** (one-man.controls.json + hooks/lib/controls.py): safety
  (fail closed under ONE_MAN_FAIL_CLOSED=1) / quality (block done/release) / advisory (warn).
- **CI evidence-gate job**: CI runs the gate against a fixture task — the authority
  beyond local hooks.
- Consolidated duplicated changed-file scanning into hooks/lib/scan.py.

### Changed
- verify-turn now records test evidence before gating.
- Installers copy one-man.controls.json.


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

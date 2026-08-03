# one-man v1.3.0 — Close the Linear Axis

The v1.0→v1.2 delivered the enforcement + feedback-recording layers. This release
closes the remaining **linear** gaps to top-team parity: review, security,
performance, reliability, decision documentation, and design verification.
The **iterative leap** (code-review loop, behavioral feedback, deploy/observe)
is deliberately v1.4.0 — it is architectural and deserves its own design pass.

---

## The linear axis — what this release completes

| Stage | Current | v1.3.0 adds |
|---|---|---|
| INTENT | task-triage exit criteria | (done) |
| UNDERSTAND | protocol principle, no enforcement | **7. understand-floor** (read-before-write nudge) |
| DESIGN | brainstorming/writing-plans routed | **5. ADR pattern** (decisions documented) |
| BUILD | discipline-guard + ship-gate | (done) |
| VERIFY | verify-turn + ship-gate | **1. auto code-review** at Stop |
| REVIEW | nothing (solo gap) | **1. auto code-review** |
| SECURITY | dep-guard on new adds | **2. continuous security audit** |
| PERF | no checks | **3. perf-guard** |
| RELIABILITY | backup.sh exists | **4. restore drill** (tested recovery) |
| DESIGN | design chain routed | **6. design-review** at Stop |

---

## Deliverables

### 1. Auto code-review at Stop (`hooks/review-gate.py` + wrapper)
- Runs on Stop after verify-turn: scans files changed this turn.
- Looks for what lint can't: design debt, hidden coupling, premature abstraction,
  wrong-algorithm-for-data, magic numbers, duplicated logic, missing error handling.
- Outputs findings as stderr feedback (exit 2 blocks "done" over review findings —
  but conservative: only clear defects, not opinions).
- Self-check: fixture code with a real defect → flagged; clean code → silent.

### 2. Continuous security audit (`scripts/security-audit.sh` + .ps1)
- Runs `pnpm audit` (or npm audit) in each project, aggregates known vulns,
  writes a dated report to `~/.claude/reports/security-<date>.md`.
- Scheduled: documented cron/Task-Scheduler line (README).
- Self-check: runs against the repo itself (audit exits non-zero on vulns).

### 3. Perf-guard (`hooks/perf-guard.py` + wrapper)
- PreToolUse/PostToolUse nudge on known anti-patterns in changed code:
  N+1 loop (query inside loop), O(n²) nested scans, unbounded pagination,
  sync I/O in async context, missing index hint.
- Guide (exit 0 + context), never blocks.
- Self-check: fixture with N+1 pattern → flagged; clean → silent.

### 4. Restore drill (`scripts/restore-drill.sh` + .ps1)
- Creates a backup, restores it to a scratch dir, verifies content hash.
- Proves backup actually works (the missing half of backup.sh).
- Self-check: runs the drill against a fixture, asserts restore matches.

### 5. ADR pattern (`docs/architecture/ADR-001-*.md` + AGENTS.md rule)
- Architecture decision records: what chosen, alternatives, why.
- AGENTS.md: every architectural decision gets an ADR in the same commit.
- Seeded with ADR-001 (one-man architecture: modular monorepo).

### 6. Design-review at Stop (`hooks/design-review.py` + wrapper)
- For turns classified "design" by task-triage: scans the diff for the design
  chain's standards — generic AI-looking output, a11y gaps (no alt, low contrast,
  no focus), placeholder content, inconsistent spacing.
- Guide + conservative gate on clear defects.
- Self-check: fixture with a11y gap → flagged; clean → silent.

### 7. Understand-floor (`hooks/understand-guard.py` + wrapper)
- PreToolUse on Edit/Write: if the file being edited was never Read in the last
  10 min AND the prompt shows no prior investigation, nudge "read before you write".
- Guide, never blocks (some edits are legitimately blind — create-new).
- Self-check: edit to unread existing file → nudge; new file → silent.

---

## Definition of done (all self-checked, CI green, plan-check `[x]`)

- [x] review-gate flags a real defect in fixture, silent on clean
- [x] security-audit produces a dated report in a fixture HOME
- [x] perf-guard flags N+1 pattern, silent on clean
- [x] restore-drill round-trips a fixture backup to scratch
- [x] ADR-001 committed; AGENTS.md rule added
- [x] design-review flags an a11y gap in fixture, silent on clean
- [x] understand-guard nudges on unread-file edit, silent on new file
- [x] 7 new self-checks in runner (14 total), CI green both OSes
- [x] v1.3.0 tagged on CI-green commit, CHANGELOG entry

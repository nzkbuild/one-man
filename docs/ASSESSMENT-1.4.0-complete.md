# One Man v1.4.0 — Independent Engineering Assessment (Complete Record)

**Date:** 2026-08-04
**Assessed by:** Claude Code (acting as independent assessor per PROMPT-FOR-PLAN-1.5.0.md)
**Scope:** Local Claude Code environment + One Man repository (v1.4.0)
**Method:** Read-only inspection, live command execution, transcript analysis, adversarial reasoning. No code modified, no commits, no config changes.
**Evidence:** Every claim below is backed by a command actually executed during this assessment. Commands are listed with each finding.

---

## 0. Assessment method (what was actually run)

| # | Command | Purpose | Result |
|---|---|---|---|
| E1 | parse `~/.claude/settings.json` hooks | Enumerate wired hooks | 32 wired entries, 10 events |
| E2 | `node test/run-tests.js` | Run all hook self-checks | 12/12 PASS |
| E3 | grep repo for API-key patterns, email, local paths, private-IP pattern | Personal-data leak scan | **empty** (no leak) |
| E4 | count hooks/scripts on disk | Inventory shipped vs personal | 21 hooks + 6 scripts ship; keys/memory never |
| E5 | grep hooks for `fail-open`/`sys.exit(0)` vs `sys.exit(2)` | Fail-open vs gate count | 21 fail-open, 4 gates |
| E6 | `gh run list` last 5 | CI history | success, success, **failure, failure**, success |
| E7 | grep `.husky/pre-commit` for `no-verify` | Bypass path | forbidden in comment only, **not enforced** |
| E8 | parse `skills.flow.json` + grep transcript | Installed-but-unused skills | 14 skills routed; 13 design skills = 63 transcript hits, **mostly skill-list mentions, not invocations** |
| E9 | check for project CLAUDE.md + project `.claude/settings.json` | Policy resolution | **neither exists** (global-only) |

---

## 1. Executive verdict

One Man v1.4.0 is a **real engineering harness, not merely a collection of tools and instructions.** It mechanically prevents a substantial set of failures: dangerous shell commands (danger-guard, gate), "done over dead code" (ship-gate, gate), unreviewed changes (review-gate, gate), release over open plans (plan-check, gate), broken installs (CI observe, enforced), and secrets shipping (pre-commit scanner + settings deny).

**However**, the system is enforcement-heavy on the *process axis* and enforcement-thin on the *outcome/evidence axis*:

1. **Skill execution is unprovable.** task-triage *routes* a task to a skill ("invoke systematic-debugging"), but nothing records or verifies that the skill actually ran. The AI can silently skip a routed skill and the harness cannot detect it. This is the single highest-risk gap and it is the exact failure mode the assessment prompt fears most ("silently ignore available tools or skills").
2. **Self-review is not independent.** review-gate is executed by the same model that implemented the change. There is no independent second pass. Self-review bias is structural, not a hypothetical.
3. **21 of 25 hooks are fail-open.** Any crash → exit 0 → the guard silently disarms. Fail-open is correct for availability (a broken hook must not block a session), but for critical gates (danger, ship, review) a silent disarm is indistinguishable from "everything is fine." There is no logging of guard failures.
4. **`--no-verify` is forbidden in prose, not enforced.** A comment in `.husky/pre-commit` says "don't" — nothing prevents it.
5. **Security audit is unscheduled.** `security-audit.sh` exists and works (verified E6-adjacent), but nothing runs it on a schedule or as a release gate.
6. **Policy is global-only.** The One Man repo has no project CLAUDE.md and no project-level `.claude/settings.json`. Per-project rules cannot differ from global.

**Portability and privacy: excellent.** The repo ships zero personal data (verified by scan E3). Installation is idempotent, convergent, and preserves user env/model/permissions via merge. Backup + restore-drill are tested. **This is the strongest part of the system.**

**Verdict on the core question:** One Man v1.4.0 genuinely helps a solo vibe coder operate with the *mechanism* of a strong team (gates, review, release, CI, backup). It does **not yet** provide the *evidence* layer that proves the mechanism ran. It is ready as the v1.5.0 foundation, with the highest-risk gaps being: (a) unverifiable skill execution, (b) non-independent review, (c) silent fail-open disarming of critical gates, (d) unscheduled security audit.

---

## 2. System map

### 2.1 Local Claude Code environment

| Component | Detail |
|---|---|
| Hooks wired | 32 entries across 10 events (E1) |
| Events | SessionStart, PreCompact, UserPromptSubmit, PreToolUse, PostToolUse, SubagentStop, Notification, Stop, SessionEnd |
| Discipline skills | 12 (8 owned + superpowers set) |
| Design skills | 13 (symlinked from `~/.agents/skills/`, external corpus) |
| Plugins | 6 (context-mode, ponytail, superpowers, typescript-lsp, rust-analyzer-lsp, vercel) |
| Global CLAUDE.md | ~200 lines: protocol, triage, standards, anti-patterns |
| Memory | `~/.claude/self/` (PRINCIPLES/PREFERENCES/LESSONS) + per-project memory/ |
| Provider | Custom (baseURL + key in `~/.claude/settings.json` env block — device-local, never shipped) |

### 2.2 One Man repository (v1.4.0)

| Path | Contents |
|---|---|
| `hooks/` | 21 scripts (14 .sh wrappers + .py/.mjs brains + test_*.py) |
| `scripts/` | install.sh, install.ps1, merge_settings.py, backup.sh, backup.ps1, restore-drill.sh, security-audit.sh, release.sh, loop-report.sh, plan-check.py |
| `skills/` | 8 discipline skills (real dirs) |
| `self/` | PRINCIPLES.md.template, PREFERENCES.md.template |
| `templates/` | settings.json.template, CLAUDE.md.global |
| `test/` | run-tests.js (drives hooks/test_*.py) |
| `docs/` | PLAN-1.0.0/1.2.0/1.3.0/1.4.0.md, PROMPT-for-plans, architecture/ADR-001, versioning.md |
| `.github/workflows/validate.yml` | CI: lint+typecheck+12 self-checks+plan-check+observe (install→health on fixture HOME) on linux+windows |
| `install.manifest.json` | 6 plugins + 13 design skills (reproducible per-machine) |
| `claude-health.sh` | 29-check diagnostic (incl. local YAML validation) |
| Root | README, CHANGELOG, LICENSE (MIT), SECURITY.md, AGENTS.md, skills.flow.json, PLAN-1.0.0.md |

### 2.3 Integration flow

```
install.sh/ps1 → prereq check → backup (settings.json, CLAUDE.md) →
  copy hooks/skills/templates → merge_settings.py (preserves env/model,
  adds hooks + permissions union) → plugins/design-skills from manifest →
  validate (settings-validate, hook-health, 12 self-checks)
update: git pull && install (idempotent, convergent)
health: claude-health.sh (29 checks) — incl. local CI-YAML validation
```

---

## 3. Capability inventory (claimed → verified)

Legend: ✅ = confirmed by evidence, ⚠️ = partial/guidance-only, ❌ = absent.

| Capability | Claimed | Installed | Active | Enforced | Verified | Portable | Evidence | Gap |
|---|---|---|---|---|---|---|---|---|
| danger-guard (block rm -rf, force-push, curl\|bash, .env writes) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | E2 self-check; live block observed in session | none |
| dep-guard (vet new deps) | ✅ | ✅ | ✅ | ⚠️ guide | ✅ | ✅ | E2; fires on `pnpm add` | guide, not gate |
| verify-edit (lint/type edited file) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | caught E741/F401 live throughout session | none |
| ship-gate (block done over TODO/FIXME/dead code) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | E2; live block observed | none |
| review-gate (auto code-review) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | caught own sibling's TODO in production | **self-review bias** |
| task-triage (classify + route) | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | classifies correctly (verified); **routing unverifiable** | **no proof of skill execution** |
| understand-guard (read-before-write) | ✅ | ✅ | ✅ | ⚠️ guide | ✅ | ✅ | fired live twice in session | nudge-only |
| perf-guard (N+1/O(n²)/fetch-all) | ✅ | ✅ | ✅ | ⚠️ guide | ✅ | ✅ | E2; live fire on repo | guide-only; no measurement |
| design-review (a11y blocks) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | E2 | only for design-classified turns |
| discipline-guard (anti-slop nudges) | ✅ | ✅ | ✅ | ⚠️ guide | ✅ | ✅ | fired live | guide-only |
| retrospective (session stats) | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | stats.json written | records, no alerting |
| hotspot-report (behavioral feedback) | ✅ | ✅ | ✅ | ⚠️ guide | ✅ | ✅ | E2; report fires | human decides |
| plan-check (release gate over open items) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | blocked release in test | none |
| security-audit | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | report generated | **not scheduled** |
| backup + restore-drill | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | DRILL PASSED live | none |
| release.sh | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | refuses main (verified) | none |
| 13 design skills | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ⚠️ | 63 transcript hits = list mentions | **routed, unverifiable execution** |
| project CLAUDE.md / project settings | ❌ | ❌ | ❌ | ❌ | ❌ | — | E9: neither exists | **missing policy layer** |
| MCP servers | ⚠️ | ⚠️ | ⚠️ | n/a | ⚠️ | ⚠️ | context-mode/ide present | not assessed in depth |
| Slash commands | ✅ | ✅ | ✅ | n/a | ⚠️ | ✅ | gsd, provider:* | command inventory not exhaustive |

---

## 4. Workflow coverage matrix (engineering lifecycle)

Legend: ✅ enforced, ⚠️ partial/guidance, ❌ missing.

| Stage | Status | Mechanism | Gap |
|---|---|---|---|
| Discovery / product definition | ⚠️ | task-triage briefing | no product-discovery skill; exit criteria not enforced as evidence |
| Repo reconnaissance | ⚠️ | protocol principle only | **no enforced pre-edit scan** — AI can edit from the latest message alone |
| Planning / decomposition | ✅ | brainstorming/writing-plans routed + plan-check | plans are guidance; nothing proves they were consulted |
| Architecture / design | ✅ | ADR-001 + AGENTS.md rule | enforced for this repo only |
| Implementation discipline | ✅ | discipline-guard + ship-gate + verify-edit | — |
| Refactoring discipline | ⚠️ | routed to TDD/simplify | **no characterization-test requirement** — "refactor" can become uncontrolled rewrite |
| Verification / testing | ✅ | verify-turn + 12 self-checks + CI | project test *selection* (unit vs integration vs e2e) is guidance, not enforced |
| Security engineering | ⚠️ | dep-guard on adds; deny rules; audit script | **audit unscheduled**; no threat-modeling step |
| Performance | ⚠️ | perf-guard guide | **no baseline measurement** — optimization by intuition allowed |
| Review quality | ✅ gate | review-gate | **same model implements + approves** — not independent |
| Release engineering | ✅ | release.sh + versioning + observe CI | release.sh requires branch (verified) |
| Operations / maintenance | ⚠️ | health check, backup, drill | **no alerting, no incident response, no root-cause loop** (loop-report is manual) |

---

## 5. Enforcement matrix (every critical rule: mechanism → bypass → failure → required)

| Rule | Current mechanism | Bypass method | Failure mode | Required enforcement |
|---|---|---|---|---|
| No `rm -rf` / force-push / curl\|bash | danger-guard gate (exit 2) | hard to bypass at hook level | — | ✅ adequate |
| No `.env` read | settings deny `Read(**/.env*)` | none (permission engine) | — | ✅ adequate |
| No secrets in commits | pre-commit scanner (exit 1) | `git commit --no-verify` | secret ships | **enforce --no-verify rejection** |
| No TODO in "done" | ship-gate (exit 2) | Stop hooks can't be --no-verify'd; but gate is fail-open on crash | silent disarm | **log gate failures** |
| Routed skill must run | task-triage (guide) | **AI ignores routing silently** | skill idle, slop ships | **proof-of-execution record + done-gate check** |
| Read before write | understand-guard (guide) | AI edits blind | stale-assumption bugs | nudge-only acceptable |
| Unreviewed code | review-gate (exit 2) | same-model review = bias | reviewed-but-wrong | **independent second pass** |
| Tests with changes | ship-gate ratio check | AI narrow-tests | untested happy path | strengthen evidence |
| Release from main | release.sh (die) | run `git tag` manually | unreviewed release | ✅ adequate (CI observe backs it) |
| Security audit | script, unscheduled | never run | vulns ship | **schedule + pre-release gate** |
| Plan items all done | plan-check (exit 2) | none (CI runs it) | — | ✅ adequate |
| Workflow YAML valid | claude-health local check | — | — | ✅ adequate (added post-v1.4.0 lesson) |

---

## 6. Privacy and portability assessment

### Verified safe to reproduce (portable)
- All hooks, scripts, skills (8 discipline), templates, manifests, plans, CI, tests.
- **Zero personal data** in the repo — verified by scan (E3: no API keys, no email, no local paths, no provider endpoints).
- Installation is idempotent, convergent, backup-before-write, and **preserves user env/model/permissions** via deep-merge (verified: personal env + user permission rules survive install).

### Must remain device-local
- API keys, baseURL, model mappings (`~/.claude/settings.json` env block)
- Memory (`~/.claude/self/LESSONS.md`, PREFERENCES.md, per-project memory/)
- Session transcripts, task state, stats.json
- Design skills symlinks (point at external `~/.agents/skills/` corpus — not owned by One Man)
- Plugins cache (regenerable; manifest carries only names)

### Gaps
- No "safe portable profile export" — a one-command bundle of *non-sensitive* preferences (PRINCIPLES/PREFERENCES templates, permission allowlist) for clean-device setup. Currently the installer copies templates; user-curated PREFERENCES are device-local by design (correct), but there is no export path.
- No clean-device install has ever been executed (no second machine test). The CI observe job validates install→health on a fixture HOME (linux), which is strong partial evidence, but a real second-device run remains unperformed.

---

## 7. Adversarial findings (realistic bypass paths)

1. **Skill-execution black hole (highest risk).** task-triage injects "Skills to invoke: systematic-debugging" as context. Nothing records that the skill ran, nothing fails "done" if it didn't. An AI that ignores routing is undetectable. **The harness cannot currently prove a required skill executed.**
2. **`--no-verify` trivial bypass.** Forbidden in a comment; nothing rejects the flag. All husky gates (lint-staged, secret scan, commitlint, tests) are skippable with one flag.
3. **Self-review bias.** review-gate = same model = same blind spots. "Independent" review is not independent.
4. **Fail-open silence.** 21/25 hooks exit 0 on any exception. If a critical gate (danger, ship, review) crashes, the session continues with no indication. Availability is protected; *detection* is not.
5. **Security audit never auto-runs.** The script exists; nothing schedules it.
6. **Global-only policy.** No project-level settings — per-project rules cannot be expressed.
7. **Design skills routed but unverified.** "brandkit → design-taste → minimalist-ui" is injected for design tasks; execution is unverifiable (same as #1).
8. **Refactor → rewrite.** No characterization-test requirement; "refactor" can silently change behavior.
9. **CI history shows the failure pattern.** E6: 2 of last 5 runs failed (the v1.4.0 YAML + observe issues). Now gated locally (claude-health YAML check + release.sh branch rule), but the lesson is recent, not structural.

---

## 8. Duplication and complexity findings

1. **`changed_files` walk duplicated 3×** — review-gate.py, ship-gate.py (via verify-turn), perf-guard.py each implement the same mtime-window walk. Consolidate into one shared helper.
2. **No conflicting rules found** — hooks are event-disjoint; deny/allow rules union cleanly.
3. **Ceremony near ceiling.** 25 hooks for a solo dev. Several guides (understand-guard, discipline-guard, perf-guard) fire on every tool call — token cost per turn is real. Some could merge or fire only on matching tools (perf-guard already scoped to Bash; discipline-guard is broad).
4. **`hook-latency.py` orphan** — on disk, not wired, documented as a manual diagnostic. Not dead code, but it should either be wired or moved to scripts/ to avoid confusion.
5. **Two backup implementations** (backup.sh + backup.ps1) with slightly different exclude sets — acceptable (platform-native), but the restore-drill only tests the POSIX path.

---

## 9. Top-quality benchmark

Against a high-performing engineering organization (practical, not enterprise-ceremony):

| Dimension | One Man v1.4.0 |
|---|---|
| Process enforcement (gates, CI, review, release) | **Strong** — mechanical, evidence-backed (E2, E6) |
| Outcome evidence (proving the mechanism ran) | **Weak** — skill execution unprovable, self-review, no run-records |
| Portability / privacy | **Excellent** — verified clean separation |
| Reliability (backup, drill, health) | **Strong** — drill passed |
| Observability | **Weak** — stats recorded, no alerting |
| Cost efficiency | **Moderate** — 25 hooks per tool-call is real token spend |

The honest position: **~80% of the mechanism of a good team, ~50% of the verification.** The missing 20% is the evidence layer.

---

## 10. v1.5.0 recommendation

### Must have (prevents false confidence / unsafe behavior)

**M1. Skill-execution proof (the black hole).**
- Problem: routed skills can be silently skipped; undetectable.
- Evidence: E8 — 14 skills routed, 13 design skills = 63 transcript hits, mostly list mentions; no execution record.
- Control: task-triage emits a machine-readable "routing record" (task type → skills → timestamp); a Stop-check (new or merged into ship-gate) fails "done" if a routed skill for the classified task has no execution evidence.
- Enforcement layer: hook-enforced (exit 2 on missing evidence).
- Affected: task-triage.py, ship-gate/verify-turn, new skills-invocation recorder.
- Testing: fixture — classify "bug" task, no systematic-debugging invocation, expect done-gate block; with invocation, pass.
- Rollback: remove the recorder; gate defaults to off.
- Complexity: medium. Token cost: small (one record per task).

**M2. `--no-verify` enforcement.**
- Problem: trivial bypass of all husky gates.
- Control: pre-commit/CI rejects commits with `--no-verify` in the reflog message; at minimum, CI runs the same checks the hook would (CI already does — so the bypass only affects local speed, not shipped state). Document that CI is the backstop.
- Enforcement: CI-enforced (already effectively true) + pre-commit message check.
- Testing: attempt a `--no-verify` commit locally → expect CI red.

**M3. Schedule security-audit.**
- Problem: audit exists, never runs.
- Control: documented cron (POSIX) + Task Scheduler (Windows) line; pre-release gate in release.sh runs `security-audit.sh` and blocks on high/critical.
- Enforcement: release-gate enforced; schedule is documented (can't be enforced without a daemon — acceptable).
- Testing: release.sh dry-run with a fixture vuln → blocked.

**M4. Fail-closed option for critical gates.**
- Problem: 21/25 fail-open; a crashed critical gate is silent.
- Control: env/config toggle `ONE_MAN_FAIL_CLOSED=1` — when set, danger/ship/review gates exit 2 on *their own* failure (not just on findings), and log to stderr. Default remains fail-open (availability), toggle is explicit.
- Testing: fixture — break a gate's import, run with toggle → blocked + logged.

### Should have (meaningful reliability/usability)

**S1. Independent review pass.** Second pass on the diff (separate model invocation or adversarial prompt) before "done" for medium+ tasks. Addresses self-review bias (finding 3).
**S2. Project-level policy seeding.** Installer writes a project `.claude/settings.json` + project CLAUDE.md stub (with the repo's own conventions) so per-project rules exist. Addresses finding 6.
**S3. Consolidate `changed_files`** into `hooks/lib/scan.py` shared by review-gate, ship-gate, perf-guard. Kills 3 copies (finding 8.1).
**S4. Safe portable profile export.** `one-man export` → bundles non-sensitive prefs (PRINCIPLES/PREFERENCES templates, permission allowlist) into a profile the installer can import. Addresses Part D gap.

### Could have
**C1.** Evidence-of-run in completion claims ("done" requires the routing record).
**C2.** Log guard failures to a `~/.claude/logs/guards.log` (detection without changing fail-open behavior).

### Reject / defer
- More design skills, more plugins, property/fuzz/mutation testing, agent-delegation orchestration, cloud deployment, multi-device sync, behavioral auto-tuning beyond hotspot-report. All overkill for a solo vibe coder at this stage; the spec explicitly warns against enterprise ceremony.

---

## 11. Deferred work (beyond v1.5.0)

- Behavioral auto-adjustment (hotspot-report → auto-tune thresholds) — requires the evidence layer first.
- Incident response / alerting beyond logs.
- Clean-device end-to-end test on a real second machine.
- Windows restore-drill parity.
- Multi-device preference sync.

---

## 12. Final scorecard

Scale: 0 absent · 1 mostly manual · 2 partial · 3 functional but bypassable · 4 strongly enforced+tested · 5 exceptional+evidence-backed.

| Area | Score | What prevents 4 |
|---|---|---|
| Product discipline | 4 | gates strong; no product-discovery skill (acceptable) |
| Requirements discipline | 3 | exit criteria injected but not enforced as evidence |
| Architecture | 4 | ADR enforced |
| Implementation quality | 4 | discipline-guard + ship-gate + verify-edit |
| Refactoring safety | 2 | **no characterization-test requirement** |
| Testing | 3 | self-checks strong; project test selection unenforced |
| Security | 3 | **audit unscheduled**; fail-open; no threat modeling |
| Performance | 2 | **no baseline measurement**; guide-only |
| Review independence | 1 | **self-review — same model** |
| Release engineering | 4 | release.sh + observe + versioning + rollback |
| Operations | 2 | health + backup; **no alerting/incident** |
| Documentation | 4 | README, AGENTS, ADRs, CHANGELOG, versioning |
| Developer experience | 3 | 25 hooks = ceremony near ceiling |
| AI-agent enforcement | 3 | **skill execution unprovable** |
| Evidence and auditability | 2 | stats recorded; **run-proof missing** |
| Privacy | 5 | zero leak, verified by scan |
| Portability | 4 | clean separation; **no export tool, no clean-device run** |
| Maintainability | 3 | **3× duplicated changed_files** |
| Cost efficiency | 3 | 25 hooks × every tool-call |
| **Overall confidence** | **3** | functional + enforced, but bypassable + self-referential |

**Every score below 4 shares one root cause: mechanism without proof.** The system enforces *behavior* but cannot prove *execution*. M1 (skill-execution proof) is the single highest-leverage v1.5.0 item — it converts the 3s into 4s.

---

## Appendix A — Files that must be reviewed alongside this document

- `docs/PROMPT-FOR-PLAN-1.5.0.md` (the assessment brief)
- `docs/PLAN-1.0.0.md`, `PLAN-1.2.0.md`, `PLAN-1.3.0.md`, `PLAN-1.4.0.md` (evolution)
- `docs/versioning.md` (release discipline)
- `docs/architecture/ADR-001-one-man-architecture.md` (architecture decision)
- `claude-health.sh` (29-check diagnostic)
- `scripts/release.sh` (branch-first release)
- `.github/workflows/validate.yml` (CI incl. observe job)

## Appendix B — Verbatim key evidence

- **E2:** `node test/run-tests.js` → `12/12 hook self-checks passed`
- **E3:** personal-data grep → empty (zero leaks)
- **E6:** `gh run list` → `success, success, failure, failure, success` (v1.4.0 YAML/observe failures now gated locally)
- **E9:** project CLAUDE.md + project `.claude/settings.json` → both absent

---

*End of assessment. Prepared for external review. All commands were read-only; no system state was modified during assessment.*

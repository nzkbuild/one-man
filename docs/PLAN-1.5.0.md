# One Man v1.5.0 — Risk-Based, Evidence-Backed Engineering Harness

**Status:** Proposed (implementation not started)
**Date:** 2026-08-04
**Based on:** ASSESSMENT-1.4.0-complete.md, verified against real code (this document records both).
**Goal:** Turn One Man from tools/hooks/rules/recommendations into a risk-based, evidence-backed harness that prevents Claude from skipping required work or claiming completion without proof.

---

## 0. Verification of the assessment (what the plan is built on)

The assessment's claims were re-checked against the actual repo. **Two claims were wrong and are corrected here** — the plan does not build on them.

| Assessment claim | Verified? | Correction |
|---|---|---|
| `changed_files` duplicated 3× | ✅ CONFIRMED | design-review.py, perf-guard.py, review-gate.py each implement it |
| Fail-open hooks 21 vs gates 4 | ❌ **WRONG** | Actual: **5 fail-open** (my grep matched "fail-open" in comments). Overstated ~4×. |
| skill-execution gap | ✅ CONFIRMED | task-triage routes; **nothing verifies routed skill ran** — but the brief's reframe stands: prove the *obligation*, not the skill |
| ship-gate ratio check | ✅ CONFIRMED | 5+ src files / 0 test files → block |
| No project-level policy | ✅ CONFIRMED | neither exists |
| "Nothing captures evidence" | ⚠️ PARTIAL | verify-turn captures test FAILED (exit 2 on red); retrospective records commits/tests/skills_invoked; **no structured evidence store, no per-task evidence** |
| release.sh refuses main | ✅ CONFIRMED (verified in session) | — |

**Implication:** v1.5.0 must NOT add a "skill-invocation prover" (the assessment's M1 was overengineered toward the wrong target). The correct target per the brief: **prove the engineering obligation was satisfied with tool-derived evidence.**

---

## 1. Verified findings (driving the plan)

### F1 — No risk classification (highest-impact gap)
task-triage classifies **type** (bug/feature/refactor/question/chore/design) but **no risk** (low/medium/high). A one-line typo fix and a payment-refactor get identical treatment. There is no mechanism that escalates scrutiny for high-risk changes (security, money, auth, concurrency, data migration).

### F2 — No per-task evidence store
verify-turn checks "did the suite pass" (exit 2 on red) but there is no record of *what* evidence was gathered for *which* task, *against which code state*. "Done" cannot be proven — only "suite happened to be green at Stop."

### F3 — Completion gate is state-blind
ship-gate scans files changed in the last 10 min — but if the model edits a file, runs tests, then edits again, the gate cannot tell "tested final state" from "tested earlier state, changed since." **Evidence staleness is undetected.**

### F4 — Review is not context-isolated
review-gate runs on the same model+context as the implementation. No independent-context review for medium/high-risk changes (the brief's item 5).

### F5 — Local hooks bypassable; CI is the real authority
`--no-verify` skips all husky gates locally. CI is the actual enforcement point — **the plan must treat CI as authority**, not add more local ceremony.

### F6 — Control criticality is implicit, not declared
Some controls gate (exit 2), some guide (exit 0), but nothing *declares* safety-critical vs quality-critical vs advisory. A safety-critical control that fails open silently is indistinguishable from "all good."

### F7 — Privacy/portability strengths (must preserve)
Zero personal data in repo (verified scan); idempotent convergent install; backup + restore-drill tested; CI observe job validates install→health.

### F8 — Duplication (real, small)
`changed_files` 3× (design-review, perf-guard, review-gate) — consolidate.

---

## 2. Proposed v1.5.0 scope — the smallest practical change

**Core idea: a per-task evidence record + risk-scaled gates + CI as authority.**

One new artifact, three changes, zero new plugins/hooks-of-new-kind:

### A. Risk classifier (extends task-triage)
- task-triage additionally assigns `risk: low | medium | high` from signals:
  - high: auth, payment, security, concurrency, data migration, crypto, `danger-guard`-adjacent surfaces, files named `*auth*`, `*pay*`, `*sec*`, `*crypto*`, `*migration*`
  - medium: multi-file refactor, API change, DB schema, public-facing behavior change
  - low: typo, docs, one-file internal, no behavior change
- Injected with the existing briefing (no new hook).

### B. Evidence store (`~/.claude/evidence/<task-id>.json`)
- Written by the hooks that already run: verify-turn records test results + exit codes + changed-file snapshot; review-gate records findings + the code state reviewed; task-triage records type/risk/obligations.
- Each record: `{task_id, type, risk, obligations, evidence: [{kind, result, exit_code, files, state_hash}], completed: false}`.
- Small, JSONL, bounded (prune old). **No new hook** — existing hooks append.

### C. Completion gate — evidence-aware (extend ship-gate)
- At Stop: if a task's risk is medium/high AND required evidence is missing/failed/stale → block "done" (exit 2).
- **Staleness:** re-hash changed files at Stop; if any file changed since evidence was recorded → evidence stale → block.
- Required evidence by obligation (the brief's item 2):
  - bug fix → a test that failed before and passes now (or a captured failing output + fix)
  - refactor → baseline tests green before + after, behavior unchanged
  - feature → tests for the new path + build green
  - dependency update → audit/CI green
  - security change → threat-model note + tests + secret scan clean
  - release → release.sh gate (already exists)

### D. Context-isolated review (extend review-gate)
- For risk=high (and medium with `--review`): review-gate emits a **separate-context review request** — the review runs in a fresh subagent context with only: the diff, the task record, the repo conventions (no implementation context). Findings recorded in the evidence store.
- This is the "independent review" without adding a plugin: a bounded subagent call, context-isolated by construction.

### E. Control criticality declaration (config)
- `one-man.controls.json` (or env): each control declares `criticality: safety | quality | advisory`.
  - safety → fail closed (on its own failure, block)
  - quality → block completion/release
  - advisory → warn only
- Default: existing behavior (fail-open for availability) preserved; the declaration makes criticality explicit + auditable (F6).

### F. CI as authority (no local-ceremony increase)
- No new local hooks. The v1.5.0 CI job: runs the evidence gate against a **fixture task** (proves the gate logic in CI, not just locally). Local `--no-verify` stays bypassable locally — CI remains the backstop (already true).

### G. Consolidate `changed_files`
- One shared helper `hooks/lib/scan.py`; review-gate, perf-guard, design-review import it.

---

## 3. Ordered milestones

| # | Milestone | Depends on |
|---|---|---|
| M1 | Consolidate `changed_files` → `hooks/lib/scan.py` (F8, cleanup) | — |
| M2 | Risk classifier in task-triage (A) | M1 |
| M3 | Evidence store + writers (B) | M2 |
| M4 | Evidence-aware completion gate (C) | M3 |
| M5 | Context-isolated review for high-risk (D) | M4 |
| M6 | Control criticality declaration (E) + CI evidence-gate job (F) | M5 |
| M7 | Release v1.5.0 (CHANGELOG, plan-check, tag, CI) | M6 |

## 4. Acceptance criteria + tests per milestone

### M1 — scan consolidation ✅ DONE
- **AC:** review-gate, perf-guard, design-review delegate to `hooks/lib/scan.py`; single implementation.
- **Result (verified):** 0 `os.walk` in the 3 hooks, all delegate to `_scan.changed_files`; 13/13 self-checks (runner extended to include `hooks/lib/test_*.py`); 6-assertion scan self-check.

### M2 — risk classifier
- **AC:** task-triage output includes `risk: high|medium|low` with the briefing.
- **Test:** fixture prompts — "fix the payment bug" → high; "update README" → low; "refactor the API module" → medium. 5-6 assertions.

### M3 — evidence store
- **AC:** verify-turn/review-gate/task-triage append to `~/.claude/evidence/<task>.json`; fields per spec; bounded (prune > 200).
- **Test:** fixture — run the hooks against a temp HOME, assert the record shape + content + pruning.

### M4 — evidence-aware gate
- **AC:** medium/high task with missing/failed/stale evidence → exit 2 blocks done; low task with no evidence → passes; re-edit after evidence → stale → blocks.
- **Test:** 6-8 assertions (missing, failed, stale-after-edit, low-risk-passes, evidence-present-passes).

### M5 — context-isolated review
- **AC:** high-risk task triggers a fresh-context review; findings land in the evidence store; review context excludes implementation history.
- **Test:** fixture — high-risk task → review record present; assert the review prompt contains only diff+task+conventions (no prior turns).

### M6 — criticality + CI
- **AC:** `one-man.controls.json` declares criticality; safety control fails closed when its own code breaks (fixture); CI job runs the evidence gate on a fixture task and passes.
- **Test:** fixture — break a safety control's import → with declaration, blocks + logs; without, fails open (preserved default).

### M7 — release
- **AC:** 12+ self-checks green (now 12 + new), plan-check `[x]`, CI green both OSes, CHANGELOG, tag v1.5.0.

## 5. Deferred / rejected

- **Rejected: skill-invocation prover (assessment M1).** The brief is right: proving "skill invoked" is ceremony; proving "obligation satisfied" is value. The evidence store covers obligations.
- **Deferred:** fail-closed for ALL gates (only safety-critical per M6); behavioral auto-tuning; alerting; multi-device sync; more plugins/skills.
- **Rejected: `--no-verify` local enforcement.** Useless locally (trivially bypassed); CI is the real authority (already enforced).

## 6. Files likely to change

- `hooks/task-triage.py` (risk classifier)
- `hooks/verify-turn.sh` + `hooks/ship-gate.py` (evidence write + gate)
- `hooks/review-gate.py` (context-isolated review + evidence)
- `hooks/lib/scan.py` (NEW, shared)
- `hooks/perf-guard.py`, `hooks/design-review.py` (import scan.py)
- `scripts/merge_settings.py` (control declaration path if config-based)
- `templates/settings.json.template` (criticality config)
- `test/` (new self-checks: risk, evidence, gate, isolated-review)
- `.github/workflows/validate.yml` (evidence-gate CI job)
- `docs/PLAN-1.5.0.md` (this file), CHANGELOG.md

## 7. Risks, compatibility, rollback

- **Risk:** evidence gate too strict → blocks legitimate low-risk work. Mitigation: risk-scaled (low risk never blocked); explicit override path (user confirms) recorded as justification in the evidence store (auditable, not silent).
- **Risk:** context-isolated review costs tokens. Mitigation: high-risk only; bounded subagent; review output capped.
- **Risk:** evidence store grows. Mitigation: JSONL + prune >200; it's local, never ships.
- **Compatibility:** all new behavior is additive — existing hooks unchanged in contract; the gate only *adds* blocks for medium/high risk with missing evidence. Existing workflows unaffected. Installer merge preserves user config (unchanged).
- **Rollback:** each milestone is independently revertible (scan.py import swap, risk field, evidence append, gate condition). The gate defaults to permissive (low-risk passes) so disabling = remove the medium/high condition. Evidence store deletion is safe (regenerates). Backup + restore-drill protect the whole system (existing).

---

## Appendix — Control criticality map (proposed)

| Control | Current | Proposed criticality |
|---|---|---|
| danger-guard | gate (exit 2) | **safety** (fail closed on own failure) |
| settings deny (.env/curl) | permission | safety (platform-enforced) |
| ship-gate | gate | **quality** (block done) |
| review-gate | gate | quality (block done; isolated for high) |
| verify-turn (tests) | gate | quality |
| plan-check | gate (CI) | quality |
| task-triage/understand/discipline/perf | guide | advisory |
| CI observe | CI | safety (release authority) |

*End of plan. No code modified. All findings verified against the actual repository (commands in §0).*

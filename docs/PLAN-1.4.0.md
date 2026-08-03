# one-man v1.4.0 — The Iterative Leap

v1.0→v1.3 closed the **linear axis**: every stage of a task is now enforced,
routed, reviewed, and measured. This release closes the **iterative axis** —
the loop that makes the system *learn from its own operation* and *deploy like
a team*. The three pillars:

1. **Behavioral feedback** — stats.json stops being a log and starts reshaping
   the system (auto-adjust thresholds, surface hotspots).
2. **Deploy/observe** — CI stops at "build passes" and gains deploy + health
   awareness for the *repo itself*.
3. **Loop-closed end-to-end** — review → learn → reshape, continuously.

---

## 1.4.1 Behavioral feedback (`hooks/hotspot-report.py` + wrapper)

**The measurement layer becomes behavioral.** Reads `~/.claude/self/stats.json`
(recorded by retrospective) and produces a SessionStart report of the last N
sessions:

| Signal | What it means | System action |
|---|---|---|
| Corrections cluster on one skill | That skill misleads | Nudge: "this skill's guidance conflicts with X corrections — review it" |
| High duration, low output | Sessions drifting | Nudge: "long sessions with few commits — scope tighter" |
| Zero test files across sessions | Test discipline slipping | Nudge: "N sessions with no test files — ship-gate will block 'done'" |
| Perf-guard hits repeat on same file | Hotspot | Nudge: "perf-guard flagged X 3× — refactor, don't patch" |

Guide (exit 0 + context at SessionStart). The **auto-adjust** half: if a guard
fired N+ times in a window with no correction, the report flags "guard may be
noisy — consider tuning" (human decides; no autonomous weakening).

Self-check: fixture stats.json with a correction cluster → report mentions it;
clean stats → silent.

## 1.4.2 Deploy/observe for the repo (`scripts/release.sh` + CI deploy job)

**The repo itself gets a deploy stage.** `release.sh` automates the release
checklist (versioning.md):

```
scripts/release.sh <vX.Y.Z>   # runs check + plan-check + CHANGELOG bump +
                              # tag + push + CI wait + rollback-drill
```

And a CI job observes the *health* of the released state: after tag, CI runs
`claude-health.sh` against a fixture HOME + the full self-check suite. If a
release ships a broken hook, the observe job fails it — not the next user.

## 1.4.3 Loop-closed (`scripts/loop-report.sh`)

Monthly/quarterly synthesis: reads stats.json + corrections + hotspots, writes
`~/.claude/reports/loop-<month>.md` — what fired, what was corrected, what to
tune. The "post-mortem" of the system itself. Scheduled via cron/Task Scheduler
(document in README).

---

## Definition of done (self-checked, CI green, plan-check `[x]`)

- [x] hotspot-report flags a correction cluster in fixture stats; silent on clean
- [x] release.sh runs the checklist on a fixture repo (dry-run mode)
- [x] CI observe job runs claude-health against fixture HOME
- [x] loop-report.sh writes a dated synthesis from fixture stats
- [x] 3 new self-checks in runner (14 total), CI green both OSes
- [x] v1.4.0 tagged on CI-green commit, CHANGELOG entry

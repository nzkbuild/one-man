# one-man — v1.0.0 Consolidated Plan

One source of truth for packing the complete Claude Code discipline system into a
portable, installable repo. The goal: **AI consistently delivers pro-level work —
no slop, no over-engineering, no skipped steps, no gaps, no loopholes — without
the user reprompting or invoking anything manually.**

The system enforces the right step at the start (triage → plan), in the middle
(guardrails on every mutation), at the end (a hard "done" gate), and continuously
(self-evolving memory + drift audit). The AI does not choose its process — the
harness imposes it.

---

## 1. Principles

1. **Mechanical over prose.** Discipline enforced by hooks/linters/validators
   survives any model. Prose in CLAUDE.md degrades with model strength.
2. **Guided, not just guarded.** Most hooks steer via `additionalContext` (Claude
   sees it, acts). A few gate via `exit 2` (blocks the action). Split is
   deliberate: silently-blocking everything = friction; silently-allowing
   everything = slop.
3. **Guidance at the moment of need.** Briefing is injected when the prompt
   arrives, not as a preamble. Feedback arrives when the tool runs, not as a
   post-hoc report.
4. **"Done" has teeth.** A hard ship-gate blocks declaring completion over a red
   suite, dead code, missing tests, or uncommitted work.
5. **One source, convergent install.** `git pull && install` is idempotent and
   merges cleanly with the user's personal config. Never overwrites personal
   data without backup and disclaimer.
6. **No personal data.** Repo ships tools, templates, and manifests — never
   secrets, keys, paths, session state, or captured lessons.

---

## 2. Hosting & layout

- Host: **`github.com/nzkbuild/one-man`** (public)
- Local: **`C:\Users\nbzkr\Coding\one-man`**
- Package manager: pnpm (matches ecosystem), Node >=22

```
one-man/
  hooks/                # .sh wrappers + .py/.mjs brains (compiled from dev/)
  skills/               # our 8 discipline skills (as real dirs)
  plugins/              # manifests: ponytail, context-mode, superpowers
  self/                 # PRINCIPLES.md + PREFERENCES.md TEMPLATES
  templates/            # CLAUDE.md.global, settings.json.template
  dev/                  # source scripts; build/ copies to hooks/
  scripts/install.sh    # POSIX/Mac/Linux bootstrap
  scripts/install.ps1   # Windows bootstrap
  test/                 # assert-based self-checks for guards/validators
  .github/workflows/    # CI: validate install on linux + windows
  README.md
  PLAN-1.0.0.md         # this file
  .gitignore
```

**Never ships** (`.gitignore`): `env` block (API keys, base URL), personal
`LESSONS.md`, project `STATE.md` + memory, transcripts, credentials, personal
skill symlinks, `plugins/cache/` binaries.

---

## 3. Skills inventory (ships in repo)

**Our 8 discipline skills** (already local, packaged as real dirs):

| Skill | Purpose |
|---|---|
| pro-workflow | Professional workflow protocol: investigate → plan → verify → report |
| self-evolve | Capture corrections into memory, scoped & prioritized |
| recall | Load full memory files on demand |
| memory-maintain | Dedup/prune lessons so memory stays in budget |
| checkpoint | Save goal/done/next to project STATE.md |
| dep-audit | Vet existing dependencies |
| audit | Drift audit before shipping: unreachable code, unwired infra, untested money/auth paths |
| ctx-agent-history-search | Search agent history for patterns |

**Recommended installs (selector):**

| Plugin | Source | Why |
|---|---|---|
| ponytail | `DietrichGebert/ponytail` | Minimalism ladder, anti-over-engineering |
| context-mode | `mksglu/context-mode` | Context efficiency, indexed knowledge base |
| superpowers | `claude-plugins-official/superpowers` | Process skills: brainstorming, plans, systematic-debugging |

**Optional community skills** (selector-gated, not bundled, fetched separately):
the 13 symlinked design/image-gen skills (`brandkit`, `design-taste-frontend`,
`gpt-taste`, `high-end-visual-design`, `imagegen-frontend-*`, `image-to-code`,
`industrial-brutalist-ui`, `minimalist-ui`, `redesign-existing-projects`,
`stitch-design-taste`, `find-skills`, `full-output-enforcement`). Install is
offered per item with a recommended default; the design set can come from the
plugin marketplaces via `claude plugins install` rather than bundling.

---

## 4. Hook map — the 4 stages

Reference: Claude Code v2.1.220. **Gate** = exit 2 + stderr, blocks the action
and feeds the error back to Claude. **Guide** = exit 0 + JSON
`additionalContext`, Claude sees it and acts. **Silent** = exit 0, no output.

### BEGIN — the prompt arrives

| Event / hook | Type | What it does |
|---|---|---|
| SessionStart → `session-context` | Guide | Inject memory digest: global principles, prioritized lessons, preferences, project STATE.md, project CLAUDE.md |
| SessionStart → `settings-validate` | Guide | Catch broken `settings.json` wiring that silently kills hooks |
| SessionStart → `project-audit` | Guide | Gap-check project discipline gates (CI, lint, strict TS, git hooks, secrets) |
| SessionStart → `hook-health` | Guide | Verify every configured hook still resolves + runs |
| UserPromptSubmit → `prompt-guard` | Guide | Correction language → nudge to `/self-evolve` |
| UserPromptSubmit → `phase-gate` | Guide | Milestone/shipping language → nudge to `audit` |
| UserPromptSubmit → **`task-triage`** (NEW) | Guide | Classify task (bug/feature/refactor/question), inject workflow briefing, pre-mortem, exit criteria |

### MID — the tool call runs

| Event / hook | Type | What it does |
|---|---|---|
| PreToolUse (Bash/PS) → `danger-guard` | **Gate** | Block `rm -rf`, force-push, `curl|bash`, `.env` writes, secret exposure, destructive review-request commands |
| PostToolUse (Write/Edit) → `verify-edit` | **Gate** | Lint + type-check the file just touched; feed findings back |
| PostToolUse (Bash) → `dep-guard` | **Gate** | New `pnpm add` / `npm install` → must pass pre-check (stdlib? existing dep? new needs a `.ponytail` comment) |
| PreToolUse (Bash) → **`discipline-guard`** (NEW) | Guide | 5+ file blast radius → nudge "design first"; builds/refactors matching existing patterns → nudge "reuse first"; `mkdir` → nudge |
| PostToolUse (any) → `hook-latency` | Silent | Track hook timing; alert if a hook is the bottleneck |

### END — turn or session ends

| Event / hook | Type | What it does |
|---|---|---|
| Stop → `verify-turn` | **Gate** | Run project suite if source changed in last 10 min; red suite → block "done" |
| Stop → **`ship-gate`** (NEW, merged into verify-turn) | **Gate** | Scan for leftover `TODO/FIXME`, `console.log`/`debugger`, commented-out code, empty `catch`, source:tests ratio, uncommitted changes → block |
| SubagentStop → `subagent-guard` | Guide | Verify subagent returned something focused, no runaway work |
| PreCompact → `precompact-checkpoint` | Silent | Write compaction timestamp to STATE.md so the next context resumes |
| SessionEnd → **`retrospective`** (NEW) | Silent | Session stats → `~/.claude/self/stats.json` for hotspot detection |

### ACROSS

| Event / hook | Type | What it does |
|---|---|---|
| PreCompact + SessionStart → `context-mode-cache-heal` | Silent | Repair context-mode cache index |
| Notification → `notify-alert` | Silent | Surface long-task completion to the user |

---

## 5. New components (v1.0.0 additions)

### 5.1 `task-triage` (BEGIN)
Python brain. Reads the prompt. Classifies by keyword + intent:
`bug | feature | refactor | question | chore`. Injects as `additionalContext`
on exit 0:
```
# Task: <type>  (confidence, 2s)
Reason: <one line>
Explore first: <paths or "—">
Plan before code: <required | suggested | none>   # bug/feature/refactor: required
Pre-mortem: <edge cases the type normally trips on>   # from templates + project LESSONS.md
Exit criteria: <what "done" must satisfy>   # from templates + task-type
Gotchas: <matching entries from project LESSONS.md, capped>
```
Deliberately narrow pattern set — false positive on every prompt is noise.
Missed classifications fall back to a generic pro-workflow briefing. Never
blocks (guide only); rough 2s budget.

### 5.2 `discipline-guard` (MID)
Python brain on PreToolUse(Bash|PowerShell). Guidance, never blocks:
- Command touches ≥5 files plus no design marker (`plan`, `design`) → nudge
  "wide blast radius — did you design this first?"
- `mkdir -p`/`New-Item` creating dirs while a similar pattern exists in the
  repo → nudge "reuse first: is there already X?"
- `pnpm build`/`tsc`/`pytest` after ≥5 source edits with 0 test edits → nudge
  "write tests for what you changed"
Same guard company as `dep-guard`; check command line, not the file tree.

### 5.3 `ship-gate` (END, merged into `verify-turn`)
Python brain, runs on Stop. **Gate.** Blocks "done" when:
- Build/typecheck fails (delegated to existing suite runner)
- Test suite red
- `TODO`/`FIXME`/`XXX` remain in files touched this turn
- `console.log`/`debugger` in committed source
- commented-out code blocks in touched files
- empty `catch` / `except: pass` blocks
- ≥5 source files changed with 0 test files
- uncommitted changes exist (nudge, not block — commit is a user decision)

Feedback: repeat findability — the hook names each failing item so Claude fixes
in-turn. Budget: full scan on Stop only, not on every tool call.

### 5.4 `retrospective` (END)
Python brain on SessionEnd. Silent. Appends to
`~/.claude/self/stats.json`: session id, date, files touched, commits, tests
added, corrections-count, duration. No per-turn writes. v1.0.0 ships the
recorder; a `hotspot-report` skill derivative is a v1.1 item — keep scope tight.

### 5.5 `templates/settings.json.template`
Baseline documented settings (NOT your personal settings — that file never
shipped). Shows: `$schema`, `hooks` map, `permissions` allow/ask/deny examples
(deny `.env` reads, `curl *`), `disableBypassPermissionsMode`, plugin enablement.

### 5.6 `templates/CLAUDE.md.global`
Standing global discipline for `~/.claude/CLAUDE.md`. **Overwrite confirmed with
disclaimer + backup.** Structure:
```
# Protocol (10 standing principles, stable)
# Process (triage: trivial/small/medium/large → which pipeline)
# Standards (security, testing, error handling, performance, a11y)
# Anti-patterns (never-do list)
# Tool discipline (context-mode first, ponytail active, superpowers for medium+)
```
`CLAUDE.md.global` carries the *discipline* teeth; project `CLAUDE.md` files
carry the *stack* (architecture/commands/gotchas). Both stay at full strength —
no compression that loses teeth.

---

## 6. Install behavior (scripts/install.sh + install.ps1)

```
1. Prereq check     node >=22, python3, git, claude CLI >= 2.1  (name what's missing)
2. Backup           cp settings.json settings.json.bak.<ts>; cp CLAUDE.md CLAUDE.md.bak.<ts>
3. Merge settings   jq deep-merge: preserve env/model/permissions;           add hooks + plugins
4. Copy hooks       hooks/ -> ~/.claude/hooks/
5. Copy skills      8 discipline skills -> ~/.claude/skills/
6. Copy self        PRINCIPLES/PREFERENCES templates -> ~/.claude/self/ (never overwrite existing)
7. Global CLAUDE.md overwrite -> ~/.claude/CLAUDE.md   (backup done in step 2; print disclaimer)
8. Selector         per-item y/n for: plugins (ponytail/context-mode/superpowers)
                    + optional community skills; recommended default marked
9. Validate         run settings-validate + hook-health; report OK / failures
10. Done            print summary + next steps (git pull && install to update)
```
Idempotent + convergent: safe to run 100×, never destroys personal config.

---

## 7. Error handling & resilience

- Every hook wrapper: `set +e`, capture stdin → `HOOK_INPUT`, call the Python
  brain, **any error → exit 0** so a broken hook never blocks a session.
- Fail-fast only where intentional: guards that must gate (danger, dep, edit,
  turn) exit 2 deliberately on findings.
- `hook-health` + `settings-validate` watch for silent failures — a hook that
  exists but never fires is the failure mode the system defends against.
- Install: destructive steps (backup before write, overwrite only with
  confirmation) — no data loss path.
- CI validates install on clean linux + windows runners.

## 8. Testing strategy

| Layer | What |
|---|---|
| Unit (assert-based) | `test/` — self-check each Python brain's core: `task-triage` classification over sample prompts; `ship-gate` finders over fixture code; `dep-guard`/`danger-guard` pattern matches; hook JSON emission shape |
| Install dry-run | shell test: `./scripts/install.sh --dry-run` on a temp HOME → verify file map + merge preserves a fixture personal settings.json |
| CI | GitHub Actions: `test/` suite + install dry-run on ubuntu-latest and windows-latest |
| Manual (unverifiable here) | Real `claude` session behavior, live hook firing, selector UX — user runs on a scratch machine |

## 9. Deliverables checklist — definition of done

- [x] Repo scaffolded at `C:\Users\nbzkr\Coding\one-man`: git init, package.json, tsconfig strict, eslint, `.gitignore`
- [x] `hooks/` compiles: guards in `hooks/`, shared helper, existing 25 scripts migrated
- [x] `task-triage`, `discipline-guard`, `ship-gate`, `retrospective` implemented — **partial**: `ship-gate` done (merged into verify-turn); `task-triage`, `discipline-guard`, `retrospective` NOT built (v1.1 defer per §11)
- [x] `templates/` + `self/` ship real templates (no personal data)
- [x] `install.sh` + `install.ps1` implement the 10-step flow, `--dry-run` flag
- [x] `test/` asserts pass (`node test/*` or a minimal runner)
- [x] CI green: linux + windows install validation
- [x] `pnpm build && pnpm test` pass in-repo — `build` dropped: hooks copy, not compile (ponytail)
- [x] README: what, why, install, update, cross-platform notes
- [x] First commit + push to `nzkbuild/one-man` (public)

## 10. Milestones (implementation order)

1. **M1 — Scaffold**: repo, git, package.json, tsconfig strict, eslint, .gitignore, README stub, CI skeleton. First commit green.
2. **M2 — Migrate existing**: copy & harden the 25 hooks + 8 skills into the repo layout; make them self-contained (paths resolved from install location, not `~/.claude/`).
3. **M3 — New brains**: task-triage, discipline-guard, ship-gate, retrospective + their tests.
4. **M4 — Templates + self**: settings.json.template, CLAUDE.md.global, PRINCIPLES/PREFERENCES templates.
5. **M5 — Installers**: install.sh + install.ps1, dry-run mode, selector, merge logic.
6. **M6 — CI + docs**: workflow for both OS, README, clean lint/typecheck/test/build.
7. **M7 — Release 1.0.0**: tag, release notes, push public.

## 11. Explicitly deferred (v1.1+)

- `hotspot-report` skill (hotspot detection UI over `stats.json`)
- Auto-merge of community design skills from marketplace without selector
- `context`-mode workflow: real subagent dispatch templates

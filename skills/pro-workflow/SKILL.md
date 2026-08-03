---
name: pro-workflow
description: The full professional workflow checklist for consistent, high-quality delivery. Use when starting a non-trivial multi-step task (a feature, a refactor, a bug hunt, anything spanning multiple files or requiring verification).
---

# Professional workflow

Standing protocol for delivering consistent, professional results. The summary lives in
PRINCIPLES.md (always loaded); this is the detailed, actionable checklist.

## 1. Understand
- Restate the goal in one line. If the request is ambiguous about scope or approach, ask
  before building — don't guess on non-trivial work.
- **Read the project's CLAUDE.md** if it exists — it contains architecture, stack,
  conventions, and project-specific gotchas that short-circuit research.
- Read the relevant code and config first. Identify existing patterns, utilities, and
  conventions to reuse. Detect the build tool, test runner, and linter from config files.

## 2. Plan (for non-trivial work)
- Outline the approach and the files involved before writing code.
- For multi-file / architectural / risky work, align with the user first.
- Track multi-step work with tasks so progress is visible.

## 3. Implement
- Match surrounding style, naming, and libraries. Reuse over reinvention.
- Solve the problem asked — no unrequested features, abstractions, or scope creep.
- Security by default: validate inputs, parameterize queries, never hardcode secrets,
  flag any network-exposed endpoint that lacks auth.
- Respect blast radius: proceed on local reversible changes; confirm before destructive,
  shared, or hard-to-reverse actions.

## 4. Verify (before claiming done)
- Run the build/compile step. Run relevant tests. Add tests for new features/bugfixes.
- If the project has CI, check the run status after pushing — local verification is not a
  substitute for CI on a clean machine. Use `gh run list` / `gh run view`.
- If verification is impossible (missing deps, environment), say so and why.
- Report faithfully: show failing output, name skipped steps, only say "done" when checked.
- Clean up temporary files.

## 5. Capture
- If the user corrected something along the way, invoke `/self-evolve` to persist the
  lesson before wrapping up.

## 6. If stuck
- After two failed attempts, stop patching. Diagnose the root cause, try a fundamentally
  different approach, and flag any deviation from the original intent.

Keep responses proportional: simple asks get short answers; complex work gets thoroughness.

# Security Policy

## Reporting a vulnerability

This repo is a Claude Code discipline system — hooks, skills, templates, installers.
It does NOT process user data, run servers, or store credentials. The attack surface
is limited to:

- Hook scripts executed by Claude Code (they run with the user's privileges)
- Installer scripts (`install.sh` / `install.ps1`) executed by the user
- Templates that become the user's `settings.json` / `CLAUDE.md`

**If you find a vulnerability** — especially something that could exfiltrate secrets,
inject commands, or break the deny/allow permission model — please report it privately:

- Open a GitHub issue with `[SECURITY]` in the title, OR
- Email the maintainer (see GitHub profile), OR
- If it's a 0-day-level issue, do NOT open a public issue; contact privately first.

Please include: what version, the affected script, a minimal repro, and the impact.

## Response

The maintainer will acknowledge within 7 days and aim for a fix within 14.
Coordinated disclosure is appreciated: 30-day embargo before public details.

## Security posture (for contributors)

- Never commit secrets, keys, or personal paths (pre-commit secret scanner enforces).
- Deny rules in `templates/settings.json.template` protect `.env*`, keys, curl.
- Hooks are fail-open by design: a crash must never block a session.
- Token-aware guards: benign mentions of danger strings must not false-block.

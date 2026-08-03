#!/usr/bin/env bash
# one-man install — POSIX/Mac/Linux bootstrap.
# Idempotent + convergent: safe to re-run, never destroys personal config.
# Usage: bash scripts/install.sh [--dry-run]
set +e

DRY=0
[ "$1" = "--dry-run" ] && DRY=1

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
TIMESTAMP="$(date +%s)"

say() { printf '[one-man] %s\n' "$*"; }
warn() { printf '[one-man] WARN: %s\n' "$*" >&2; }
die()  { printf '[one-man] ERROR: %s\n' "$*" >&2; exit 1; }

# Forwarded: run the action but skip real writes when dry.
run() {
  if [ "$DRY" = "1" ]; then
    printf '  (dry-run) would: %s\n' "$*"
  else
    "$@"
  fi
}

# ---------- Step 0: prereq ----------
say "Prereq check"
command -v node >/dev/null 2>&1 || die "node>=22 required (missing)"
command -v git  >/dev/null 2>&1 || die "git required (missing)"
command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 || die "python3 required (missing)"
command -v claude >/dev/null 2>&1 || warn "claude CLI not found — hooks will install but you can't run Claude Code until it's installed"
NODE_MAJOR="$(node -e 'console.log(process.versions.node.split(".")[0])' 2>/dev/null)"
[ -n "$NODE_MAJOR" ] && [ "$NODE_MAJOR" -ge 22 ] 2>/dev/null || warn "node <22 detected ($NODE_MAJOR) — hooks should work but Node 22+ is the supported floor"

# ---------- Step 1: backup ----------
if [ -f "$CLAUDE_HOME/settings.json" ]; then
  say "Backup settings.json"
  run cp "$CLAUDE_HOME/settings.json" "$CLAUDE_HOME/settings.json.bak.$TIMESTAMP"
fi
if [ -f "$CLAUDE_HOME/CLAUDE.md" ]; then
  say "Backup CLAUDE.md"
  run cp "$CLAUDE_HOME/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md.bak.$TIMESTAMP"
fi
[ "$DRY" = "1" ] && { say "Dry-run complete. No files were written."; exit 0; }

# ---------- Step 2: ensure dirs ----------
mkdir -p "$CLAUDE_HOME/hooks" "$CLAUDE_HOME/skills" "$CLAUDE_HOME/self" "$CLAUDE_HOME/plugins"

# ---------- Step 3: hooks ----------
say "Install hooks (14)"
cp "$REPO"/hooks/*.sh "$REPO"/hooks/*.py "$REPO"/hooks/*.mjs "$CLAUDE_HOME/hooks/" 2>/dev/null
cp "$REPO"/hooks/test_*.py "$CLAUDE_HOME/hooks/" 2>/dev/null

# ---------- Step 4: skills (8 discipline) ----------
say "Install discipline skills (8)"
for d in audit checkpoint ctx-agent-history-search dep-audit memory-maintain pro-workflow recall self-evolve; do
  rm -rf "$CLAUDE_HOME/skills/$d"
  cp -r "$REPO/skills/$d" "$CLAUDE_HOME/skills/"
done

# ---------- Step 5: self templates (never overwrite existing) ----------
say "Install self/ templates (preserve existing)"
# PRINCIPLES is the generic discipline baseline — safe to refresh.
cp -f "$REPO/self/PRINCIPLES.md.template" "$CLAUDE_HOME/self/PRINCIPLES.md" 2>/dev/null || true
# PREFERENCES is user-curated — only write if missing.
[ -f "$CLAUDE_HOME/self/PREFERENCES.md" ] || cp "$REPO/self/PREFERENCES.md.template" "$CLAUDE_HOME/self/PREFERENCES.md" 2>/dev/null || true

# ---------- Step 6: global CLAUDE.md (backup done in step 1) ----------
say "Install global CLAUDE.md (backup made)"
cp "$REPO/templates/CLAUDE.md.global" "$CLAUDE_HOME/CLAUDE.md"

# ---------- Step 7: merge settings (jq or python) ----------
say "Merge settings — preserve your env/model, add hooks + permissions"
if [ -f "$CLAUDE_HOME/settings.json" ]; then
  if command -v jq >/dev/null 2>&1; then
    # Build the hooks block from the template's own structure (minimal merge):
    python3 "$REPO/scripts/merge_settings.py" "$CLAUDE_HOME/settings.json" "$CLAUDE_HOME"
  else
    python3 "$REPO/scripts/merge_settings.py" "$CLAUDE_HOME/settings.json" "$CLAUDE_HOME"
  fi
else
  python3 "$REPO/scripts/merge_settings.py" "$CLAUDE_HOME" "$CLAUDE_HOME" --init
fi

# ---------- Step 7.5: plugins + design skills (from manifest, per-machine) ----------
if command -v claude >/dev/null 2>&1; then
  say "Install plugins from manifest (selector: y/n per plugin)"
  for p in $(python3 -c "
import json
m = json.load(open('$REPO/install.manifest.json'))
print('\n'.join(m['plugins']))" 2>/dev/null); do
    if [ "$DRY" = "1" ]; then
      printf '  (dry-run) would: claude plugins install %s\n' "$p"
    else
      read -r -p "  Install plugin $p? [Y/n] " ans </dev/tty
      case "$ans" in n|N) echo "  skip $p";; *) claude plugins install "$p" 2>/dev/null && echo "  installed $p";; esac
    fi
  done
  say "Symlink design skills from ~/.agents/skills (when present)"
  for s in $(python3 -c "
import json
m = json.load(open('$REPO/install.manifest.json'))
print('\n'.join(m['designSkills']))" 2>/dev/null); do
    if [ -d "$HOME/.agents/skills/$s" ]; then
      [ "$DRY" = "1" ] && printf '  (dry-run) would: ln -s %s\n' "$s" || { [ -e "$CLAUDE_HOME/skills/$s" ] || ln -s "$HOME/.agents/skills/$s" "$CLAUDE_HOME/skills/$s"; }
    fi
  done
else
  say "claude CLI not found — skipping plugin/design-skill install (run after installing Claude Code)"
fi

# ---------- Step 8: validate ----------
say "Validate hook wiring"
python3 "$CLAUDE_HOME/hooks/settings-validate.py" < /dev/null >/dev/null 2>&1
python3 "$CLAUDE_HOME/hooks/hook-health.py" < /dev/null >/dev/null 2>&1
say "Hook self-checks:"
(cd "$CLAUDE_HOME/hooks" && python3 test_danger_guard.py && python3 test_dep_guard.py && python3 test_ship_gate.py && python3 test_plan_check.py 2>/dev/null)

# ---------- Step 9: done ----------
say "Install complete. Restart Claude Code to bind settings permissions."
say "Update anytime: git pull && bash scripts/install.sh"

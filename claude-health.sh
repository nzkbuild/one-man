#!/usr/bin/env bash
# claude-health.sh — one-shot diagnostic for the Claude Code discipline system.
# Verifies, in one command, that the safety + autonomy + done-gate stack is wired
# and functional. Run any time the environment feels off, after an update, or
# before trusting it unattended.
#
# READ-only. Never edits anything. Exit 0 = all good, 1 = a check failed.

set -u
H="$(command -v claude >/dev/null 2>&1 && claude --version 2>/dev/null | head -1 || echo 'NOT FOUND')"
CFG_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
P="$(command -v python || command -v python3 || echo '')"

pass=0; fail=0
ok()   { printf '  [OK]   %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  [FAIL] %s\n' "$1"; fail=$((fail+1)); }

echo "== claude-health: $H =="

echo "-- 1. settings.json valid --"
if [ -f "$HOME/.claude/settings.json" ] && "$P" -c "import json,os; json.load(open(os.path.expanduser('~/.claude/settings.json')))" 2>/dev/null; then
  ok "settings.json parses"
else
  bad "settings.json missing or invalid JSON"
fi

echo "-- 2. hooks wired + on disk --"
# Pull hook filenames directly from settings.json — no python, no escaping hell.
WIRED="$(
  python - "$HOME/.claude/settings.json" <<'PYEOF'
import json, os, re, sys
d = json.load(open(sys.argv[1]))
outs = []
for groups in d['hooks'].values():
    for grp in groups:
        for h in grp.get('hooks', []):
            m = re.search(r'"([^"]+\.(?:sh|py|mjs))"', h.get('command', ''))
            if m:
                outs.append(os.path.basename(m.group(1)))
print(' '.join(sorted(set(outs))))
PYEOF
)"
[ -z "$WIRED" ] && { bad "no hooks found in settings"; exit 1; }
for f in $WIRED; do
  if [ -f "$CFG_HOME/hooks/$f" ]; then ok "hook exists: $f"; else bad "MISSING hook: $f"; fi
done

echo "-- 3. permissions deny (secrets) --"
if "$P" -c "
import json, os
d = json.load(open(os.path.expanduser('~/.claude/settings.json')))
deny = d.get('permissions', {}).get('deny', [])
print('deny count:', len(deny))
secrets = [x for x in deny if '.env' in x or 'credential' in x or 'pem' in x]
print('secret denies:', len(secrets))
" 2>/dev/null | grep -q "secret denies: [1-9]"; then
  ok "deny rules protect .env/credentials"
else
  bad "no secret deny rules in permissions"
fi

echo "-- 4. ship-gate (done has teeth) --"
if [ -f "$HOME/.claude/hooks/ship-gate.py" ] && "$P" -c "import ast, os; ast.parse(open(os.path.expanduser('~/.claude/hooks/ship-gate.py')).read())" 2>/dev/null; then
  ok "ship-gate.py parses"
else
  bad "ship-gate.py missing or broken"
fi

echo "-- 5. hook self-checks --"
for t in test_danger_guard.py test_dep_guard.py test_ship_gate.py; do
  if [ -f "$CFG_HOME/hooks/$t" ] && cd "$CFG_HOME/hooks" && "$P" "$t" >/dev/null 2>&1; then
    ok "self-check: $t"
  else
    bad "self-check FAILED: $t"
  fi
done

echo ""
echo "== result: $pass ok, $fail failed =="
[ "$fail" = "0" ] && exit 0 || exit 1

#!/usr/bin/env bash
# one-man loop report — the system's own post-mortem.
# Synthesizes stats.json + corrections into a monthly review: what fired,
# what was corrected, what to tune. The loop-closed artifact.
# Usage: bash scripts/loop-report.sh [YYYY-MM]
set +e

STATS="$HOME/.claude/self/stats.json"
REPORT_DIR="${ONE_MAN_REPORT_DIR:-$HOME/.claude/reports}"
MONTH="${1:-$(date +%Y-%m)}"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/loop-$MONTH.md"

[ -f "$STATS" ] || { echo "no stats.json yet — retrospective hasn't recorded sessions"; exit 0; }

python - "$STATS" "$REPORT" "$MONTH" <<'PYEOF'
import json, sys
stats_path, report, month = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    entries = json.load(open(stats_path))
except Exception:
    entries = []
# filter to the month (date field is ISO)
month_entries = [e for e in entries if str(e.get("date", "")).startswith(month)]
with open(report, "w", encoding="utf-8") as f:
    f.write(f"# one-man loop report — {month}\n\n")
    if not month_entries:
        f.write("No sessions recorded this month.\n")
        sys.exit(0)
    f.write(f"Sessions: {len(month_entries)}\n")
    total_min = sum(e.get("duration_min", 0) for e in month_entries)
    total_commits = sum(e.get("commits", 0) for e in month_entries)
    src = sum(e.get("files_touched_src", 0) for e in month_entries)
    tests = sum(e.get("files_touched_test", 0) for e in month_entries)
    f.write(f"Total time: {total_min:.0f} min | commits: {total_commits} | src files: {src} | test files: {tests}\n\n")
    corr = [e for e in month_entries if e.get("corrections", 0) > 0]
    if corr:
        f.write(f"Corrections: {len(corr)} sessions had them — review the recurring ones.\n\n")
    else:
        f.write("No corrections recorded. Either none happened or prompt-guard isn't feeding them.\n\n")
    f.write("## What to tune next\n- Look at the guards that fired most. Noisy guard > silence, but a guard that\n  fires constantly without a correction is likely a false-positive pattern.\n")
print(f"loop report written: {report}")
PYEOF

#!/usr/bin/env python3
"""Self-check for hotspot-report.py — behavioral feedback signals."""
import importlib.util
import json
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("hr", Path(__file__).parent / "hotspot-report.py")
_hr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hr)

PASS = 0


def check(name, cond):
    global PASS
    if not cond:
        print(f"FAIL: {name}")
        raise SystemExit(1)
    PASS += 1


def run(stats):
    """Point module at temp stats, run main, capture output."""
    import io
    from contextlib import redirect_stdout
    with tempfile.TemporaryDirectory() as tmp:
        _hr.STATS_FILE = Path(tmp) / "stats.json"
        _hr.STATS_FILE.write_text(json.dumps(stats), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                _hr.main()
            except SystemExit:
                pass
        return buf.getvalue()


# correction cluster -> report
out = run([{"corrections": 1, "duration_min": 30, "commits": 1},
           {"corrections": 1, "duration_min": 30, "commits": 1},
           {"corrections": 1, "duration_min": 30, "commits": 1}])
check("correction cluster flagged", "corrections" in out)

# long-session-low-output -> report
out = run([{"duration_min": 120, "commits": 0, "files_touched_src": 3, "files_touched_test": 0},
           {"duration_min": 150, "commits": 0, "files_touched_src": 2, "files_touched_test": 0}])
check("slow sessions flagged", "90+ min" in out)

# no-tests -> report
out = run([{"files_touched_src": 5, "files_touched_test": 0, "duration_min": 20, "commits": 1},
           {"files_touched_src": 4, "files_touched_test": 0, "duration_min": 20, "commits": 1},
           {"files_touched_src": 6, "files_touched_test": 0, "duration_min": 20, "commits": 1}])
check("no-tests flagged", "no test files" in out)

# clean stats -> silent
out = run([{"duration_min": 30, "commits": 2, "files_touched_src": 2, "files_touched_test": 1}])
check("clean silent", "Hotspot" not in out)

# empty/missing -> silent
out = run([])
check("empty stats silent", "Hotspot" not in out)

print(f"OK: {PASS} assertions passed")

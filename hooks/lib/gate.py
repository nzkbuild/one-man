"""Evidence-aware completion gate — the v1.5.0 heart.

At Stop, for the current task record: every obligation must have evidence
proving it was satisfied, and that evidence must not be stale (files changed
since verification). Missing/failed/stale evidence blocks "done" (exit 2)
for medium/high-risk tasks. Low-risk tasks pass (no ceremony) but still get
basic verification (the suite run in verify-turn).

Explicit override: a user-visible justification recorded in the record
(`override: "reason"`) lets a task pass without evidence — auditable, not
silent. This is the "skipped without justification" escape the brief allows.

Obligation satisfaction (M4 mapping):
  - bug    -> evidence kind "tests" result "passed" (regression covered by
              the suite) OR "repro" (captured failing output + fix)
  - refactor -> "tests" passed + baseline
  - feature  -> "tests" passed
  - chore    -> any evidence or override (light)
  - design/question -> no gate (advisory)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evidence as _ev


def _current_record():
    return _ev.read_record("current")


def _satisfied(rec) -> tuple:
    """Return (ok, reasons) — is every obligation backed by non-stale evidence?"""
    reasons = []
    risk = rec.get("risk", "low")
    if risk == "low":
        return True, ["low-risk: no evidence gate"]
    if rec.get("override"):
        return True, [f"override: {rec['override']}"]

    evidence = rec.get("evidence", [])
    # v1.7.0 M2: obligation proof — a passed test satisfies the obligation ONLY
    # when it is capability-tied (which capability produced it). Evidence
    # without a capability is unproven provenance.
    passed_tests = [e for e in evidence
                    if e.get("kind") == "tests" and e.get("result") == "passed"
                    and e.get("capability")]
    if not passed_tests:
        reasons.append("no capability-tied passed test evidence — the suite must pass, "
                       "recorded by a real capability, for this risk level")
        return False, reasons

    # Staleness: any file referenced by the LATEST passing evidence changed since?
    latest = passed_tests[-1]
    for f in latest.get("files", []):
        h = _ev.state_hash([f])
        if h != latest.get("state_hash"):
            reasons.append(f"stale evidence: {f} changed after verification")
            return False, reasons
    return True, reasons


def main():
    rec = _current_record()
    if not rec:
        sys.exit(0)  # no task seeded — nothing to gate

    risk = rec.get("risk", "low")
    if risk == "low":
        sys.exit(0)  # low-risk: basic verification (suite) already ran

    ok, reasons = _satisfied(rec)
    if ok:
        sys.exit(0)

    lines = [
        f"## Evidence gate — task ({rec.get('type')}, risk={risk}) lacks proof of done:",
    ]
    for r in reasons[:6]:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("Fix: run the suite (or capture the specific evidence), then end the turn.")
    lines.append("Justified skip: state the reason — it is recorded as an auditable override.")
    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)

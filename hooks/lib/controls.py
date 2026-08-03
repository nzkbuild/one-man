"""Control criticality declaration (v1.5.0 M6).

Reads one-man.controls.json (installed to ~/.claude/one-man.controls.json;
repo copy is the source). Declares what each control must do on failure:
  - safety: fail closed — on the control's OWN failure, block + log
  - quality: block completion/release (existing exit-2 gates)
  - advisory: warn only (existing guides)

The point: a safety control that crashes must NOT silently disarm into
"all good". With ONE_MAN_FAIL_CLOSED=1, safety controls exit 2 on their own
errors instead of the default fail-open. Any error reading config -> safe
default (fail-open preserved; the declaration is advisory if absent).
"""
import json
import os
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
REPO_CONTROLS = Path(__file__).parent.parent.parent / "one-man.controls.json"
USER_CONTROLS = HOME / ".claude" / "one-man.controls.json"


def criticality(control: str) -> str:
    """Return safety|quality|advisory for a control (default: advisory)."""
    for src in (USER_CONTROLS, REPO_CONTROLS):
        try:
            if src.exists():
                data = json.loads(src.read_text(encoding="utf-8"))
                c = data.get("controls", {}).get(control, {})
                return c.get("criticality", "advisory")
        except Exception:
            continue
    return "advisory"


def fail_closed_enabled() -> bool:
    """True when safety controls must fail closed (explicit opt-in)."""
    return os.environ.get("ONE_MAN_FAIL_CLOSED", "0") == "1"

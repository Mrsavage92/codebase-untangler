#!/usr/bin/env python3
"""
update_state.py - Update fields in state.json and regenerate STATE.md mirror.

Usage:
  python -m scripts.update_state set <path.to.field> <value>
  python -m scripts.update_state advance <phase>          # mark phase done, advance to next
  python -m scripts.update_state override <phase> <gate> "reason"
  python -m scripts.update_state record-tests <passing> <failing>
  python -m scripts.update_state regen                    # just regenerate STATE.md from JSON
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(".untangler")
STATE_JSON = STATE_DIR / "state.json"
STATE_MD = STATE_DIR / "STATE.md"
OVERRIDES_LOG = STATE_DIR / "overrides.log"


def load():
    return json.loads(STATE_JSON.read_text())


def save(state):
    STATE_JSON.write_text(json.dumps(state, indent=2))
    STATE_MD.write_text(render_md(state))


def render_md(state):
    lines = [
        "# Codebase Untangler - State",
        "",
        f"**Started**: {state['started_at']}",
        f"**Current phase**: {state['current_phase']} ({state['phases'][str(state['current_phase'])]['name']})",
        f"**Branch**: {state['baseline']['branch'] or '(not set)'}",
        f"**Stack**: {', '.join(state['stack']) if state['stack'] else '(not detected)'}",
        "",
        "## Phase progress",
        ""
    ]
    for i in range(6):
        p = state["phases"][str(i)]
        marker = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}.get(p["status"], "[?]")
        lines.append(f"- {marker} Phase {i}: {p['name']} ({p['status']})")
    lines.extend([
        "",
        "## Baseline",
        "",
        f"- Total LOC: {state['baseline']['total_loc'] or 'tbd'}",
        f"- File count: {state['baseline']['file_count'] or 'tbd'}",
        f"- Tests: {state['baseline']['test_count'] or 'tbd'} "
        f"({state['baseline']['tests_passing'] or 0} passing, {state['baseline']['tests_failing'] or 0} failing)",
        "",
        "## Overrides used",
        ""
    ])
    if state["overrides"]:
        for o in state["overrides"]:
            lines.append(f"- {o['timestamp']} Phase {o['phase']}: {o['gate']} - {o['reason']}")
    else:
        lines.append("(none)")
    lines.extend(["", "---", "*Auto-generated from state.json.*"])
    return "\n".join(lines) + "\n"


def set_nested(d, path, value):
    keys = path.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    # try to parse value as number/bool/null
    try:
        value = json.loads(value)
    except (ValueError, TypeError):
        pass
    d[keys[-1]] = value


def cmd_set(args):
    if len(args) != 2:
        print("Usage: set <path> <value>")
        sys.exit(2)
    state = load()
    set_nested(state, args[0], args[1])
    save(state)
    print(f"Set {args[0]} = {args[1]}")


def cmd_advance(args):
    if len(args) != 1:
        print("Usage: advance <phase>")
        sys.exit(2)
    phase = args[0]
    state = load()
    if phase not in state["phases"]:
        print(f"Unknown phase: {phase}")
        sys.exit(2)
    state["phases"][phase]["status"] = "done"
    state["phases"][phase]["completed_at"] = datetime.now(timezone.utc).isoformat()
    next_phase = str(int(phase) + 1)
    if next_phase in state["phases"]:
        state["current_phase"] = int(next_phase)
        state["phases"][next_phase]["status"] = "in_progress"
        state["phases"][next_phase]["started_at"] = datetime.now(timezone.utc).isoformat()
    save(state)
    print(f"Phase {phase} marked done. Now at phase {state['current_phase']}.")


def cmd_override(args):
    if len(args) != 3:
        print('Usage: override <phase> <gate> "<reason>"')
        sys.exit(2)
    phase, gate, reason = args
    state = load()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "gate": gate,
        "reason": reason
    }
    state["overrides"].append(entry)
    save(state)
    with OVERRIDES_LOG.open("a") as f:
        f.write(f"{entry['timestamp']} phase={phase} gate={gate} reason={reason}\n")
    print(f"Override recorded for phase {phase} gate '{gate}'.")


def cmd_record_tests(args):
    if len(args) != 2:
        print("Usage: record-tests <passing> <failing>")
        sys.exit(2)
    passing, failing = int(args[0]), int(args[1])
    state = load()
    state["baseline"]["tests_passing"] = passing
    state["baseline"]["tests_failing"] = failing
    state["baseline"]["test_count"] = passing + failing
    state["last_test_run"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "passing": failing == 0,
        "passing_count": passing,
        "failing_count": failing
    }
    save(state)
    print(f"Recorded: {passing} passing, {failing} failing.")


def cmd_regen(args):
    state = load()
    save(state)
    print("STATE.md regenerated.")


COMMANDS = {
    "set": cmd_set,
    "advance": cmd_advance,
    "override": cmd_override,
    "record-tests": cmd_record_tests,
    "regen": cmd_regen,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    if not STATE_JSON.exists():
        print(f"ERROR: {STATE_JSON} not found. Run init_state.py first.")
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()

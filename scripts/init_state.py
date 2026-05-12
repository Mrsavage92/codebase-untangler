#!/usr/bin/env python3
"""
init_state.py - Initialise the .untangler/ state directory.

Creates state.json (machine-readable, source of truth) and STATE.md (human mirror).
Run once at the start of a fresh engagement.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


STATE_DIR = Path(".untangler")
STATE_JSON = STATE_DIR / "state.json"
STATE_MD = STATE_DIR / "STATE.md"
AUDIT_JSON = STATE_DIR / "audit.json"
DEFERRED_MD = STATE_DIR / "deferred.md"
OVERRIDES_LOG = STATE_DIR / "overrides.log"
RUNNING_MD = STATE_DIR / "RUNNING.md"


def initial_state():
    return {
        "schema_version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "current_phase": 0,
        "phases": {
            "0": {"name": "Triage", "status": "in_progress", "gates": {}, "started_at": datetime.now(timezone.utc).isoformat()},
            "1": {"name": "Audit", "status": "pending", "gates": {}},
            "2": {"name": "Safety Net", "status": "pending", "gates": {}},
            "3": {"name": "Refactor", "status": "pending", "gates": {}},
            "4": {"name": "Hardening", "status": "pending", "gates": {}},
            "5": {"name": "Handover", "status": "pending", "gates": {}}
        },
        "baseline": {
            "git_tag": "pre-refactor-baseline",
            "branch": None,
            "total_loc": None,
            "file_count": None,
            "test_count": None,
            "tests_passing": None,
            "tests_failing": None
        },
        "stack": [],
        "top_5_signed_off_at": None,
        "overrides": []
    }


def initial_audit():
    return {
        "schema_version": 1,
        "issues": [],
        "top_5": [],
        "deferred": []
    }


def render_state_md(state):
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

    lines.extend([
        "",
        "---",
        "*This file is auto-generated from state.json. Do not edit directly.*"
    ])
    return "\n".join(lines) + "\n"


def main():
    if STATE_DIR.exists() and STATE_JSON.exists():
        print(f"ERROR: {STATE_JSON} already exists. Use update_state.py instead.")
        sys.exit(1)

    STATE_DIR.mkdir(exist_ok=True)

    state = initial_state()
    audit = initial_audit()

    STATE_JSON.write_text(json.dumps(state, indent=2))
    AUDIT_JSON.write_text(json.dumps(audit, indent=2))
    STATE_MD.write_text(render_state_md(state))
    DEFERRED_MD.write_text("# Deferred Items\n\nProblems noticed during refactor but deliberately not fixed now.\n\n")
    OVERRIDES_LOG.write_text("")
    if not RUNNING_MD.exists():
        RUNNING_MD.write_text("# How to run this app\n\nDocument the exact steps to run locally.\n\n## Setup\n\n## Run\n\n## Test\n\n")

    print(f"Initialised state in {STATE_DIR}/")
    print(f"  - {STATE_JSON}")
    print(f"  - {STATE_MD}")
    print(f"  - {AUDIT_JSON}")
    print(f"  - {DEFERRED_MD}")
    print(f"  - {RUNNING_MD}")
    print(f"  - {OVERRIDES_LOG}")
    print()
    print("Next: complete the Pre-Flight Checklist in SKILL.md, then begin Phase 0.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
check_gate.py <phase> - Validate the exit gate for a given phase.

Exit codes:
  0 - all gate checks passed
  1 - one or more checks failed
  2 - invalid usage or state file missing

Usage:
  python -m scripts.check_gate 0
  python -m scripts.check_gate 1
  etc.
"""

import json
import subprocess
import sys
from pathlib import Path

STATE_DIR = Path(".untangler")
STATE_JSON = STATE_DIR / "state.json"
AUDIT_JSON = STATE_DIR / "audit.json"


def load_state():
    if not STATE_JSON.exists():
        print(f"ERROR: {STATE_JSON} not found. Run init_state.py first.")
        sys.exit(2)
    return json.loads(STATE_JSON.read_text())


def load_audit():
    if not AUDIT_JSON.exists():
        return None
    return json.loads(AUDIT_JSON.read_text())


def git_diff_empty():
    """True if there are no uncommitted changes."""
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() == ""


def git_branch():
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def git_tag_exists(tag):
    result = subprocess.run(["git", "tag", "-l", tag], capture_output=True, text=True)
    return result.stdout.strip() == tag


def check_phase_0(state):
    checks = []
    checks.append(("App run command documented", (STATE_DIR / "RUNNING.md").exists() and
                   len((STATE_DIR / "RUNNING.md").read_text().strip()) > 100))
    checks.append(("Baseline LOC captured", state["baseline"]["total_loc"] is not None))
    checks.append(("Baseline test count captured", state["baseline"]["test_count"] is not None))
    checks.append(("Stack detected", len(state["stack"]) > 0))
    checks.append(("Baseline git tag exists", git_tag_exists(state["baseline"]["git_tag"])))
    branch = git_branch()
    checks.append(("On a refactor branch", branch is not None and branch.startswith("refactor/")))
    return checks


def check_phase_1(state):
    audit = load_audit()
    checks = []
    checks.append(("REFACTOR_AUDIT.md exists", Path("REFACTOR_AUDIT.md").exists()))
    checks.append(("REFACTOR_AUDIT.md has substance (>100 lines)",
                   Path("REFACTOR_AUDIT.md").exists() and
                   len(Path("REFACTOR_AUDIT.md").read_text().splitlines()) > 100))
    checks.append(("audit.json has >= 5 issues", audit is not None and len(audit.get("issues", [])) >= 5))
    checks.append(("Top 5 selected in audit.json", audit is not None and len(audit.get("top_5", [])) == 5))
    checks.append(("Top 5 signed off by user", state.get("top_5_signed_off_at") is not None))

    # Verify no code changes happened during audit phase
    # (only state files and audit doc should have changed)
    result = subprocess.run(
        ["git", "diff", "--name-only", state["baseline"]["git_tag"]],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        changed = [f for f in result.stdout.strip().split("\n") if f]
        allowed_prefixes = (".untangler/", "REFACTOR_AUDIT.md")
        code_changes = [f for f in changed if not f.startswith(allowed_prefixes) and f]
        checks.append((f"No code changes during audit (got {len(code_changes)} unexpected)",
                       len(code_changes) == 0))
    return checks


def check_phase_2(state):
    audit = load_audit()
    checks = []
    if audit is None or not audit.get("top_5"):
        checks.append(("audit.json with Top 5 exists", False))
        return checks

    for issue_id in audit["top_5"]:
        issue = next((i for i in audit["issues"] if i["id"] == issue_id), None)
        if not issue:
            checks.append((f"Issue {issue_id} found in issues list", False))
            continue
        safety = issue.get("safety_net", {})
        checks.append((f"Issue {issue_id} has safety net plan", "type" in safety))
        checks.append((f"Issue {issue_id} safety net verified", safety.get("status") == "verified"))

    checks.append(("At least one safety net deliberately broken-then-fixed",
                   any(i.get("safety_net", {}).get("broken_then_fixed") for i in audit["issues"]
                       if i["id"] in audit["top_5"])))
    return checks


def check_phase_3(state):
    audit = load_audit()
    checks = []
    if audit is None or not audit.get("top_5"):
        checks.append(("audit.json with Top 5 exists", False))
        return checks

    for issue_id in audit["top_5"]:
        issue = next((i for i in audit["issues"] if i["id"] == issue_id), None)
        if not issue:
            continue
        checks.append((f"Issue {issue_id} marked done", issue.get("status") == "done"))

    # Tests must pass (we record the result of the last test run in state.json)
    last_test = state.get("last_test_run", {})
    checks.append(("Last test run passing", last_test.get("passing") is True))
    checks.append(("Git working tree clean", git_diff_empty()))
    return checks


def check_phase_4(state):
    checks = []
    checks.append(("ARCHITECTURE.md exists", Path("ARCHITECTURE.md").exists()))
    # Look for lint/boundary config - this varies by stack so check for common indicators
    boundary_indicators = [
        Path(".eslintrc.json"), Path(".eslintrc.js"), Path("eslint.config.js"),
        Path(".importlinter"), Path("pyproject.toml"),
    ]
    has_lint_config = any(p.exists() for p in boundary_indicators)
    checks.append(("Lint config present", has_lint_config))

    hook_indicators = [Path(".husky"), Path(".pre-commit-config.yaml"), Path(".git/hooks/pre-commit")]
    checks.append(("Pre-commit hooks configured", any(p.exists() for p in hook_indicators)))

    claude_md = Path("CLAUDE.md")
    checks.append(("CLAUDE.md has guard rails section",
                   claude_md.exists() and "Codebase Conventions" in claude_md.read_text()))
    return checks


def check_phase_5(state):
    checks = []
    checks.append(("HANDOVER.md exists", (STATE_DIR / "HANDOVER.md").exists()))
    # Check tag exists
    result = subprocess.run(["git", "tag", "-l", "refactor-complete-*"], capture_output=True, text=True)
    checks.append(("refactor-complete tag set", bool(result.stdout.strip())))
    return checks


PHASE_CHECKERS = {
    0: check_phase_0,
    1: check_phase_1,
    2: check_phase_2,
    3: check_phase_3,
    4: check_phase_4,
    5: check_phase_5,
}


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.check_gate <phase>")
        sys.exit(2)
    try:
        phase = int(sys.argv[1])
    except ValueError:
        print("Phase must be an integer 0-5")
        sys.exit(2)
    if phase not in PHASE_CHECKERS:
        print(f"Unknown phase: {phase}")
        sys.exit(2)

    state = load_state()
    checks = PHASE_CHECKERS[phase](state)

    print(f"\nGate check for Phase {phase} ({state['phases'][str(phase)]['name']}):\n")
    passed = 0
    failed_items = []
    for name, ok in checks:
        marker = "[PASS]" if ok else "[FAIL]"
        print(f"  {marker} {name}")
        if ok:
            passed += 1
        else:
            failed_items.append(name)

    print(f"\n{passed}/{len(checks)} checks passed.\n")

    if failed_items:
        print("Failed items:")
        for f in failed_items:
            print(f"  - {f}")
        print()
        print("To override (use the magic phrase):")
        print('  "I understand the risk, override gate."')
        print()
        sys.exit(1)

    print(f"Phase {phase} gate PASSED. You may proceed to Phase {phase + 1}." if phase < 5
          else "Phase 5 complete. Refactor handover done.")
    sys.exit(0)


if __name__ == "__main__":
    main()

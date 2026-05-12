# State Schema

Reference for `.untangler/state.json` and `.untangler/audit.json` structures.

---

## state.json

The source of truth for workflow progress. Machine-readable. Updated by `update_state.py`.

```json
{
  "schema_version": 1,
  "started_at": "2026-05-12T00:00:00Z",
  "current_phase": 0,
  "phases": {
    "0": {
      "name": "Triage",
      "status": "in_progress",
      "gates": {},
      "started_at": "2026-05-12T00:00:00Z",
      "completed_at": null
    }
  },
  "baseline": {
    "git_tag": "pre-refactor-baseline",
    "branch": "refactor/untangle-2026-05-12",
    "total_loc": 12450,
    "file_count": 187,
    "test_count": 23,
    "tests_passing": 21,
    "tests_failing": 2
  },
  "stack": ["nextjs", "supabase"],
  "top_5_signed_off_at": null,
  "overrides": [
    {
      "timestamp": "2026-05-13T10:00:00Z",
      "phase": "2",
      "gate": "deliberate-break-test",
      "reason": "Time-boxed engagement; user accepts risk."
    }
  ],
  "last_test_run": {
    "timestamp": "2026-05-13T11:00:00Z",
    "passing": true,
    "passing_count": 23,
    "failing_count": 0
  }
}
```

### Field meanings

| Field | Type | Purpose |
|-------|------|---------|
| `schema_version` | int | Version of this schema. Bump on breaking changes. |
| `started_at` | ISO timestamp | When the engagement began |
| `current_phase` | int 0-5 | Current phase Claude is working on |
| `phases.<N>.status` | enum | `pending` / `in_progress` / `done` |
| `phases.<N>.gates` | object | Optional gate check result cache |
| `baseline.git_tag` | string | Tag to diff against for "have we changed code" checks |
| `baseline.branch` | string | The refactor branch name |
| `stack` | array of string | Detected stacks (used to load reference files) |
| `top_5_signed_off_at` | ISO timestamp or null | When user confirmed the Top 5 |
| `overrides` | array | Every gate override, with reason |
| `last_test_run` | object | Latest test execution status |

---

## audit.json

The structured catalogue of issues found in Phase 1. Each issue tracked through to Phase 3.

```json
{
  "schema_version": 1,
  "issues": [
    {
      "id": "I-001",
      "title": "Auth check duplicated across 3 routes",
      "severity": "high",
      "category": "duplication",
      "files": [
        "routes/orders.js:23",
        "routes/users.js:45",
        "routes/admin.js:12"
      ],
      "description": "Same user authorisation logic exists in three handlers with subtle variations.",
      "status": "pending",
      "safety_net": {
        "type": "integration_test",
        "location": "tests/auth.integration.test.js",
        "status": "verified",
        "broken_then_fixed": true
      },
      "refactor_plan": "Extract to services/auth.requireUser(); migrate routes one at a time.",
      "commits": []
    }
  ],
  "top_5": ["I-001", "I-002", "I-003", "I-004", "I-005"],
  "deferred": ["I-006", "I-007", "I-008"]
}
```

### Issue fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | string | Stable identifier (I-001, I-002, ...) |
| `severity` | enum | `low` / `medium` / `high` / `critical` |
| `category` | enum | `duplication` / `boundary` / `dead_code` / `complexity` / `dependency` / `risk` |
| `files` | array | File:line references (real, not approximate) |
| `status` | enum | `pending` / `in_progress` / `done` / `deferred` |
| `safety_net.type` | enum | `e2e` / `integration_test` / `unit_test` / `snapshot` / `smoke_script` / `manual_checklist` |
| `safety_net.status` | enum | `planned` / `implemented` / `verified` |
| `safety_net.broken_then_fixed` | bool | Has the safety net been deliberately broken to prove it detects regressions? |
| `commits` | array of SHA | Commits implementing this fix |

### Severity definitions

- **critical** - data loss, money handling, security risk
- **high** - blocks safe refactor of adjacent code, major duplication, broken boundary
- **medium** - smells, naming, mid-size files
- **low** - taste, micro-cleanups

Top 5 should always include the critical and high items first. If there are more than 5
high items, surface that to the user - this codebase may need multiple refactor cycles.

# REFACTOR_AUDIT.md Template

Use this structure for Phase 1. Save to repo root. No code changes during Phase 1.

The structured equivalent in `.untangler/audit.json` is the source of truth; this Markdown
file is a human-readable mirror.

---

```markdown
# Refactor Audit - <project-name>

**Date**: YYYY-MM-DD
**Auditor**: Claude Code (codebase-untangler skill)
**Baseline commit**: <git sha>
**Stack**: <e.g. Next.js + Supabase>

## 1. App Summary

One paragraph: what the app does, who uses it, what stack, hosting environment.

## 2. Entry Points

| Type | Path / Trigger | Handler | Notes |
|------|----------------|---------|-------|
| HTTP route | POST /api/orders | app/api/orders/route.ts | |
| Scheduled | cron daily 03:00 | supabase/functions/cleanup | |
| Webhook | Stripe events | app/api/webhooks/stripe | |
| CLI | npm run migrate | scripts/migrate.ts | |

## 3. Module Map

| Path | LOC | Purpose | Concerns mixed? |
|------|-----|---------|-----------------|
| /app | 2100 | Next.js routes + UI | Yes - DB queries inline |
| /lib | 800 | Helpers | Yes - 5 unrelated concerns |
| /components | 1500 | React components | Some contain business logic |

## 4. Hotspots

### Large files (>500 LOC)
- `app/dashboard/page.tsx` - 1247 lines
- `lib/helpers.ts` - 890 lines

### High-churn (from `git log` shortstat)
- `lib/helpers.ts` - 89 commits
- `app/api/route.ts` - 67 commits

Run `python -m scripts.audit_helpers hotspots` to generate this.

## 5. Duplication Catalogue (issues I-001 to I-00N)

| ID | What | Locations | Canonical home |
|----|------|-----------|----------------|
| I-001 | User auth check | routes/orders:23, routes/users:45, routes/admin:12 | services/auth.ts |
| I-002 | Date formatting | lib/helpers:120, components/Header:30, utils/format:8 | lib/format.ts |
| I-003 | API error handler | 6 places, all slightly different | middleware/errors.ts |

## 6. Boundary Violations

- `components/Dashboard.tsx` imports directly from `/lib/db` (UI -> data layer)
- `lib/helpers.ts` mixes DB queries, HTTP calls, formatting
- `app/api/route.ts` contains business logic that belongs in a service

## 7. Dead Code Candidates

Verify each before deletion (grep for dynamic imports, check git blame).

- `lib/legacy-payments.ts` - 0 imports
- `utils/v1-formatter.ts` - 0 imports, comment says "replaced by v2"

## 8. Dependency Issues

### Unused
- `lodash` - only `_.get` used once; remove
- `moment` - replaced by date-fns

### Redundant
- Both `axios` and `node-fetch` in use - pick one

### Version concerns
- React 17 with components written for 18 patterns

## 9. Risk Register

| File | Concern | Risk if changed |
|------|---------|-----------------|
| `lib/billing.ts` | Nested, no tests, handles money | Customer charged wrong |
| `app/api/webhooks/route.ts` | No retry, swallows errors | Silent data loss |
| `services/sync.ts` | Mutable module-level state | Race conditions worsen |

## 10. Test Coverage

- Unit: 12 files, last run 87/93 passing
- Integration: none
- E2E: none
- Estimated coverage: ~15%

## 11. TOP 5 PRIORITIES

In order. These are what Phase 3 fixes.

1. **[I-XXX] Establish baseline tests for the checkout flow** - revenue path, no tests.
   Blocks everything else. Phase 2 work.
2. **[I-001] Extract auth logic** - duplicated 3x, blocks safe changes there
3. **[I-XXX] Split `lib/helpers.ts`** - 890 lines of mixed concerns
4. **[I-XXX] Pick one HTTP client** - migrate to `axios` (or `fetch` - user choice)
5. **[I-XXX] Add boundary lint rule** - prevent UI -> DB imports

Issues 6+ deferred to a later pass.

## 12. Out of Scope

- Framework upgrades
- Performance optimisation
- New feature work
- Visual/UX changes

## 13. Sign-off

User confirmed Top 5 on: __________ (timestamp recorded in state.json)
```

---

## Tips

- Real numbers, not "big": "1247 lines" is auditable.
- Every reference is file:line - the user can verify each one.
- Top 5 is the contract. Get explicit sign-off before any code changes.
- Commit the audit as its own commit - that's the contract for the work.

# CLAUDE.md Guard Rails

Append this section to the project's `CLAUDE.md` after Phase 4 so future AI-assisted work
doesn't re-tangle the codebase.

---

```markdown
## Codebase Conventions (do not break these)

This project has been through a structural refactor. Future changes must respect these
conventions. If you cannot follow them for a specific task, stop and ask the user before
proceeding.

### Architecture

Layer rules (see `ARCHITECTURE.md` for the diagram):

- UI components never import from `/db`, `/lib/clients/*`, or `/services/*/internal`
- Route handlers contain no business logic - they call services
- Services never import from route or UI layers
- Shared utilities live in `/lib`; nothing in `/lib` imports from app code

One canonical way per concern (these were chosen during the cleanup):

- HTTP calls: `<chosen client>` only
- Date handling: `<chosen library>` only
- Auth checks: `services/auth.requireUser()` only
- Errors: throw `AppError` subclasses, handled by `middleware/errors`

File size discipline:

- Hard cap 500 lines; if approaching, split before adding more
- Functions ideally <50 lines

### Before adding code

- Search the codebase for existing implementations. Do not create a fourth way to do
  something that already has three. Use the canonical version.
- If the canonical version doesn't fit, extend it - do not fork it.
- New modules require a one-line purpose comment at the top.

### Before creating a new file

- Could this go in an existing module under 300 lines? Prefer that over a new file.
- Can you state the file's purpose in one sentence? If not, redesign first.

### Refactor + feature rule

- Never combine refactor and feature in the same commit
- If a refactor is needed to enable a feature, do the refactor in a separate commit first,
  verify tests pass, commit, then add the feature

### Tests

- New business logic requires a test before merging
- Bug fixes require a regression test (one that would have caught the bug)
- Never disable a failing test to make CI pass

### When tempted to rewrite

- Don't. Refactor incrementally. Use the `codebase-untangler` skill if needed.
- If you genuinely believe a rewrite is needed, write a proposal and get user sign-off first.

### Anti-patterns that triggered the last cleanup

These specific patterns caused the previous tangle. Watch for them:

- Copy-pasting a route handler and editing one variable
- Adding "just one more" helper to `lib/helpers`
- Inlining business logic in JSX/templates because "it's quick"
- Catching errors and swallowing them silently
- Using `any` / `// @ts-ignore` to make types compile
- Storing config in code instead of env / config files

If you find yourself doing any of these, stop and find the right pattern.
```

---

## Customisation

When applying this template, edit:

- The "chosen client/library" lines to reflect actual Phase 3 decisions
- The "Anti-patterns that triggered the last cleanup" list to match what the audit found
- The layer rules to match the actual `ARCHITECTURE.md`

Keep it short. Long CLAUDE.md files get ignored. Enforceable rules > best-practice essays.

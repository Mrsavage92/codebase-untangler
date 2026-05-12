# codebase-untangler

> A stateful Claude Code skill for safely refactoring tangled, multi-agent-built codebases without breaking working features.

## Why this exists

I've been building SaaS for a few months using a mix of Claude, Codex, Cursor, Copilot, and Lovable. The problem: they don't communicate. Each one picks up the codebase, makes its own assumptions about structure, and adds its own conventions.

What started clean has slowly tangled. Different patterns for the same problem. Duplicate utilities. Files that grew because the next agent didn't know there was already a home for that logic.

This skill is the fix.

## What it does

A stateful, gated 6-phase workflow:

1. **Triage** - get it running, tag a baseline, detect the stack
2. **Audit** - written report with hotspots, duplication, boundary violations, Top 5 priorities you sign off on
3. **Safety net** - build the tests for the behaviours you're about to refactor near
4. **Refactor** - one issue at a time, small commits, verified after each change
5. **Hardening** - lint rules, pre-commit hooks, architecture doc, guard rails in CLAUDE.md
6. **Handover** - summary, deferred items, recommended cadence

## What makes it different

- **State persists** in `.untangler/state.json`. Pick it up next week and Claude reads the state and resumes exactly where you left off.
- **Gates are enforced by scripts** that exit 1 if checks fail. Not vibes.
- **Override requires a specific phrase**: `"I understand the risk, override gate."` Paraphrases don't count. Every override is logged.
- **Anti-drift baked in.** When Claude thinks "while I'm in here..." it has to write the item to `deferred.md` and continue with the current task.
- **Stack-aware.** Next.js, Supabase, Python/FastAPI, Node/Express, React Native each get their own reference file with patterns specific to that stack.

## Prime directive

**No change ships without a way to prove it didn't break anything.**

Every feature that works today must still work after every change. Behaviour first. Beauty later. Never rewrite.

## Install

1. Download [`codebase-untangler.skill`](./codebase-untangler.skill)
2. Drop it in your Claude Code skills directory
3. Trigger it by mentioning a messy codebase, vibe-coded project, or asking to refactor without breaking things

## What's in the bundle

- `SKILL.md` - the workflow itself
- `scripts/` - four Python scripts that enforce gates and manage state
- `references/` - audit template, refactor patterns, CLAUDE.md guard rails, state schema
- `references/stacks/` - stack-specific patterns for Next.js, Supabase, Python/FastAPI, Node/Express, React Native

## License

MIT. Use it, fork it, ship it.

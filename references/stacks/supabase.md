# Stack Reference: Supabase

Patterns and gotchas for Supabase projects (Postgres + Auth + Storage + Edge Functions + RLS).

---

## Detection

- `@supabase/supabase-js` in `package.json`
- `supabase/` directory with `config.toml` and `migrations/`
- `.env` with `NEXT_PUBLIC_SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`

---

## Canonical layout

```
supabase/
  config.toml
  migrations/         # numbered SQL files
  functions/          # edge functions
  seed.sql
lib/
  supabase/
    client.ts         # browser/anon client
    server.ts         # server client with session cookies
    admin.ts          # service role client (server-only!)
    types.ts          # generated types from `supabase gen types`
    queries/          # typed queries
```

---

## Common vibe-code symptoms

### 1. Service role key used in client code

**Symptom**: `SUPABASE_SERVICE_ROLE_KEY` (or anon key with admin privileges) exposed to the
browser bundle.

**Critical security issue** - flag as severity `critical` in audit. Fix immediately,
rotate the key.

**Fix**: service role only in server contexts (route handlers, server components, edge
functions). Browser uses anon key. Use Supabase SSR helpers for session-aware queries.

### 2. RLS disabled "to make it work"

**Symptom**: tables have `enable row level security = false` or no policies.

**Fix**: re-enable RLS table by table, write policies, test each one. This is Phase 2/3 work
with careful testing - getting RLS wrong leaks data.

### 3. Types not generated, stringly-typed queries

**Symptom**: no `Database` type, queries return `any`.

**Fix**: `supabase gen types typescript --linked > lib/supabase/types.ts`. Wire into client
creation: `createClient<Database>(...)`.

### 4. Auth checks duplicated

**Symptom**: every server component calls `supabase.auth.getUser()` differently.

**Fix**: one `getCurrentUser()` helper in `lib/auth.ts` that wraps it.

### 5. N+1 queries everywhere

**Symptom**: page fetches a list, then loops fetching related data per row.

**Fix**: use Postgres joins via Supabase's nested selects:
```ts
supabase.from('orders').select('*, customer:customers(*), items:order_items(*)')
```

### 6. Edge functions duplicating server logic

**Symptom**: same business logic in `supabase/functions/` and `app/api/`.

**Fix**: pick the right home. Edge functions for: webhooks from external services, scheduled
jobs, cross-region low-latency reads. Route handlers for: auth-aware app logic.

### 7. Migrations not in version control or not idempotent

**Symptom**: `migrations/` empty but schema is complex; or migrations have hand edits.

**Fix**: dump current schema with `supabase db diff`, capture as a baseline migration,
commit. All future changes through migrations.

---

## Safety net patterns

- **RLS policy tests**: write SQL-level tests using `supabase test db` or pgTAP
- **API integration tests**: test against a local Supabase instance (`supabase start`)
- **Webhook tests**: replay captured payloads against edge functions locally

---

## Tooling

- `supabase db lint` - SQL linting
- `supabase db diff` - what's changed in the schema
- `supabase gen types typescript --linked` - regenerate types
- `pg_dump` for emergency schema backups before refactor

---

## Phase 4 guard rails

Add to CLAUDE.md guard rails:

```
- Supabase service role key is server-only. Never import from client components.
- All tables have RLS enabled. Adding a table requires policies in the same migration.
- All queries use generated `Database` types - no `any`.
- Schema changes go through migrations only - no Supabase dashboard edits in prod.
```

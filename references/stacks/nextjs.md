# Stack Reference: Next.js (App Router)

Patterns, conventions, and tooling for Next.js codebases (13+ App Router). Most vibe-coded
projects use this stack.

---

## Detection

Look for:
- `next` in `package.json` dependencies
- `app/` directory with `layout.tsx` and `page.tsx`
- `next.config.js` / `next.config.mjs`

If `pages/` exists alongside `app/`, project is mid-migration - flag in audit.

---

## Canonical layout

```
app/
  (marketing)/        # route group, no URL impact
  (app)/              # authenticated routes
  api/
    <resource>/route.ts
  layout.tsx
  page.tsx
components/
  ui/                 # presentational, no logic, no data fetching
  features/           # feature-specific composite components
lib/
  db/                 # database client + queries
  clients/            # external API clients (Stripe, Resend, etc)
  validators/         # zod schemas
  utils/              # pure utility functions
services/             # business logic, called by route handlers
types/
hooks/                # client-only React hooks
```

---

## Common vibe-code symptoms

### 1. Business logic in route handlers

**Symptom**: `app/api/orders/route.ts` has 200+ lines of Stripe calls, DB writes, and email
sending all inline.

**Fix**: extract to `services/orders/createOrder.ts`. Route becomes a thin handler.

### 2. Server/client component confusion

**Symptom**: `'use client'` everywhere, including pages that don't need it. Or no
`'use client'` at all and runtime errors about useState.

**Fix**: default is server. Add `'use client'` only when you genuinely need browser APIs,
state, or effects. Move data fetching up to server components.

### 3. `getServerSession` called 5 different ways

**Symptom**: every route handler calls auth differently.

**Fix**: one `requireUser()` helper in `lib/auth.ts`, used everywhere.

### 4. Duplicate fetching logic across pages

**Symptom**: each page has its own `fetchSomething()`.

**Fix**: queries live in `lib/db/queries/<resource>.ts`. Pages import them.

### 5. UI components importing from `/lib/db`

**Symptom**: `components/ProductCard.tsx` has `import { db } from '@/lib/db'`.

**Fix**: components receive data via props. Server components fetch and pass down.

### 6. `app/` and `pages/` both present

Mid-migration state. Plan it as a strangler-fig phase: pick routes one at a time, migrate
to `app/`, delete the `pages/` version.

---

## Lint rules (Phase 4)

`eslint.config.js`:

```js
import boundaries from 'eslint-plugin-boundaries';

export default [
  {
    plugins: { boundaries },
    settings: {
      'boundaries/elements': [
        { type: 'app', pattern: 'app/**' },
        { type: 'components', pattern: 'components/**' },
        { type: 'services', pattern: 'services/**' },
        { type: 'lib', pattern: 'lib/**' },
      ],
    },
    rules: {
      'boundaries/element-types': ['error', {
        default: 'disallow',
        rules: [
          { from: 'app', allow: ['services', 'lib', 'components'] },
          { from: 'components', allow: ['lib', 'components'] },
          { from: 'services', allow: ['lib', 'services'] },
          { from: 'lib', allow: ['lib'] },
        ],
      }],
    },
  },
];
```

`@next/eslint-plugin-next` for Next-specific rules. `eslint-plugin-react-server-components`
to catch client/server boundary mistakes.

---

## Safety net patterns

- **E2E**: Playwright with `next dev` running. Test the critical revenue paths.
- **Route integration tests**: Use `next-test-api-route-handler` to test `app/api/*` routes
  without spinning up the server.
- **Component tests**: Vitest + React Testing Library for client components only.
- **Server component tests**: harder; usually covered by E2E instead.

---

## Tooling

- `next build` - catches most type/import errors
- `next lint` - configurable eslint runner
- `madge --circular --extensions ts,tsx app/ components/ lib/` - find circular deps
- `npx knip` - find unused exports, files, dependencies (excellent for vibe-coded projects)
- `npx ts-prune` - find unused TypeScript exports
- `npx depcheck` - find unused dependencies

Run `knip` early in Phase 1 - it surfaces a lot.

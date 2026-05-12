# Stack Reference: Node / Express

Patterns for Node.js Express applications. Apply also to Fastify, Koa, NestJS-without-DI
with minor adjustments.

---

## Detection

- `express` (or `fastify`, `koa`) in `package.json`
- An `app.js` / `server.js` / `index.js` with `app.listen(...)`

---

## Canonical layout

```
src/
  routes/             # Express routers, one per resource
    orders.js
  controllers/        # request/response handling, thin
  services/           # business logic
  repositories/       # data access
  middleware/         # auth, errors, logging
  lib/
    clients/          # external API clients
    validators/       # joi / zod / yup schemas
    utils/
  config/
    index.js          # env -> typed config
  app.js              # builds the app
  server.js           # listens on port
tests/
```

---

## Common vibe-code symptoms

### 1. Everything in one file

**Symptom**: 1500-line `index.js` with routes, DB, helpers, middleware all together.

**Fix**: split-file refactor (see refactor-patterns.md #4). Don't try to do it all at once;
extract one router at a time.

### 2. Routes contain database queries

**Symptom**: `app.get('/users/:id', async (req, res) => { const user = await db.query(...) })`.

**Fix**: extract to `repositories/users.js`. Route calls repo.

### 3. Mixed error handling

**Symptom**: some routes throw, some return `{ error }`, some `res.status(500).send()`.

**Fix**: one `AppError` class hierarchy + one error middleware. All routes use the same
pattern. Async errors caught with `express-async-errors` or wrapper.

### 4. Validation scattered

**Symptom**: ad-hoc `if (!req.body.email) return res.status(400)...` everywhere.

**Fix**: zod/joi schema per route, validation in middleware.

### 5. Multiple HTTP clients

**Symptom**: `axios`, `node-fetch`, native `fetch`, and `got` all in package.json.

**Fix**: pick one. Migrate one call site at a time. Remove the rest.

### 6. Mutable singletons

**Symptom**: `let currentUser; module.exports = { setUser, getUser };`.

**Fix**: stateless modules. State lives in request context (`res.locals` or a context
library like `cls-hooked`).

### 7. No layering between web framework and business logic

**Symptom**: services take `req` and `res` as parameters.

**Fix**: services take plain data, return plain data. Controllers translate between HTTP
and service signatures.

---

## Lint rules (Phase 4)

`.eslintrc.json`:

```json
{
  "extends": ["eslint:recommended"],
  "plugins": ["import", "boundaries"],
  "settings": {
    "boundaries/elements": [
      { "type": "routes", "pattern": "src/routes/**" },
      { "type": "controllers", "pattern": "src/controllers/**" },
      { "type": "services", "pattern": "src/services/**" },
      { "type": "repositories", "pattern": "src/repositories/**" },
      { "type": "lib", "pattern": "src/lib/**" }
    ]
  },
  "rules": {
    "boundaries/element-types": ["error", {
      "default": "disallow",
      "rules": [
        { "from": "routes", "allow": ["controllers", "middleware"] },
        { "from": "controllers", "allow": ["services", "lib", "validators"] },
        { "from": "services", "allow": ["repositories", "lib", "services"] },
        { "from": "repositories", "allow": ["lib"] }
      ]
    }]
  }
}
```

---

## Safety net patterns

- **Route tests**: `supertest` against the app (no real port binding)
- **Service tests**: plain unit tests, mock repositories
- **Repository tests**: against a real test DB (transactions roll back) or `testcontainers`

---

## Tooling

- `eslint` with the above rules
- `madge --circular src/` - circular deps
- `knip` - unused code/files/deps (excellent for Node projects too)
- `npm audit` - security
- `npm-check-updates` - dependency freshness
- `clinic.js` (later) - performance, not for Phase 3

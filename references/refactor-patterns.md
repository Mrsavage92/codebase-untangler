# Refactor Patterns

Safe, behaviour-preserving refactoring patterns. Apply one at a time. Verify after each.
Commit. No exceptions.

---

## 1. Extract Function

**When**: A block of inline code has a single purpose.

**Before**:
```js
app.post('/orders', async (req, res) => {
  const user = await db.users.findOne({ id: req.session.userId });
  if (!user) return res.status(401).send('Not logged in');
  if (user.status !== 'active') return res.status(403).send('Account suspended');
  if (user.credits < req.body.total) return res.status(402).send('Insufficient credits');
  const order = await db.orders.create({ userId: user.id, ...req.body });
  res.json(order);
});
```

**After**:
```js
async function authoriseUserForOrder(session, total) {
  const user = await db.users.findOne({ id: session.userId });
  if (!user) return { ok: false, status: 401, message: 'Not logged in' };
  if (user.status !== 'active') return { ok: false, status: 403, message: 'Account suspended' };
  if (user.credits < total) return { ok: false, status: 402, message: 'Insufficient credits' };
  return { ok: true, user };
}

app.post('/orders', async (req, res) => {
  const auth = await authoriseUserForOrder(req.session, req.body.total);
  if (!auth.ok) return res.status(auth.status).send(auth.message);
  const order = await db.orders.create({ userId: auth.user.id, ...req.body });
  res.json(order);
});
```

**Verification**: Same route tests pass. Function is now unit-testable.

---

## 2. Extract Module

**Steps**:
1. Identify the cohesive group
2. Create new file with identical signatures
3. Move functions; original file re-exports from new location (transitional)
4. Run tests
5. Update call sites to import from new module directly, one at a time
6. Remove transitional re-export
7. Run tests

The transitional re-export step lets you migrate call sites without breaking anything.

---

## 3. Replace Duplicated Code

Never dedupe all instances at once. Process:

1. Pick the cleanest existing implementation as canonical
2. Move it to shared location
3. Replace ONE duplicate with call to canonical
4. Test, commit
5. Repeat for next duplicate

If duplicates differ slightly, the canonical may need parameters. Add them as you go.

---

## 4. Split File

**When**: file >500 lines or mixes >2 concerns.

**Steps**:
1. Identify natural seams (groups of exports that belong together)
2. Create directory named after original (`auth.js` -> `auth/`)
3. Move groups into focused files (`auth/login.js`, `auth/tokens.js`)
4. Create `auth/index.js` re-exporting the public API of the original
5. Rest of codebase keeps importing from `auth` - no breakage
6. Optionally, later, update call sites to import from specific submodules

---

## 5. Rename for Clarity

**Always use IDE rename refactor**, never find-and-replace. IDE understands scope.

- TS/JS: VS Code F2 or TS language server rename
- Python: Pylance rename or `rope`

If renaming across languages, commit before and after each rename. Trivial revert.

---

## 6. Replace Magic Value

**Before**:
```js
if (user.role === 2) { /* ... */ }
setTimeout(retry, 3600000);
```

**After**:
```js
const ROLE_ADMIN = 2;
const ONE_HOUR_MS = 60 * 60 * 1000;

if (user.role === ROLE_ADMIN) { /* ... */ }
setTimeout(retry, ONE_HOUR_MS);
```

Better: enums/const objects for related sets.

---

## 7. Introduce Parameter Object

**When**: function takes 4+ args, or args always passed together.

**Before**:
```js
function createOrder(userId, productId, quantity, currency, couponCode, shippingAddress) { ... }
```

**After**:
```js
function createOrder({ userId, productId, quantity, currency, couponCode, shippingAddress }) { ... }
```

Self-documenting call sites, order-independent.

---

## 8. Move File

`git mv` preserves history. IDE updates imports automatically. One file per commit.

---

## 9. Strangler Fig

**When**: you need to replace a whole subsystem but can't do it in one go.

1. Build new module alongside old
2. Route ONE call site to new module
3. Verify
4. Route next call site
5. Repeat until no callers of old module
6. Delete old module

Use this when a subsystem genuinely needs to be rewritten but you can't stop shipping.

---

## 10. Introduce Seam (for legacy untested code)

**When**: you need to refactor code that has no tests and can't easily be tested as-is.

Working Effectively With Legacy Code (Feathers) defines a **seam**: a place where you can
alter behaviour without editing in place. Introduce one to enable testing:

- Extract function -> mock the function
- Extract dependency to parameter -> inject a fake
- Wrap a class behind an interface -> swap implementations

Then write the characterisation test against the seam, THEN refactor behind it.

---

## Anti-patterns

- **Refactor + feature same commit** - never. Pure restructuring only.
- **"While I'm in here..."** - the most dangerous phrase. Note in `deferred.md`, do later.
- **Refactoring untested code without tests** - go write the characterisation test first.
- **Multi-module PRs** - keep each commit focused on one slice.
- **Rewriting "for clarity"** - if behaviour might change, it's not a refactor.

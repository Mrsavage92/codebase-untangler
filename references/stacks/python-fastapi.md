# Stack Reference: Python / FastAPI

Patterns for Python codebases, particularly FastAPI applications.

---

## Detection

- `fastapi` in `pyproject.toml` / `requirements.txt`
- `main.py` or `app/main.py` with `FastAPI()` instance
- `uvicorn` as the runner

---

## Canonical layout

```
app/
  api/
    v1/
      routes/         # FastAPI routers, one per resource
      dependencies.py # shared dependencies (auth, db session)
  core/
    config.py         # settings via pydantic
    security.py       # auth helpers
  db/
    base.py           # SQLAlchemy base
    session.py        # session factory
    models/           # ORM models, one per file
  schemas/            # Pydantic request/response models
  services/           # business logic
  workers/            # Celery / arq tasks
tests/
  conftest.py
  api/
  services/
```

---

## Common vibe-code symptoms

### 1. Business logic in route handlers

**Symptom**: 100-line route function doing DB queries, external API calls, email sending.

**Fix**: route is a thin layer - parse input (Pydantic), call service, return response.
Move logic to `app/services/<resource>.py`.

### 2. Pydantic models, SQLAlchemy models, dicts all flowing through the same code

**Symptom**: function signatures with `dict` types; `.dict()` and `.model_dump()` calls
sprinkled everywhere.

**Fix**: typed boundaries. Pydantic for I/O. SQLAlchemy for DB. Convert at the edges,
not in the middle.

### 3. Global state / singletons

**Symptom**: `db = SessionLocal()` at module level; mutable module globals.

**Fix**: use FastAPI's dependency injection. `db: Session = Depends(get_db)`. Same for
config, clients, auth.

### 4. No async / mixed sync and async

**Symptom**: async route handlers calling sync DB code, blocking the event loop.

**Fix**: pick a lane. SQLAlchemy 2.0 supports async; or use sync routes consistently with
proper worker count.

### 5. Settings scattered across files

**Symptom**: `os.environ.get(...)` called from multiple files.

**Fix**: one `Settings(BaseSettings)` class in `app/core/config.py`. Inject via dependency.

### 6. Tests use real database

**Symptom**: tests slow, flaky, leak state.

**Fix**: pytest fixtures using transactions that roll back. Or `sqlite::memory:` for tests
if the schema is simple enough.

---

## Lint rules (Phase 4)

`pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "B", "UP", "N", "TID", "RUF"]

[tool.ruff.isort]
known-first-party = ["app"]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[tool.importlinter]
root_packages = ["app"]

[[tool.importlinter.contracts]]
name = "Routes don't import from services internals"
type = "forbidden"
source_modules = ["app.api"]
forbidden_modules = ["app.services.*.internal"]

[[tool.importlinter.contracts]]
name = "Services don't import from API layer"
type = "forbidden"
source_modules = ["app.services"]
forbidden_modules = ["app.api"]
```

---

## Safety net patterns

- **Route tests**: `httpx.AsyncClient` against the app, no real network
- **Service tests**: pure functions or fakes for dependencies
- **DB integration**: pytest fixtures with transactional rollback
- **Migration tests**: `alembic upgrade head` then `alembic downgrade base` cleanly

---

## Tooling

- `ruff` - lint, format, replace flake8/black/isort
- `mypy --strict` - type check
- `import-linter` - enforce layer boundaries
- `vulture` - find dead code
- `pip-audit` - dependency vulnerabilities
- `pip list --outdated` - dependency drift

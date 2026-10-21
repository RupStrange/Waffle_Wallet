# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Waffle Wallet is a lightweight personal expense tracker built with FastAPI, SQLAlchemy 2.0 and PostgreSQL.

---

## Architecture
```
expense-tracker/
├── main.py             # App factory — mounts static, registers routers, url_for shim; delegates error handling to errors package
├── dependencies.py     # Shared Jinja2Templates singleton, get_db(), get_current_user()
├── database/
│   ├── database.py     # engine, SessionLocal, Base (DeclarativeBase)
│   └── db.py           # init_db(), seed_db(), shared pwd_context
├── core/
│   └── config.py       # Settings class backed by env vars, accessed via get_settings()
├── routers/
│   ├── pages.py        # GET routes that render Jinja2 templates + POST /register
│   ├── auth.py         # POST /login, GET /logout
│   ├── profile.py      # Dashboard / account / preferences pages
│   ├── expenses.py     # Expense CRUD routes (stubs; students implement Steps 7–9)
│   └── api_expenses.py # GET /api/expenses — JSON endpoint, requires auth
├── models/             # SQLAlchemy models: user.py (User), expense.py (Expense)
├── schemas/            # Pydantic schemas: user.py, expense.py
├── services/           # Business logic: authentication.py, registration.py
├── crud/               # DB query functions: users.py, expenses.py
├── errors/
│   ├── __init__.py     # exports register_exception_handlers(app), called from main.py
│   ├── exceptions.py   # custom exception types
│   └── handlers.py     # Exception handlers (JSON-aware for /api routes)
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this
│   └── *.html          # One template per page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles
│   │   └── landing.css     # Landing-page-only styles
│   └── js/
│       └── main.js         # Vanilla JS only
└── requirements.txt
```

**Where things belong:**
- New routes → new file under `routers/`, never inline in `main.py`
- DB queries → `crud/` only, never inline in route functions or services
- Engine/session/schema bootstrap → `database/`, never queries
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags
- Business logic → `services/`, not inside routers
- DB queries → `crud/`, not inside routers or services

---

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — call a service/crud, return a response
- DB queries: no raw SQL — use SQLAlchemy ORM expressions (`select()`, `.where()`). SQLAlchemy
  parameterises **values** automatically, but **never** interpolate column names, table names or
  sort direction into SQL text — map user input through a hardcoded allowlist dict instead
- Error handling: raise `HTTPException` for HTTP errors, not bare string returns

---

## Tech constraints

- **FastAPI only** — no Flask, no Django, no other web frameworks
- **PostgreSQL + SQLAlchemy** — psycopg3 driver (`psycopg[binary]`), synchronous ORM, `DeclarativeBase` style
- **No raw SQL** — use SQLAlchemy ORM and parameterised expressions only
- **Vanilla JS only** — no React, no jQuery, no npm packages
- **No new pip packages** — work within `requirements.txt` as-is unless explicitly told otherwise
- Python 3.10+ assumed — f-strings and `match` statements are fine

---

## Subagent policy

- Always use a built-in **Explore** subagent for codebase exploration before implementing any new feature
- Always use a subagent to verify test results after any implementation
- When asked to plan, delegate codebase research to a subagent before presenting the plan
- Always use a built-in **Plan** subagent in plan mode

---

## Commands
```bash
# Setup
python -m venv venv
.\venv\Scripts\activate           # Windows PowerShell
source venv/bin/activate          # macOS/Linux
pip install -r requirements.txt

# Run dev server (port 5001)
uvicorn main:app --reload --port 5001
# or
python main.py

# Database migrations (Alembic owns the schema -- never create_all())
#   1. edit the model  2. autogenerate  3. READ the generated file  4. apply
.\venv\Scripts\alembic.exe revision --autogenerate -m "what changed"
.\venv\Scripts\alembic.exe upgrade head
.\venv\Scripts\alembic.exe current          # which revision this DB is at
.\venv\Scripts\alembic.exe history          # the revision chain
.\venv\Scripts\alembic.exe check            # does the DB match the models?
.\venv\Scripts\alembic.exe downgrade -1     # undo the newest revision

# Run all tests
pytest

# Run a specific test file
pytest tests/test_foo.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s
```

---

## Testing

- `pytest==8.3.5` and `httpx==0.28.1` are already in `requirements.txt`
- No `tests/` directory exists yet — create it when adding the first test file
- **Never use `with TestClient(app)`** — the context manager fires the lifespan, which runs `seed_db()` against the real PostgreSQL database. Use `TestClient(app)` plainly (no `with`)

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `POST /register` | Implemented — in `routers/pages.py` |
| `GET /login` | Implemented — renders `login.html` |
| `POST /login` | Implemented — in `routers/auth.py` |
| `GET /terms` | Implemented — renders `terms.html` |
| `GET /privacy` | Implemented — renders `privacy.html` |
| `GET /logout` | Implemented — clears session, redirects to `/` |
| `GET /profile` | Implemented — renders `profile.html` (dashboard) — static placeholder data, no auth guard yet (known gap) |
| `GET /account` | Implemented — renders `account.html` — static placeholder data, no auth guard yet (known gap) |
| `GET /preferences` | Implemented — renders `preferences.html` — static placeholder data, no auth guard yet (known gap) |
| `GET /api/expenses` | Implemented — JSON; requires auth; accepts `ExpenseFilters` query params; returns `ExpenseListResponse` |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/{id}/edit` | Stub — Step 8 |
| `GET /expenses/{id}/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use plain string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `crud/` or `database/`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **Alembic owns the schema.** Revisions live in `alembic/versions/`. `alembic/env.py` reads the DB
  URL from `get_settings()` — never from the committed `alembic.ini`, which must stay
  credential-free — and sets `target_metadata = Base.metadata` *after* `import models`. That import
  looks unused and is not: without it autogenerate sees empty metadata and emits `drop_table` for
  both tables. After pulling new migrations run `.\venv\Scripts\alembic.exe upgrade head` by hand;
  migrations are deliberately not run at startup, because every `--reload` restart would take DDL
  locks and concurrent workers would race the same revision
- **Always read a generated revision before applying it.** Autogenerate does **not** detect
  `CheckConstraint` changes at all (so `ck_expenses_category_valid` must be migrated by hand with
  `op.drop_constraint` + `op.create_check_constraint`), renders renames as drop + create (data loss
  unless hand-edited to `op.alter_column(new_column_name=...)`), and produces false-positive
  `alter_column` noise on `Numeric` and `now()` from the `compare_type` / `compare_server_default`
  flags
- **`init_db()` / `create_all()` is retired** from the startup path — it still exists in
  `database/db.py` for building a scratch DB, but never run it against the real database:
  `create_all()` adds missing *tables* only and will silently diverge from the migration history.
  That divergence was a real bug: `ix_expenses_user_id_date` sat declared-but-nonexistent until
  Alembic was adopted
- **The 7 expense categories have one canonical source:** `models/expense.py:VALID_CATEGORIES`. The
  `CheckConstraint` SQL (via `_CATEGORY_SQL_LIST`) and `schemas/expense.py:CATEGORY_TYPE` (via
  `Literal[VALID_CATEGORIES]`) are both derived from it, so they cannot drift. Still hand-duplicated
  in three places that must be kept in sync by hand: `database/db.py` (seed data),
  `templates/profile.html` and `templates/preferences.html`. Reference list:
  `.claude/specs/01-database-setup.md` §9
- **`main.py`'s exception handler returns HTML/plain text** — any JSON route must be special-cased
  by path prefix, or its errors reach the client unparseable
- **Never use `with TestClient(app)`** — the context manager fires the lifespan, which runs
  `seed_db()` against the real PostgreSQL database (`init_db()` is no longer called, but the rule
  stands). Use `TestClient(app)` plainly
- **`url_for` shim in `main.py`** — templates use Flask-style `url_for('name')` calls; the shim in `main.py` translates these to Starlette's `app.url_path_for()`. Never remove it, and always name new routes with `name=` in the router decorator
- The app runs on **port 5001**, not the FastAPI default 8000 — don't change this
- The shared `Jinja2Templates` instance lives in `dependencies.py` — always import it from there, never create a second instance

---

## Changelog

### 2026-10-21 — feature/filter-transactions
Add expense filtering: /api/expenses endpoint, Alembic migrations, and errors package
- Added `routers/api_expenses.py` — authed JSON `GET /api/expenses` returning `ExpenseListResponse`
- Added `crud/expenses.py` — `list_expenses()` builds filtered/paginated query with a hardcoded sort allowlist
- Added `schemas/expense.py` filter/response schemas; `CATEGORY_TYPE` now derives from `models.expense.VALID_CATEGORIES` (single source of truth, via new `_CATEGORY_SQL_LIST` for the CHECK constraint)
- Adopted Alembic: `alembic/` (baseline + composite-index revisions), `alembic.ini`; `init_db()`/`create_all()` retired from startup (lifespan now runs `seed_db()` only)
- Added `errors/` package (`register_exception_handlers`, custom exceptions, JSON-aware handlers); moved handlers out of `main.py`
- Added `tests/` (`conftest.py`, `test_expense_filters.py`) and `pytest.ini`
- `requirements.txt`: pinned `starlette`, added `alembic`

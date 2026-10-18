# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Waffle Wallet is a lightweight personal expense tracker built with FastAPI and SQLite.

---

## Architecture
```
expense-tracker/
├── main.py             # App factory — mounts static, registers routers, url_for shim, 404 handler
├── dependencies.py     # Shared Jinja2Templates singleton imported by all routers
├── database.py         # SQLite helpers: get_db(), init_db(), seed_db()  ← student Step 1
├── core/
│   └── config.py       # Settings class backed by env vars, accessed via get_settings()
├── routers/
│   ├── pages.py        # GET routes that render Jinja2 templates
│   └── expenses.py     # Expense CRUD routes (stubs; students implement Steps 7–9)
├── models/             # SQLAlchemy-style model classes — empty until needed
├── schemas/            # Pydantic request/response schemas — empty until needed
├── services/           # Business logic — empty until needed
├── crud/               # DB query functions — empty until needed
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
- DB logic → `database.py` only, never inline in route functions
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags
- Business logic → `services/`, not inside routers
- DB queries → `crud/`, not inside routers or services

---

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — call a service/crud, return a response
- DB queries: always use parameterized queries (`?` placeholders) — never f-strings in SQL
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

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /terms` | Implemented — renders `terms.html` |
| `GET /privacy` | Implemented — renders `privacy.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/{id}/edit` | Stub — Step 8 |
| `GET /expenses/{id}/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use plain string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database.py` or `crud/`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database.py` is currently a documented stub** — do not assume `get_db()`, `init_db()`, or `seed_db()` exist until Step 1 implements them
- **`url_for` shim in `main.py`** — templates use Flask-style `url_for('name')` calls; the shim in `main.py` translates these to Starlette's `app.url_path_for()`. Never remove it, and always name new routes with `name=` in the router decorator
- The app runs on **port 5001**, not the FastAPI default 8000 — don't change this
- The shared `Jinja2Templates` instance lives in `dependencies.py` — always import it from there, never create a second instance
